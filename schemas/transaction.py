from pydantic import BaseModel, Field
from typing import Tuple
from datetime import datetime

class TransDTO(BaseModel):
    buyer_id: int
    sale_id: int
    appointment_time: datetime

class StatusDTO(BaseModel):
    trans_id: int

class ArriveDTO(BaseModel):
    trans_id:int
    id:int
    location: Tuple[float, float]