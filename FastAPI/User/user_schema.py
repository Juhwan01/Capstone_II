from pydantic import BaseModel

class TransDTO(BaseModel):
    seller_id:int
    buyer_id:int
    request_id:int
    transaction_loc:str

class TransCloseDTO(BaseModel):
    trans_id:int