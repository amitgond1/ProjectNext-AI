import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class Difficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class InteractionStatus(str, enum.Enum):
    saved = "saved"
    started = "started"
    completed = "completed"
    dismissed = "dismissed"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    career_goal: Mapped[str] = mapped_column(String(50), index=True)
    target_companies: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty))
    time_available_weeks: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    interactions: Mapped[list["UserProjectInteraction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    domain: Mapped[str] = mapped_column(String(60), index=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), index=True)
    estimated_weeks: Mapped[int] = mapped_column(Integer)
    resume_value_score: Mapped[float] = mapped_column(Float)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_companies: Mapped[list[str]] = mapped_column(JSON, default=list)
    learning_outcomes: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interactions: Mapped[list["UserProjectInteraction"]] = relationship(back_populates="project")

    @property
    def semantic_text(self) -> str:
        return " | ".join([
            self.title,
            self.description,
            f"domain {self.domain}",
            f"technologies {' '.join(self.tech_stack)}",
            f"roles {' '.join(self.target_roles)}",
            f"outcomes {' '.join(self.learning_outcomes)}",
        ])


class UserProjectInteraction(Base):
    __tablename__ = "user_project_interactions"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[InteractionStatus] = mapped_column(Enum(InteractionStatus), default=InteractionStatus.saved)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[UserProfile] = relationship(back_populates="interactions")
    project: Mapped[Project] = relationship(back_populates="interactions")

