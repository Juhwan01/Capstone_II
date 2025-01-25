from pydantic import BaseModel, Field
from typing import Tuple
from datetime import datetime

class TransDTO(BaseModel):
    seller_id: int
    buyer_id: int
    request_id: int
    transaction_loc: Tuple[float, float]
    appointment_time: datetime

class SuccessDTO(BaseModel):
    trans_id: int

class ArriveDTO(BaseModel):
    trans_id:int
    id:int
    location: Tuple[float, float]

class CancelDTO(BaseModel):
    trans_id: int
