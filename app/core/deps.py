from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.models.vendor import Vendor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Resolve the authenticated user from the bearer token."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")

    return user


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to have the ADMIN role."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")

    return current_user


def require_active_vendor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Vendor:
    """Require the authenticated user to be an active, non-suspended vendor."""
    if current_user.role != UserRole.VENDOR.value:
        raise HTTPException(status_code=403, detail="Only vendors allowed")

    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor not found")

    if not vendor.is_active:
        raise HTTPException(status_code=403, detail="Vendor account is suspended")

    return vendor
