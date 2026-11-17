from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.core.enums import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str | None = None  # Ignored by public registration to prevent privilege escalation

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
