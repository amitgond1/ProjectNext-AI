import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.recommender import embedding_service, recommend
from app.schemas import ProfileInput
from app.seed import seed_projects


def test_data_science_never_returns_data_engineering(monkeypatch):
    asyncio.run(_verify_data_science_relevance(monkeypatch))


async def _verify_data_science_relevance(monkeypatch):
    monkeypatch.setattr(embedding_service, "_attempted", True)
    monkeypatch.setattr(embedding_service, "_model", None)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_projects(session)
        profile = ProfileInput(
            skills=["Python", "Pandas", "Scikit-learn"], interests=["healthcare analytics"],
            career_goal="DATA_SCIENCE", project_vision="predict patient readmission risk",
            preferred_domains=["Data Science"], difficulty="intermediate", time_available_weeks=10,
        )
        results, _ = await recommend(session, profile, "new-user", 12)
        assert results
        assert all(item.project.domain == "Data Science" for item in results)
        assert "Healthcare" in results[0].project.title
    await engine.dispose()
