from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class IngredientCreate(BaseModel):
    name: str
    category: str
    expiry_date: datetime
    amount: int

class IngredientResponse(IngredientCreate):
    id: int


class IngredientDeleteRequest(BaseModel):
    ingredient_ids: List[int]

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    expiry_date: Optional[datetime] = None
    amount: Optional[int] = None      

    class Config:
        from_attributes = True
