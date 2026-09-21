from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from models import User, UserRead, UserUpdate, get_session
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, hash_password, verify_password
from routers.common import log_activity
router = APIRouter()
@router.post("/auth/login", tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> dict:
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    log_activity(session, user.id, "user_login", f"User '{user.username}' logged in.")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserRead, tags=["Auth"])
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/auth/me", response_model=UserRead, tags=["Auth"])
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> User:
    update_data = user_update.model_dump(exclude_unset=True)

    new_password = update_data.pop("password", None)
    if new_password:
        current_user.hashed_password = hash_password(new_password)

    if "username" in update_data and update_data["username"] != current_user.username:
        clash = session.exec(select(User).where(User.username == update_data["username"])).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")

    if "email" in update_data and update_data["email"] != current_user.email:
        clash = session.exec(select(User).where(User.email == update_data["email"])).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    log_activity(session, current_user.id, "profile_updated", "User updated their profile.")
    return current_user
