from typing import List
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from models import ActivityLog, ActivityLogRead, Project, Task, TaskStatus, TaskPriority, TeamMember, User, get_session
from security import get_current_user
router = APIRouter()
@router.get("/activity", response_model=List[ActivityLogRead], tags=["Activity"])
def list_activity(
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[ActivityLog]:
    query = (
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
    )
    return session.exec(query).all()


@router.get("/dashboard/stats", tags=["Dashboard"])
def dashboard_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    owned_project_ids = session.exec(
        select(Project.id).where(Project.user_id == current_user.id)
    ).all()

    empty_status = {TaskStatus.TODO: 0, TaskStatus.IN_PROGRESS: 0, TaskStatus.DONE: 0}
    empty_priority = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 0, TaskPriority.LOW: 0}

    if not owned_project_ids:
        return {
            "total_projects": 0,
            "total_tasks": 0,
            "tasks_by_status": empty_status,
            "tasks_by_priority": empty_priority,
            "team_members": 0,
            "completion_rate": 0.0,
        }

    tasks = session.exec(select(Task).where(Task.project_id.in_(owned_project_ids))).all()

    tasks_by_status = dict(empty_status)
    tasks_by_priority = dict(empty_priority)
    for task in tasks:
        normalized_status = {
            "To Do": TaskStatus.TODO,
            "Todo": TaskStatus.TODO,
            "In Progress": TaskStatus.IN_PROGRESS,
            "Done": TaskStatus.DONE,
        }.get(task.status, task.status)
        if normalized_status in tasks_by_status:
            tasks_by_status[normalized_status] += 1
        if task.priority in tasks_by_priority:
            tasks_by_priority[task.priority] += 1

    total_tasks = len(tasks)
    completed = tasks_by_status[TaskStatus.DONE]
    completion_rate = round((completed / total_tasks) * 100, 1) if total_tasks else 0.0

    team_members = len(
        session.exec(select(TeamMember).where(TeamMember.user_id == current_user.id)).all()
    )

    return {
        "total_projects": len(owned_project_ids),
        "total_tasks": total_tasks,
        "tasks_by_status": tasks_by_status,
        "tasks_by_priority": tasks_by_priority,
        "team_members": team_members,
        "completion_rate": completion_rate,
    }

