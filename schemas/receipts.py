from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TempReceiptUpdate(BaseModel):
    name: Optional[str] = None

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[int] = None
    category: Optional[str] = None
    expiry_date: Optional[datetime] = None 