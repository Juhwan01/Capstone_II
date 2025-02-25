
from pydantic import BaseModel
from datetime import datetime
from typing import List

# ✅ 메시지 기본 스키마
class MessageBase(BaseModel):
    chat_id: int
    sender_id: int
    content: str

class ChatCreate(BaseModel):
    buyer_id: int
    seller_id: int
    item_id: int

class ChatQuery(BaseModel):
    user_id: int

class MessageCreate(MessageBase):
    """클라이언트에서 메시지를 보낼 때 사용"""
    pass

class MessageResponse(MessageBase):
    """서버가 메시지를 반환할 때 사용"""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # Pydantic 1.x의 orm_mode=True 대응

# ✅ 사용자 응답 스키마
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # Pydantic 1.x의 orm_mode=True 대응

# ✅ 판매 상품(Sale) 응답 스키마
class ItemResponse(BaseModel):
    id: int
    title: str
    value: float  # 가격 정보 포함

    class Config:
        from_attributes = True  # Pydantic 1.x의 orm_mode=True 대응

# ✅ 채팅방 응답 스키마 (구매자, 판매자, 상품 정보 포함)
class ChatBase(BaseModel):
    id: int
    buyer: UserResponse  # 구매자 정보
    seller: UserResponse  # 판매자 정보
    item: ItemResponse  # 채팅 대상 상품 정보
    created_at: datetime
    messages: List[MessageResponse] = []  # 해당 채팅방의 메시지 목록

    class Config:
        from_attributes = True  # Pydantic 1.x의 orm_mode=True 대응
