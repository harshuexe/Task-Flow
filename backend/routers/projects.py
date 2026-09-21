from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from models import (
    FileRecord,
    Project,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    Task,
    TeamMember,
    TeamMemberCreate,
    TeamMemberRead,
    TeamMemberUpdate,
    User,
    get_session,
)
from security import get_current_user
from routers.common import get_owned_project, get_owned_team_member, log_activity

router = APIRouter()
@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Project:
    project = Project(**project_in.model_dump(), user_id=current_user.id)
    session.add(project)
    session.commit()
    session.refresh(project)

    log_activity(session, current_user.id, "project_created", f"Created project '{project.title}'.")
    return project


@router.get("/projects", response_model=List[ProjectRead], tags=["Projects"])
def list_projects(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[Project]:
    return session.exec(select(Project).where(Project.user_id == current_user.id)).all()


@router.get("/projects/{project_id}", response_model=ProjectRead, tags=["Projects"])
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Project:
    return get_owned_project(project_id, current_user, session)


@router.put("/projects/{project_id}", response_model=ProjectRead, tags=["Projects"])
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Project:
    project = get_owned_project(project_id, current_user, session)

    for field, value in project_update.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    session.add(project)
    session.commit()
    session.refresh(project)

    log_activity(session, current_user.id, "project_updated", f"Updated project '{project.title}'.")
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    project = get_owned_project(project_id, current_user, session)
    title = project.title

    for task in session.exec(select(Task).where(Task.project_id == project_id)).all():
        session.delete(task)
    for file_record in session.exec(select(FileRecord).where(FileRecord.project_id == project_id)).all():
        session.delete(file_record)

    session.delete(project)
    session.commit()

    log_activity(session, current_user.id, "project_deleted", f"Deleted project '{title}'.")


@router.post("/team", response_model=TeamMemberRead, status_code=status.HTTP_201_CREATED, tags=["Team"])
def add_team_member(
    member_in: TeamMemberCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TeamMember:
    member = TeamMember(**member_in.model_dump(), user_id=current_user.id)
    session.add(member)
    session.commit()
    session.refresh(member)

    log_activity(session, current_user.id, "team_member_added", f"Added team member '{member.name}'.")
    return member


@router.get("/team", response_model=List[TeamMemberRead], tags=["Team"])
def list_team_members(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[TeamMember]:
    return session.exec(select(TeamMember).where(TeamMember.user_id == current_user.id)).all()


@router.patch("/team/{member_id}", response_model=TeamMemberRead, tags=["Team"])
def update_team_member(
    member_id: int,
    member_update: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TeamMember:
    member = get_owned_team_member(member_id, current_user, session)

    for field, value in member_update.model_dump(exclude_unset=True).items():
        setattr(member, field, value)

    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/team/{member_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Team"])
def remove_team_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    member = get_owned_team_member(member_id, current_user, session)
    name = member.name
    session.delete(member)
    session.commit()

    log_activity(session, current_user.id, "team_member_removed", f"Removed team member '{name}'.")
