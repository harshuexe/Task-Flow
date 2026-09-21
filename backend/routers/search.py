from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from models import Project, Task, User, get_session
from security import get_current_user

router = APIRouter()


@router.get("/search", tags=["Search"])
def search(
    q: str = Query(min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    query = f"%{q.strip()}%"
    projects = session.exec(
        select(Project).where(Project.user_id == current_user.id, Project.title.ilike(query))
    ).all()
    owned_project_ids = session.exec(
        select(Project.id).where(Project.user_id == current_user.id)
    ).all()
    tasks = session.exec(
        select(Task).where(Task.project_id.in_(owned_project_ids), Task.title.ilike(query))
    ).all() if owned_project_ids else []
    return {
        "query": q,
        "results": {
            "projects": [{"id": project.id, "title": project.title} for project in projects],
            "tasks": [{"id": task.id, "title": task.title, "status": task.status} for task in tasks],
        },
    }