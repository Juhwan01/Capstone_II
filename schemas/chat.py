from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional

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

    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic 2.x 대응

# ✅ 사용자 응답 스키마
class UserResponse(BaseModel):
    id: int
    nickname: str = Field(alias="name")  # nickname을 name으로 사용
    email: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # 별칭 사용 시 필요
    )
    
# ✅ 판매 상품(Sale) 응답 스키마
class ItemResponse(BaseModel):
    id: int
    title: str
    value: float  # 가격 정보 포함

    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic 2.x 대응

# ✅ 채팅방 응답 스키마 (구매자, 판매자, 상품 정보 포함)
class ChatBase(BaseModel):
    id: int
    buyer: Optional[UserResponse]  # ✅ None이 될 가능성 대비
    seller: Optional[UserResponse]
    item: Optional[ItemResponse]
    created_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic 2.x 대응
