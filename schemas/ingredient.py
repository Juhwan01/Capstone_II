from pydantic import BaseModel
from datetime import datetime

class IngredientCreate(BaseModel):
    name: str
    category: str
    expiry_date: datetime
    value: float
    location_lat: float
    location_lon: float
    nutrition: dict

class IngredientResponse(IngredientCreate):
    id: int

    class Config:
        from_attributes = True
