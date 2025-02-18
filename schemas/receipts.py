from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TempReceiptUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    category: Optional[str] = None
    expiry_date: Optional[datetime] = None

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    category: Optional[str] = None
    expiry_date: Optional[datetime] = None 