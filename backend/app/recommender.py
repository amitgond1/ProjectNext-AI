import logging
import threading
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from anyio import to_thread
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import InteractionStatus, Project, UserProfile, UserProjectInteraction
from .schemas import ProfileInput
from .seed import CURATED_PROJECTS

logger = logging.getLogger(__name__)
CURATED_TITLES = {item["title"] for item in CURATED_PROJECTS}

STATUS_WEIGHT = {
    InteractionStatus.dismissed: -1.0,
    InteractionStatus.saved: 1.0,
    InteractionStatus.started: 2.0,
    InteractionStatus.completed: 3.0,
}


@dataclass
class ScoredProject:
    project: Project
    score: float
    content: float
    collaborative: float
    impact: float
    reason: str


class EmbeddingService:
    """Lazy Sentence-BERT encoder with an offline-safe semantic hashing fallback."""

    def __init__(self) -> None:
        self._model = None
        self._attempted = False
        self._lock = threading.Lock()
        self._fallback = HashingVectorizer(n_features=768, alternate_sign=False, norm="l2", ngram_range=(1, 2))

    @property
    def backend(self) -> str:
        return settings.model_name if self._model is not None else "hashing-fallback (Sentence-BERT loads lazily)"

    def _load(self):
        if self._attempted:
            return self._model
        with self._lock:
            if self._attempted:
                return self._model
            self._attempted = True
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(settings.model_name)
                logger.info("Loaded embedding model %s", settings.model_name)
            except Exception as exc:  # API remains available during model registry/network incidents.
                logger.warning("Sentence-BERT unavailable; using hashing fallback: %s", exc)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        if model is not None:
            return np.asarray(model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)
        return self._fallback.transform(texts).toarray().astype(np.float32)


embedding_service = EmbeddingService()


def profile_text(profile: ProfileInput) -> str:
    return " | ".join([
        f"skills {' '.join(profile.skills)}",
        f"interests {' '.join(profile.interests)}",
        f"career role {profile.career_goal}",
        f"target companies {' '.join(profile.target_companies)}",
        f"project vision {profile.project_vision}",
        f"past project experience {profile.experience_summary}",
        f"desired outcome {profile.desired_outcome}",
        f"weekly effort {profile.weekly_hours} hours",
        f"preferred domains {' '.join(profile.preferred_domains)}",
        f"must use technologies {' '.join(profile.must_have_technologies)}",
        f"difficulty {profile.difficulty.value}",
    ])


def resume_impact(profile: ProfileInput, project: Project) -> float:
    effective_role = {"DATA_SCIENCE": "DATA", "DATA_ENGINEERING": "DATA"}.get(profile.career_goal, profile.career_goal)
    role_match = 1.0 if effective_role in project.target_roles else 0.35
    wanted = {company.casefold() for company in profile.target_companies}
    offered = {company.casefold() for company in project.target_companies}
    company_match = len(wanted & offered) / max(1, len(wanted)) if wanted else 0.5
    profile_skills = {skill.casefold() for skill in profile.skills}
    project_skills = {skill.casefold() for skill in project.tech_stack}
    skill_bridge = min(1.0, len(profile_skills & project_skills) / max(1, min(3, len(project_skills))) + 0.25)
    base = project.resume_value_score / 10.0
    return float(np.clip(0.45 * base + 0.3 * role_match + 0.15 * skill_bridge + 0.1 * company_match, 0, 1))


def feasibility(profile: ProfileInput, project: Project) -> float:
    required_hours = project.estimated_weeks * {"beginner": 7, "intermediate": 10, "advanced": 14}[project.difficulty.value]
    available_hours = profile.time_available_weeks * profile.weekly_hours
    time_score = 1.0 if available_hours >= required_hours else max(0.1, available_hours / required_hours)
    levels = {"beginner": 0, "intermediate": 1, "advanced": 2}
    gap = abs(levels[profile.difficulty.value] - levels[project.difficulty.value])
    return 0.7 * time_score + 0.3 * (1.0 - 0.35 * gap)


def build_reason(profile: ProfileInput, project: Project, content: float, collab: float) -> str:
    shared = [skill for skill in project.tech_stack if skill.casefold() in {s.casefold() for s in profile.skills}]
    parts: list[str] = []
    if shared:
        parts.append(f"you already know {', '.join(shared[:3])}")
    effective_role = {"DATA_SCIENCE": "DATA", "DATA_ENGINEERING": "DATA"}.get(profile.career_goal, profile.career_goal)
    if effective_role in project.target_roles:
        parts.append(f"it aligns with your {profile.career_goal.replace('_', ' ').title()} goal")
    required_hours = project.estimated_weeks * {"beginner": 7, "intermediate": 10, "advanced": 14}[project.difficulty.value]
    if profile.time_available_weeks * profile.weekly_hours >= required_hours:
        parts.append(f"it fits your {profile.weekly_hours} hours/week schedule")
    if collab > 0.25:
        parts.append("similar learners rated related work highly")
    if not parts and content > 0.2:
        parts.append(f"your interests match its {project.domain} focus")
    return "Recommended because " + ", and ".join(parts[:3]) + "."


async def collaborative_scores(session: AsyncSession, target_user_id: str, projects: list[Project]) -> tuple[dict[int, float], bool]:
    result = await session.execute(select(UserProjectInteraction))
    interactions = list(result.scalars())
    user_ids = sorted({item.user_id for item in interactions} | {target_user_id})
    project_ids = [project.id for project in projects]
    user_index = {value: index for index, value in enumerate(user_ids)}
    project_index = {value: index for index, value in enumerate(project_ids)}
    matrix = np.zeros((len(user_ids), len(project_ids)), dtype=np.float32)
    ratings_by_project: dict[int, list[float]] = defaultdict(list)
    target_has_history = False
    for item in interactions:
        if item.project_id not in project_index:
            continue
        value = STATUS_WEIGHT[item.status] * ((item.rating or 3) / 3.0)
        matrix[user_index[item.user_id], project_index[item.project_id]] = value
        if value > 0:
            ratings_by_project[item.project_id].append(value)
        target_has_history |= item.user_id == target_user_id

    if target_has_history and len(user_ids) > 1:
        target_row = user_index[target_user_id]
        similarities = cosine_similarity(matrix[target_row:target_row + 1], matrix)[0]
        similarities[target_row] = 0
        positive = np.clip(similarities, 0, None)
        denominator = positive.sum()
        predictions = positive @ matrix / denominator if denominator > 0 else np.zeros(len(project_ids))
        minimum, maximum = predictions.min(), predictions.max()
        if maximum > minimum:
            predictions = (predictions - minimum) / (maximum - minimum)
        return {pid: float(predictions[index]) for pid, index in project_index.items()}, False

    # Bayesian-smoothed popularity is safer than zero when a user has no interactions.
    scores = {pid: (sum(values) + 2.0) / (len(values) + 2.0) for pid, values in ratings_by_project.items()}
    ceiling = max(scores.values(), default=1.0)
    return {project.id: scores.get(project.id, 0.25) / ceiling for project in projects}, True


async def recommend(session: AsyncSession, profile: ProfileInput, user_id: str, limit: int) -> tuple[list[ScoredProject], bool]:
    all_projects = list((await session.execute(select(Project))).scalars())
    # Role eligibility is a hard retrieval constraint. Behavioral popularity
    # must never push an unrelated AI/SDE project into a Data user's results.
    legacy_role = {"DATA_SCIENCE": "DATA", "DATA_ENGINEERING": "DATA"}.get(profile.career_goal, profile.career_goal)
    projects = [project for project in all_projects if legacy_role in project.target_roles]
    if profile.career_goal == "DATA_SCIENCE":
        projects = [project for project in projects if project.domain != "Data Engineering"]
    elif profile.career_goal == "DATA_ENGINEERING":
        projects = [project for project in projects if project.domain in {"Data Engineering", "Cloud & DevOps"} or any(term in project.description.casefold() for term in ("pipeline", "lakehouse", "warehouse", "stream"))]
    excluded = {item.casefold() for item in profile.excluded_technologies}
    if excluded:
        projects = [project for project in projects if not excluded.intersection(item.casefold() for item in project.tech_stack)]
    preferred = {item.casefold() for item in profile.preferred_domains}
    if preferred:
        domain_matches = [project for project in projects if project.domain.casefold() in preferred]
        if domain_matches:
            projects = domain_matches
    must_have = {item.casefold() for item in profile.must_have_technologies}
    if must_have:
        technology_matches = [project for project in projects if must_have.issubset({item.casefold() for item in project.tech_stack})]
        if technology_matches:
            projects = technology_matches
    curated_role_projects = [project for project in projects if project.title in CURATED_TITLES]
    # Data recommendations have a complete curated set; do not dilute it with
    # mechanically generated catalog variants.
    if profile.career_goal == "DATA_SCIENCE" and curated_role_projects:
        projects = curated_role_projects
    if not projects:
        return [], True
    # Transformer inference is CPU-bound; keep the async API event loop responsive.
    project_by_id = {project.id: project for project in all_projects}
    liked_projects = [project_by_id[project_id] for project_id in profile.liked_project_ids if project_id in project_by_id]
    disliked_projects = [project_by_id[project_id] for project_id in profile.disliked_project_ids if project_id in project_by_id]
    texts = [profile_text(profile)] + [project.semantic_text for project in projects] + [project.semantic_text for project in liked_projects + disliked_projects]
    vectors = await to_thread.run_sync(embedding_service.encode, texts)
    query_vector = vectors[0].copy()
    preference_start = 1 + len(projects)
    if liked_projects:
        liked_vectors = vectors[preference_start:preference_start + len(liked_projects)]
        query_vector = query_vector + 0.4 * liked_vectors.mean(axis=0)
    if disliked_projects:
        disliked_start = preference_start + len(liked_projects)
        disliked_vectors = vectors[disliked_start:disliked_start + len(disliked_projects)]
        query_vector = query_vector - 0.3 * disliked_vectors.mean(axis=0)
    norm = np.linalg.norm(query_vector)
    if norm > 0:
        query_vector = query_vector / norm
    content_scores = cosine_similarity(query_vector.reshape(1, -1), vectors[1:1 + len(projects)])[0]
    collaborative, cold_start = await collaborative_scores(session, user_id, projects)
    excluded = set(profile.completed_project_ids) | set(profile.disliked_project_ids)
    existing = await session.execute(
        select(UserProjectInteraction.project_id).where(
            UserProjectInteraction.user_id == user_id,
            UserProjectInteraction.status.in_([InteractionStatus.completed, InteractionStatus.dismissed]),
        )
    )
    excluded.update(existing.scalars())
    scored: list[ScoredProject] = []
    for index, project in enumerate(projects):
        if project.id in excluded:
            continue
        content = float(np.clip(content_scores[index], 0, 1))
        collab = float(np.clip(collaborative.get(project.id, 0), 0, 1))
        impact = resume_impact(profile, project)
        fit = feasibility(profile, project)
        # Concrete curated ideas receive a modest quality prior; relevance is
        # still determined primarily by the user's semantic profile.
        is_flagship = project.title in CURATED_TITLES
        quality = 1.0 if is_flagship else project.resume_value_score / 10.0
        if cold_start:
            score = 0.53 * content + 0.04 * collab + 0.25 * impact + 0.1 * fit + 0.08 * quality
        else:
            score = 0.47 * content + 0.14 * collab + 0.21 * impact + 0.1 * fit + 0.08 * quality
        if is_flagship:
            score += 0.06
        scored.append(ScoredProject(
            project=project,
            score=round(score * 100, 2),
            content=round(content * 100, 2),
            collaborative=round(collab * 100, 2),
            impact=round(impact * 100, 2),
            reason=build_reason(profile, project, content, collab),
        ))
    ranked = sorted(scored, key=lambda item: item.score, reverse=True)
    if ranked and all(item.project.title in CURATED_TITLES for item in ranked):
        return ranked[:limit], cold_start
    # Avoid a monotonous page containing twelve variants from one domain.
    diversified: list[ScoredProject] = []
    domain_counts: dict[str, int] = defaultdict(int)
    for item in ranked:
        if domain_counts[item.project.domain] >= 3:
            continue
        diversified.append(item)
        domain_counts[item.project.domain] += 1
        if len(diversified) == limit:
            break
    if len(diversified) < limit:
        used = {item.project.id for item in diversified}
        diversified.extend(item for item in ranked if item.project.id not in used and len(diversified) < limit)
    return diversified, cold_start
