# schemas/auth.py
from typing import Optional
from datetime import datetime
from typing_extensions import Annotated
from pydantic import BaseModel, EmailStr, Field
from models.models import UserRole

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from models.models import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    nickname: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    password: Optional[str] = Field(None, min_length=8)

class User(UserBase):
    id: int
    is_active: bool
    role: UserRole
    trust_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True