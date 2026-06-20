from pydantic import BaseModel, EmailStr
from app.core.enums import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = UserRole.CUSTOMER.value

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
