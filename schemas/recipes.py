from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal

class RecipeBase(BaseModel):
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    calories: Optional[int] = None
    carbs: Optional[Decimal] = Field(None, decimal_places=2)
    protein: Optional[Decimal] = Field(None, decimal_places=2)
    fat: Optional[Decimal] = Field(None, decimal_places=2)
    sodium: Optional[Decimal] = Field(None, decimal_places=2)
    image_small: Optional[str] = Field(None, max_length=255)
    image_large: Optional[str] = Field(None, max_length=255)
    ingredients: str
    instructions: Dict[str, Any]  # JSONB field
    cooking_img: Dict[str, Any]  # JSONB field

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    calories: Optional[int] = None
    carbs: Optional[Decimal] = None
    protein: Optional[Decimal] = None
    fat: Optional[Decimal] = None
    sodium: Optional[Decimal] = None
    image_small: Optional[str] = None
    image_large: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[Dict[str, Any]] = None
    cooking_img: Optional[Dict[str, Any]] = None

class Recipe(RecipeBase):
    id: int
    creator_id: Optional[int] = None

    class Config:
        from_attributes = True
        
class RecipeRating(BaseModel):
    rating: float = Field(..., ge=0, le=5, description="Rating value between 0 and 5")