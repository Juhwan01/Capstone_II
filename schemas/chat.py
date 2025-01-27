from pydantic import BaseModel
from datetime import datetime
from typing import List

class MessageBase(BaseModel):
    chat_id: int
    sender_id: int
    content: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes  = True #Pydantic 1.X인 경우에 orm_mode = True로 수정

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes  = True #Pydantic 1.X인 경우에 orm_mode = True로 수정

class ChatBase(BaseModel):
    id: int
    user1: UserResponse
    user2: UserResponse
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes  = True #Pydantic 1.X인 경우에 orm_mode = True로 수정
