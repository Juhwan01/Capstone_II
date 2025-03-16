from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from models.models import GroupPurchaseStatus

class GroupPurchaseStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    COMPLETED = "completed"

class GroupPurchaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)  # 공구 가격
    original_price: float = Field(..., gt=0)  # 원래 가격
    category: str = Field(...)  # 카테고리 필드 추가
    max_participants: int = Field(default=5, ge=2, le=100)
    end_date: datetime

    # saving_price는 자동 계산
    @property
    def saving_price(self) -> float:
        return self.original_price - self.price

    # 기본값 설정
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_participants: int = Field(default=0)
    status: str = Field(default="open")

    # timezone 처리를 위한 validator 추가
    @validator('end_date', 'created_at', 'updated_at', pre=True)
    def remove_timezone(cls, v):
        if isinstance(v, datetime):
            return v.replace(tzinfo=None)
        elif isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                return dt.replace(tzinfo=None)
            except ValueError:
                return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%f")
        return v

class GroupPurchaseCreate(GroupPurchaseBase):
    pass

class GroupPurchaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    max_participants: Optional[int] = None
    status: Optional[GroupPurchaseStatus] = None
    end_date: Optional[datetime] = None

class GroupPurchase(GroupPurchaseBase):
    id: int
    created_by: int  # 생성자 ID
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ParticipantInfo(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    joined_at: datetime

    class Config:
        from_attributes = True

class GroupPurchaseDetail(GroupPurchase):
    participants_info: List[ParticipantInfo] = []

    class Config:
        from_attributes = True
