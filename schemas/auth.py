# schemas/auth.py
from typing import Optional
from datetime import datetime
from typing_extensions import Annotated
from pydantic import BaseModel, EmailStr, Field
from models.models import UserRole

# 토큰 응답 스키마
class Token(BaseModel):
    access_token: str  # JWT 접근 토큰
    token_type: str    # 토큰 타입 (Bearer)

# 토큰 데이터 스키마
class TokenData(BaseModel):
    email: Optional[str] = None  # 토큰에 저장될 이메일 정보

# 기본 사용자 정보 스키마
class UserBase(BaseModel):
    email: EmailStr    # 이메일 (유효성 검사 포함)
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="사용자 이름 (3-50자 사이)"
    )

# 사용자 생성 스키마
class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        description="비밀번호 (최소 8자)"
    )

# 사용자 정보 업데이트 스키마
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
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