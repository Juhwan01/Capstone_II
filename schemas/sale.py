from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SaleCreate(BaseModel):
    ingredient_id: int
    ingredient_name: str
    seller_id: int
    value: float
    location_lat: float
    location_lon: float
    title: str
    expiry_date: datetime
    status: Optional[str] = Field(default="Available")
    amount: int
    contents: Optional[str]
    category: str  

class SaleImageResponse(BaseModel):
    image_url: str

class Config:
    from_attributes = True

class SaleResponse(BaseModel):
    id: int
    ingredient_id: Optional[int] = None
    ingredient_name: str
    title: str
    seller_id: int
    value: float
    location: Optional[dict] = None
    expiry_date: datetime
    status: str
    category: str  
    images: List[str] = []
    contents: Optional[str]

    class Config:
        from_attributes = True