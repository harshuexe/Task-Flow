"""
SQLModel schemas for Ai-Task Flow.

Defines the database tables described in ARCHITECTURE.md, the
SQLAlchemy engine/session plumbing, and the Create/Read/Update
variants used by the API layer (main.py, Phase 2 continued).
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Optional

from dotenv import load_dotenv
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{(BASE_DIR / 'database.db').as_posix()}"
elif DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL.removeprefix("sqlite:///")
    if not os.path.isabs(sqlite_path):
        DATABASE_URL = f"sqlite:///{(BASE_DIR / sqlite_path).resolve().as_posix()}"

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling; harmless for other database backends.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Create all tables. Call once at application startup (see main.py)."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        legacy_statuses = {"To Do": "todo", "Todo": "todo", "In Progress": "in_progress", "Done": "done"}
        changed = False
        for task in session.exec(select(Task)).all():
            normalized_status = legacy_statuses.get(task.status)
            if normalized_status:
                task.status = normalized_status
                session.add(task)
                changed = True
        if changed:
            session.commit()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session


# --------------------------------------------------------------------------
# User
# --------------------------------------------------------------------------
class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, nullable=False, max_length=50)
    email: str = Field(index=True, unique=True, nullable=False, max_length=255)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)

    projects: List["Project"] = Relationship(back_populates="owner")
    team_memberships: List["TeamMember"] = Relationship(back_populates="user")
    activity_logs: List["ActivityLog"] = Relationship(back_populates="user")
    files: List["FileRecord"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


# --------------------------------------------------------------------------
# Project
# --------------------------------------------------------------------------
class ProjectBase(SQLModel):
    title: str = Field(nullable=False, max_length=200)
    description: Optional[str] = Field(default=None)


class Project(ProjectBase, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    owner: Optional[User] = Relationship(back_populates="projects")
    tasks: List["Task"] = Relationship(back_populates="project")
    files: List["FileRecord"] = Relationship(back_populates="project")


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    user_id: int


class ProjectUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None


# --------------------------------------------------------------------------
# Task
# --------------------------------------------------------------------------
class TaskStatus:
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority:
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


VALID_TASK_STATUSES = {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE}
VALID_TASK_PRIORITIES = {TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW}


class TaskBase(SQLModel):
    title: str = Field(nullable=False, max_length=200)
    description: Optional[str] = Field(default=None)
    status: str = Field(default=TaskStatus.TODO, max_length=20)
    priority: str = Field(default=TaskPriority.MEDIUM, max_length=10)
    due_date: Optional[str] = Field(default=None)


class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", nullable=False)

    project: Optional[Project] = Relationship(back_populates="tasks")


class TaskCreate(TaskBase):
    project_id: int


class TaskRead(TaskBase):
    id: int
    project_id: int


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


# --------------------------------------------------------------------------
# TeamMember
# --------------------------------------------------------------------------
class TeamMemberBase(SQLModel):
    name: str = Field(nullable=False, max_length=100)
    email: str = Field(nullable=False, max_length=255)
    role: str = Field(default="Member", max_length=50)
    color: str = Field(default="#6366F1", max_length=20)
    presence: str = Field(default="offline", max_length=10)


class TeamMember(TeamMemberBase, table=True):
    __tablename__ = "team_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: Optional[User] = Relationship(back_populates="team_memberships")


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberRead(TeamMemberBase):
    id: int
    user_id: int


class TeamMemberUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    color: Optional[str] = None
    presence: Optional[str] = None


# --------------------------------------------------------------------------
# ActivityLog
# --------------------------------------------------------------------------
class ActivityLogBase(SQLModel):
    action: str = Field(nullable=False, max_length=100)
    details: Optional[str] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ActivityLog(ActivityLogBase, table=True):
    __tablename__ = "activity_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: Optional[User] = Relationship(back_populates="activity_logs")


class ActivityLogCreate(SQLModel):
    action: str
    details: Optional[str] = None


class ActivityLogRead(ActivityLogBase):
    id: int
    user_id: int


# --------------------------------------------------------------------------
# FileRecord
# --------------------------------------------------------------------------
class FileRecordBase(SQLModel):
    filename: str = Field(nullable=False, max_length=255)
    file_size: str = Field(nullable=False, max_length=50)
    file_type: str = Field(nullable=False, max_length=100)
    file_url: str = Field(nullable=False, max_length=500)
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id")
    upload_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FileRecord(FileRecordBase, table=True):
    __tablename__ = "file_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: Optional[User] = Relationship(back_populates="files")
    project: Optional[Project] = Relationship(back_populates="files")


class FileRecordCreate(SQLModel):
    filename: str
    file_size: str
    file_type: str
    file_url: str
    project_id: Optional[int] = None


class FileRecordRead(FileRecordBase):
    id: int
    user_id: int
