"""
Security utilities for Ai-Task Flow.

Handles password hashing/verification and JWT access-token
creation/validation, plus the FastAPI dependency used to resolve
the current authenticated user on protected routes.
"""

import os
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from models import User, get_session

load_dotenv(Path(__file__).resolve().parent / ".env")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# This value is intentionally available only when explicitly set in
# backend/.env together with ENVIRONMENT=development; it is never a fallback.
DEVELOPMENT_SECRET_KEY = "insecure-dev-key-change-me"
ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "")).strip().lower()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing from backend/.env. Set a random key of at least "
        "32 characters before starting the API."
    )
if len(SECRET_KEY) < 32:
    if ENVIRONMENT == "development" and SECRET_KEY == DEVELOPMENT_SECRET_KEY:
        warnings.warn(
            "Using the documented insecure development SECRET_KEY. "
            "Never use it outside ENVIRONMENT=development.",
            RuntimeWarning,
        )
    else:
        raise RuntimeError(
            "SECRET_KEY is too weak. Use a random value of at least 32 characters "
            "(the documented development value is permitted only with "
            "ENVIRONMENT=development)."
        )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl points at the login route that will be defined on the auth
# router in main.py (Phase 2 continued) — update this string if that
# route's path ends up different.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --------------------------------------------------------------------------
# JWT token handling
# --------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    `data` should include at least {"sub": <username>}.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises jose.JWTError on failure —
    callers should catch this (see get_current_user below).
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# --------------------------------------------------------------------------
# FastAPI dependencies
# --------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the currently authenticated user from the bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Hook for future account-status checks (e.g. disabled/banned users)."""
    return current_user
