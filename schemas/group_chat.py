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
        orm_mode = True


class GroupChatParticipantBase(BaseModel):
    user_id: int
    chatroom_id: int


class GroupChatParticipantCreate(GroupChatParticipantBase):
    pass


class GroupChatParticipant(GroupChatParticipantBase):
    id: int
    joined_at: datetime

    class Config:
        orm_mode = True


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
        orm_mode = True


class GroupChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    content: str  # 클라이언트에는 'content'로 일관되게 제공
    chatroom_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class ChatHistoryResponse(BaseModel):
    type: str = "history"
    messages: List[GroupChatMessageResponse]


class ConnectionResponse(BaseModel):
    type: str = "connection"
    status: str
    chatroom_id: int


class ErrorResponse(BaseModel):
    type: str = "error"
    message: str


class ChatMessageRequest(BaseModel):
    type: str = "chat"
    content: str