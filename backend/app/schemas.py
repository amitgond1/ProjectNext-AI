from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Difficulty, InteractionStatus


CareerGoal = Literal["SDE", "AI_ML", "DATA_SCIENCE", "DATA_ENGINEERING", "DEVOPS", "CYBERSECURITY", "PRODUCT"]


class ProfileInput(BaseModel):
    user_id: str | None = None
    name: str | None = Field(default=None, max_length=100)
    skills: list[str] = Field(min_length=1, max_length=30)
    interests: list[str] = Field(min_length=1, max_length=20)
    career_goal: CareerGoal
    target_companies: list[str] = Field(default_factory=list, max_length=20)
    project_vision: str = Field(default="", max_length=500)
    experience_summary: str = Field(default="", max_length=1000)
    desired_outcome: Literal["JOB", "LEARNING", "SAAS", "RESEARCH", "HACKATHON"] = "JOB"
    weekly_hours: int = Field(default=10, ge=2, le=60)
    preferred_domains: list[str] = Field(default_factory=list, max_length=10)
    excluded_technologies: list[str] = Field(default_factory=list, max_length=20)
    must_have_technologies: list[str] = Field(default_factory=list, max_length=10)
    liked_project_ids: list[int] = Field(default_factory=list, max_length=50)
    disliked_project_ids: list[int] = Field(default_factory=list, max_length=50)
    difficulty: Difficulty = Difficulty.intermediate
    time_available_weeks: int = Field(ge=1, le=52)
    completed_project_ids: list[int] = Field(default_factory=list, max_length=100)

    @field_validator("skills", "interests", "target_companies", "preferred_domains", "excluded_technologies", "must_have_technologies")
    @classmethod
    def normalize_list(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    tech_stack: list[str]
    domain: str
    difficulty: Difficulty
    estimated_weeks: int
    resume_value_score: float
    target_roles: list[str]
    target_companies: list[str]
    learning_outcomes: list[str]


class RecommendationOut(ProjectOut):
    recommendation_score: float
    content_score: float
    collaborative_score: float
    resume_impact_score: float
    reason: str
    matched_skills: list[str]
    skills_to_learn: list[str]
    role_fit: bool
    time_fit: bool
    domain_fit: bool
    confidence: Literal["high", "medium", "exploratory"]


class RecommendationResponse(BaseModel):
    user_id: str
    algorithm_version: str
    cold_start: bool
    engine: str
    profile_interpreted_as: str
    preference_signals_used: int
    recommendations: list[RecommendationOut]


class FeedbackInput(BaseModel):
    user_id: str
    project_id: int
    status: InteractionStatus
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=2000)

    @field_validator("rating")
    @classmethod
    def completed_needs_rating(cls, rating: int | None, info):
        status = info.data.get("status")
        if status == InteractionStatus.completed and rating is None:
            raise ValueError("rating is required when a project is completed")
        return rating


class FeedbackOut(BaseModel):
    message: str
    interaction_id: int


class PaginatedProjects(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProjectOut]


class HealthOut(BaseModel):
    status: str
    project_count: int
    embedding_backend: str


class MilestoneOut(BaseModel):
    id: str
    week_label: str
    title: str
    tasks: list[str]
    deliverable: str


class ProjectBlueprintOut(BaseModel):
    project_id: int
    title: str
    problem_statement: str
    unique_angle: str
    skill_gap: list[str]
    architecture: list[str]
    mvp_features: list[str]
    stretch_features: list[str]
    success_metrics: list[str]
    milestones: list[MilestoneOut]
    resume_bullets: list[str]
    interview_questions: list[str]
    readme_markdown: str
