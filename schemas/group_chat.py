from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class GroupChatroomBase(BaseModel):
    group_purchase_id: int

class GroupChatroomCreate(GroupChatroomBase):
    pass

class GroupChatroom(GroupChatroomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GroupChatMessageBase(BaseModel):
    chatroom_id: int
    sender_id: int
    message: str

class GroupChatMessageCreate(GroupChatMessageBase):
    pass

class GroupChatMessage(GroupChatMessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
