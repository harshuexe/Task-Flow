from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select

from backend.models import User, create_db_and_tables, engine
from backend.security import hash_password

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@tapi.com"
ADMIN_PASSWORD = "admin123"


def create_admin() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        existing_user = session.exec(
            select(User).where(
                (User.username == ADMIN_USERNAME) | (User.email == ADMIN_EMAIL)
            )
        ).first()

        if existing_user:
            print(
                f"Admin user already exists: "
                f"{existing_user.username} ({existing_user.email})"
            )
            return

        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
        )
        session.add(admin)
        session.commit()
        print(f"Created admin user: {ADMIN_USERNAME} ({ADMIN_EMAIL})")


if __name__ == "__main__":
    create_admin()
