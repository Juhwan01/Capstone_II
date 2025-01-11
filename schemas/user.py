from typing import Dict, List, Optional
from pydantic import BaseModel

class UserProfileBase(BaseModel):
    cooking_skill: int = 3
    preferred_cooking_time: int = 30
    owned_ingredients: Dict[str, float] = {}

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int
    recipe_history: List[int] = []
    ratings: Dict[str, float] = {}
    
    class Config:
        orm_mode = True