from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from models import (
    Project,
    Task,
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
    User,
    VALID_TASK_PRIORITIES,
    VALID_TASK_STATUSES,
    get_session,
)
from security import get_current_user
from routers.common import get_owned_project, get_owned_task, log_activity

router = APIRouter()


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    get_owned_project(task_in.project_id, current_user, session)

    if task_in.status not in VALID_TASK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value.")
    if task_in.priority not in VALID_TASK_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority value.")

    task = Task(**task_in.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)

    log_activity(session, current_user.id, "task_created", f"Created task '{task.title}'.")
    return task


@router.get("/tasks", response_model=List[TaskRead], tags=["Tasks"])
def list_tasks(
    project_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[Task]:
    if project_id is not None:
        get_owned_project(project_id, current_user, session)
        query = select(Task).where(Task.project_id == project_id)
    else:
        owned_project_ids = session.exec(
            select(Project.id).where(Project.user_id == current_user.id)
        ).all()
        if not owned_project_ids:
            return []
        query = select(Task).where(Task.project_id.in_(owned_project_ids))

    if status_filter:
        query = query.where(Task.status == status_filter)

    return session.exec(query).all()


@router.get("/tasks/{task_id}", response_model=TaskRead, tags=["Tasks"])
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    return get_owned_task(task_id, current_user, session)


@router.patch("/tasks/{task_id}", response_model=TaskRead, tags=["Tasks"])
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    task = get_owned_task(task_id, current_user, session)
    update_data = task_update.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] not in VALID_TASK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value.")
    if "priority" in update_data and update_data["priority"] not in VALID_TASK_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority value.")

    for field, value in update_data.items():
        setattr(task, field, value)

    session.add(task)
    session.commit()
    session.refresh(task)

    log_activity(
        session, current_user.id, "task_updated",
        f"Updated task '{task.title}' (status: {task.status}).",
    )
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    task = get_owned_task(task_id, current_user, session)
    title = task.title
    session.delete(task)
    session.commit()

    log_activity(session, current_user.id, "task_deleted", f"Deleted task '{title}'.")

