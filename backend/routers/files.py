import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select
from models import FileRecord, FileRecordRead, Project, User, get_session
from security import get_current_user
from routers.common import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR, get_owned_project, log_activity
router = APIRouter()
@router.post("/files/upload", response_model=FileRecordRead, status_code=status.HTTP_201_CREATED, tags=["Files"])
async def upload_file(
    project_id: Optional[int] = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FileRecord:
    if project_id is not None:
        get_owned_project(project_id, current_user, session)

    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{extension}' is not allowed.",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the 20MB size limit.",
        )

    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination_path = UPLOAD_DIR / stored_name
    with open(destination_path, "wb") as out_file:
        out_file.write(contents)

    file_record = FileRecord(
        filename=file.filename or stored_name,
        file_size=str(len(contents)),
        file_type=file.content_type or "application/octet-stream",
        file_url=f"/static/uploads/{stored_name}",
        project_id=project_id,
        user_id=current_user.id,
    )
    session.add(file_record)
    session.commit()
    session.refresh(file_record)

    log_activity(session, current_user.id, "file_uploaded", f"Uploaded file '{file_record.filename}'.")
    return file_record


@router.get("/files", response_model=List[FileRecordRead], tags=["Files"])
def list_files(
    project_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[FileRecord]:
    query = select(FileRecord).where(FileRecord.user_id == current_user.id)
    if project_id is not None:
        get_owned_project(project_id, current_user, session)
        query = query.where(FileRecord.project_id == project_id)
    return session.exec(query).all()


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Files"])
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    file_record = session.get(FileRecord, file_id)
    if not file_record or file_record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    stored_path = UPLOAD_DIR / os.path.basename(file_record.file_url)
    if os.path.exists(stored_path):
        os.remove(stored_path)

    filename = file_record.filename
    session.delete(file_record)
    session.commit()

    log_activity(session, current_user.id, "file_deleted", f"Deleted file '{filename}'.")
