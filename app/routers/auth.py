from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/login",
    summary="Authenticate user",
    description="Validates user credentials and returns a JWT bearer token.",
)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role}
    )

    return {"access_token": token, "token_type": "bearer"}
