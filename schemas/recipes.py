from typing import Dict, List, Optional
from pydantic import BaseModel

class RecipeBase(BaseModel):
    name: str
    ingredients: Dict[str, float]
    difficulty: int
    cooking_time: int

class RecipeCreate(RecipeBase):
    pass

class Recipe(RecipeBase):
    id: int
    created_by: Optional[int]
    
    class Config:
        orm_mode = True

class RecommendationResponse(BaseModel):
    recipe: Recipe
    score: float
    is_exploration: bool