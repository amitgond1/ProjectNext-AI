from fastapi.testclient import TestClient

from app.main import app
from app.recommender import embedding_service


def test_recommendation_and_feedback_flow(monkeypatch):
    # Keep CI deterministic and offline; production still lazily loads Sentence-BERT.
    monkeypatch.setattr(embedding_service, "_attempted", True)
    monkeypatch.setattr(embedding_service, "_model", None)
    payload = {
        "skills": ["Python", "FastAPI", "React"],
        "interests": ["AI", "recommendation systems"],
        "career_goal": "AI_ML",
        "target_companies": ["Google"],
        "difficulty": "intermediate",
        "time_available_weeks": 8,
        "completed_project_ids": [],
    }
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["project_count"] >= 200

        response = client.post("/recommend?limit=3", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert len(result["recommendations"]) == 3
        assert result["engine"].startswith("Sentence-BERT")
        assert all(item["reason"].startswith("Recommended because") for item in result["recommendations"])
        assert all("confidence" in item and "matched_skills" in item for item in result["recommendations"])

        refined_payload = {
            **payload,
            "user_id": result["user_id"],
            "liked_project_ids": [result["recommendations"][0]["id"]],
            "desired_outcome": "JOB",
            "weekly_hours": 12,
        }
        refined = client.post("/recommend?limit=3", json=refined_payload)
        assert refined.status_code == 200
        assert refined.json()["preference_signals_used"] == 1

        blueprint = client.get(
            f'/projects/{result["recommendations"][0]["id"]}/blueprint',
            params={"user_id": result["user_id"]},
        )
        assert blueprint.status_code == 200
        plan = blueprint.json()
        assert len(plan["milestones"]) == 5
        assert len(plan["architecture"]) >= 4
        assert len(plan["resume_bullets"]) == 3
        assert "# " in plan["readme_markdown"]

        feedback = client.post("/feedback", json={
            "user_id": result["user_id"],
            "project_id": result["recommendations"][0]["id"],
            "status": "completed",
            "rating": 5,
        })
        assert feedback.status_code == 200
