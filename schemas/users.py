from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .recipes import Recipe

# 기본 사용자 프로필 스키마
class UserProfileBase(BaseModel):
    cooking_skill: int = Field(
        default=3, 
        ge=1, 
        le=5, 
        description="요리 실력 (1-5)"
    )
    preferred_cooking_time: int = Field(
        default=30, 
        ge=5, 
        le=240, 
        description="선호하는 조리 시간 (5-240분)"
    )
    owned_ingredients: Dict[str, float] = Field(
        default={},
        description="보유 중인 재료 목록"
    )

# 사용자 프로필 생성 스키마
class UserProfileCreate(UserProfileBase):
    pass

# 사용자 프로필 업데이트 스키마
class UserProfileUpdate(BaseModel):
    cooking_skill: Optional[int] = Field(None, ge=1, le=5)
    preferred_cooking_time: Optional[int] = Field(None, ge=5, le=240)
    owned_ingredients: Optional[Dict[str, float]] = None

# 사용자 프로필 응답 스키마
class UserProfile(UserProfileBase):
    id: int            # 프로필 고유 ID
    user_id: int       # 사용자 ID
    recipe_history: List[int] = Field(
        default=[], 
        description="조회한 레시피 기록"
    )
    ratings: Dict[str, float] = Field(
        default={},
        description="레시피 평가 기록"
    )
    created_at: datetime  # 생성 시간
    updated_at: datetime  # 수정 시간

    class Config:
        from_attributes = True

# 추천 응답 스키마
class RecommendationResponse(BaseModel):
    recipe: Recipe     # 추천된 레시피 정보
    score: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="추천 점수 (0-1 사이)"
    )
    is_exploration: bool = Field(
        ..., 
        description="탐색적 추천 여부"
    )

class TrustScoreUpdate(BaseModel):
    trust_score: float = Field(..., ge=0, le=100, description="신뢰도 점수 (0-100)")