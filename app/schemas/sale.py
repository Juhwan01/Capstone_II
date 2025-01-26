from pydantic import BaseModel, Field
from typing import Optional

class SaleCreate(BaseModel):
    ingredient_id: int
    ingredient_name : str
    seller_id: int
    value: float
    location_lat: float
    location_lon: float
    status: Optional[str] = Field(default="Available")

class SaleResponse(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name : str
    seller_id: int
    value: float
    location : dict
    status: str

    class Config:
        orm_mode = True
