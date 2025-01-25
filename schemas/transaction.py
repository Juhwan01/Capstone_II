from pydantic import BaseModel
from typing import Tuple

class TransDTO(BaseModel):
    seller_id:int
    buyer_id:int
    request_id:int
    transaction_loc:Tuple[float, float]

class SuccessDTO(BaseModel):
    trans_id:int
    seller_loc:Tuple[float, float]
    buyer_loc:Tuple[float, float]
    
class CancelDTO(BaseModel):
    trans_id:int
    
