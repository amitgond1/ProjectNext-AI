from app.models import Difficulty
from app.recommender import feasibility, resume_impact
from app.schemas import ProfileInput
from app.seed import build_catalog


def test_impact_and_feasibility_are_bounded():
    profile = ProfileInput(
        skills=["Python", "FastAPI"],
        interests=["AI", "recommendations"],
        career_goal="AI_ML",
        target_companies=["Google"],
        difficulty=Difficulty.intermediate,
        time_available_weeks=8,
    )
    for project in build_catalog():
        assert 0 <= resume_impact(profile, project) <= 1
        assert 0 <= feasibility(profile, project) <= 1
