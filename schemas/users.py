from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from .recipes import Recipe

# 재료 아이템 스키마
class IngredientItem(BaseModel):
    name: str
    amount: float

# 영양소 제한 스키마
class NutritionLimits(BaseModel):
    max_calories: Optional[int] = Field(None, ge=0, description="최대 칼로리 제한")
    max_carbs: Optional[float] = Field(None, ge=0, description="최대 탄수화물 제한(g)")
    max_protein: Optional[float] = Field(None, ge=0, description="최대 단백질 제한(g)")
    max_fat: Optional[float] = Field(None, ge=0, description="최대 지방 제한(g)")
    max_sodium: Optional[float] = Field(None, ge=0, description="최대 나트륨 제한(g)")

# 기본 사용자 프로필 스키마
class UserProfileBase(BaseModel):
    owned_ingredients: List[IngredientItem] = Field(
        default_factory=list,
        description="보유 중인 재료 목록"
    )
    nutrition_limits: NutritionLimits = Field(
        default_factory=NutritionLimits,
        description="영양소 제한 설정"
    )

# 사용자 프로필 생성 스키마
class UserProfileCreate(UserProfileBase):
    pass

# 사용자 프로필 업데이트 스키마
class UserProfileUpdate(BaseModel):
    owned_ingredients: Optional[List[IngredientItem]] = None
    nutrition_limits: Optional[NutritionLimits] = None

# 사용자 프로필 응답 스키마
class UserProfile(UserProfileBase):
    id: int
    user_id: int
    recipe_history: List[int] = Field(
        default=[],
        description="조회한 레시피 기록"
    )
    ratings: Dict[str, float] = Field(
        default={},
        description="레시피 평가 기록"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 추천 응답 스키마
class RecommendationResponse(BaseModel):
    recipe: Recipe
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
    nutrition_match: Dict[str, float] = Field(
        default_factory=dict,
        description="영양소 제한 대비 비율 정보"
    )

class TrustScoreUpdate(BaseModel):
    trust_score: float = Field(..., ge=0, le=100, description="신뢰도 점수 (0-100)")