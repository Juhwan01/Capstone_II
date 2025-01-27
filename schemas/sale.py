from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SaleCreate(BaseModel):
    ingredient_id: int
    ingredient_name : str
    seller_id: int
    value: float
    location_lat: float
    location_lon: float
    expiry_date: datetime
    status: Optional[str] = Field(default="Available")

class SaleResponse(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name : str
    seller_id: int
    value: float
    location : dict
    expiry_date: datetime
    status: str

    class Config:
        from_attributes = True #Pydantic 1.X인 경우에 orm_mode = True로 수정
