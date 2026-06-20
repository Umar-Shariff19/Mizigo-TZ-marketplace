from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_admin_user
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(tags=["Users"])


@router.post(
    "/users",
    response_model=UserResponse,
    summary="Create user",
    description="Registers a new marketplace user with a hashed password.",
)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Depends(require_admin_user)],
    summary="List users",
    description="Returns all registered users. Requires an authenticated ADMIN user.",
)
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()
