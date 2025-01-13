from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 기본 레시피 정보 스키마
class RecipeBase(BaseModel):
    name: str = Field(..., description="레시피 이름")
    ingredients: Dict[str, float] = Field(
        ..., 
        description="재료와 수량 정보 (예: {'양파': 1, '감자': 2})"
    )
    difficulty: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="난이도 (1-5)"
    )
    cooking_time: int = Field(
        ..., 
        ge=5, 
        le=240, 
        description="조리 시간 (5-240분)"
    )

# 레시피 생성 스키마
class RecipeCreate(RecipeBase):
    pass

# 레시피 업데이트 스키마
class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    ingredients: Optional[Dict[str, float]] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    cooking_time: Optional[int] = Field(None, ge=5, le=240)

# 레시피 정보 응답 스키마
class Recipe(RecipeBase):
    id: int            # 레시피 고유 ID
    created_by: int    # 작성자 ID
    created_at: datetime  # 생성 시간
    updated_at: datetime  # 수정 시간

    class Config:
        from_attributes = True
        
class RecipeRating(BaseModel):
    rating: float = Field(..., ge=0, le=5, description="Rating value between 0 and 5")