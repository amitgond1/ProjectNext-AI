from app.models import Difficulty
from app.seed import build_catalog


def test_catalog_has_200_unique_projects():
    projects = build_catalog()
    assert len(projects) >= 200
    assert len({project.slug for project in projects}) == len(projects)
    assert {project.difficulty for project in projects} == set(Difficulty)
    assert all(1 <= project.resume_value_score <= 10 for project in projects)

