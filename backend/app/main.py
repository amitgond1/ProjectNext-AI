import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models  # noqa: F401 - registers ORM metadata
from .config import settings
from .blueprint import build_blueprint
from .database import SessionLocal, create_tables, get_session
from .models import Difficulty, Project, UserProfile, UserProjectInteraction
from .recommender import embedding_service, recommend
from .schemas import (
    FeedbackInput,
    FeedbackOut,
    HealthOut,
    PaginatedProjects,
    ProfileInput,
    ProjectOut,
    ProjectBlueprintOut,
    RecommendationOut,
    RecommendationResponse,
)
from .seed import seed_projects

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_tables()
    async with SessionLocal() as session:
        count = await seed_projects(session)
        logger.info("Project catalog ready with %s projects", count)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Explainable hybrid project recommendations for students and freshers.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthOut, tags=["system"])
async def health(session: AsyncSession = Depends(get_session)) -> HealthOut:
    count = await session.scalar(select(func.count(Project.id))) or 0
    return HealthOut(status="ok", project_count=count, embedding_backend=embedding_service.backend)


@app.get("/projects", response_model=PaginatedProjects, tags=["projects"])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: str | None = None,
    difficulty: Difficulty | None = None,
    search: str | None = Query(default=None, min_length=2, max_length=100),
    session: AsyncSession = Depends(get_session),
) -> PaginatedProjects:
    filters = []
    if domain:
        filters.append(func.lower(Project.domain) == domain.lower())
    if difficulty:
        filters.append(Project.difficulty == difficulty)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(Project.title.ilike(pattern) | Project.description.ilike(pattern))
    query = select(Project).where(*filters)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list((await session.execute(
        query.order_by(Project.resume_value_score.desc(), Project.id).offset((page - 1) * page_size).limit(page_size)
    )).scalars())
    return PaginatedProjects(total=total, page=page, page_size=page_size, items=items)


@app.get("/projects/{project_id}/blueprint", response_model=ProjectBlueprintOut, tags=["projects"])
async def project_blueprint(
    project_id: int,
    user_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> ProjectBlueprintOut:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    user = await session.get(UserProfile, user_id) if user_id else None
    if user_id and user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return ProjectBlueprintOut(**build_blueprint(project, user))


async def upsert_profile(session: AsyncSession, data: ProfileInput) -> UserProfile:
    user = await session.get(UserProfile, data.user_id) if data.user_id else None
    if data.user_id and user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    if user is None:
        user = UserProfile()
        session.add(user)
    user.name = data.name
    user.skills = data.skills
    user.interests = data.interests
    user.career_goal = data.career_goal
    user.target_companies = data.target_companies
    user.preferred_difficulty = data.difficulty
    user.time_available_weeks = data.time_available_weeks
    await session.flush()
    return user


@app.post("/recommend", response_model=RecommendationResponse, tags=["recommendations"])
async def get_recommendations(
    profile: ProfileInput,
    limit: int = Query(10, ge=1, le=settings.max_recommendations),
    session: AsyncSession = Depends(get_session),
) -> RecommendationResponse:
    try:
        user = await upsert_profile(session, profile)
        results, cold_start = await recommend(session, profile, user.id, limit)
        await session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        logger.exception("Recommendation request failed")
        raise HTTPException(status_code=500, detail="Could not generate recommendations") from exc
    recommendations = [
        RecommendationOut(
            **ProjectOut.model_validate(item.project).model_dump(),
            recommendation_score=item.score,
            content_score=item.content,
            collaborative_score=item.collaborative,
            resume_impact_score=item.impact,
            reason=item.reason,
            matched_skills=[skill for skill in item.project.tech_stack if skill.casefold() in {value.casefold() for value in profile.skills}],
            skills_to_learn=[skill for skill in item.project.tech_stack if skill.casefold() not in {value.casefold() for value in profile.skills}][:4],
            role_fit=True,
            time_fit=profile.time_available_weeks * profile.weekly_hours >= item.project.estimated_weeks * {"beginner": 7, "intermediate": 10, "advanced": 14}[item.project.difficulty.value],
            domain_fit=not profile.preferred_domains or item.project.domain.casefold() in {value.casefold() for value in profile.preferred_domains},
            confidence="high" if item.content >= 55 else "medium" if item.content >= 30 else "exploratory",
        )
        for item in results
    ]
    return RecommendationResponse(
        user_id=user.id,
        algorithm_version="hybrid-v2.0-role-strict",
        cold_start=cold_start,
        engine=f"Sentence-BERT ({settings.model_name}) + behavioral ranking",
        profile_interpreted_as=f"{profile.career_goal.replace('_', ' ').title()}: {profile.project_vision or ', '.join(profile.interests)}",
        preference_signals_used=len(profile.liked_project_ids) + len(profile.disliked_project_ids),
        recommendations=recommendations,
    )


@app.post("/feedback", response_model=FeedbackOut, tags=["feedback"])
async def submit_feedback(payload: FeedbackInput, session: AsyncSession = Depends(get_session)) -> FeedbackOut:
    user = await session.get(UserProfile, payload.user_id)
    project = await session.get(Project, payload.project_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    interaction = await session.scalar(select(UserProjectInteraction).where(
        UserProjectInteraction.user_id == payload.user_id,
        UserProjectInteraction.project_id == payload.project_id,
    ))
    if interaction is None:
        interaction = UserProjectInteraction(user_id=payload.user_id, project_id=payload.project_id)
        session.add(interaction)
    interaction.status = payload.status
    interaction.rating = payload.rating
    interaction.feedback_text = payload.feedback_text
    await session.commit()
    await session.refresh(interaction)
    return FeedbackOut(message="Feedback recorded; it will influence future rankings.", interaction_id=interaction.id)
