"""Shared dependencies and helpers for API routers."""
import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session
from models import ActivityLog, Project, Task, TeamMember, User

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
ALLOWED_UPLOAD_EXTENSIONS = {".py", ".js", ".ts", ".json", ".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024

def log_activity(session: Session, user_id: int, action: str, details: Optional[str] = None) -> None:
    entry = ActivityLog(user_id=user_id, action=action, details=details)
    session.add(entry)
    session.commit()

def get_owned_project(project_id: int, current_user: User, session: Session) -> Project:
    project = session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project

def get_owned_task(task_id: int, current_user: User, session: Session) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    project = session.get(Project, task.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task

def get_owned_team_member(member_id: int, current_user: User, session: Session) -> TeamMember:
    member = session.get(TeamMember, member_id)
    if not member or member.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found.")
    return member
