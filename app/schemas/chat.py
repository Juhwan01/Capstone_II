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
        orm_mode = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True

class ChatBase(BaseModel):
    id: int
    user1: UserResponse
    user2: UserResponse
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True
