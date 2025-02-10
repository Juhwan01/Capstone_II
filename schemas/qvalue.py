from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class QValueBase(BaseModel):
    user_id: int
    recipe_id: int
    value: float = Field(default=0.0, ge=0.0, le=1.0, description="Q-learning value between 0 and 1")

class QValueCreate(QValueBase):
    pass

class QValueUpdate(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0, description="Updated Q-learning value")

class QValue(QValueBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True