from pydantic import BaseModel
from datetime import datetime
from typing import List

class IngredientCreate(BaseModel):
    name: str
    category: str
    expiry_date: datetime
    amount: int

class IngredientResponse(IngredientCreate):
    id: int


class IngredientDeleteRequest(BaseModel):
    ingredient_ids: List[int]
    class Config:
        from_attributes = True
