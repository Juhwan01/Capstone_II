from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class TransDTO(BaseModel):
    buyer_id: int
    sale_id: int
    appointment_time: datetime

class StatusDTO(BaseModel):
    sale_id: int

class ArriveDTO(BaseModel):
    sale_id:int
    id:int
    location: List[float]