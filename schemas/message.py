from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    content: str
    sender_id: int
    chat_id: int

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True