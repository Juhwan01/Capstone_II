from pydantic import BaseModel
from datetime import datetime

class IngredientCreate(BaseModel):
    name: str
    category: str
    expiry_date: datetime
    amount: int

class IngredientResponse(IngredientCreate):
    id: int

    class Config:
        from_attributes = True
