from enum import Enum
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base
import enum

class UserRole(str, Enum):
    CHEF = "셰프"
    MASTER = "요리마스터"
    EXPERT = "집밥달인"
    NEWBIE = "새댁/새싹"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.NEWBIE)
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recipes = relationship("Recipe", back_populates="creator")
    q_values = relationship("QValue", back_populates="user")

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    ingredients = Column(JSON, nullable=False)
    difficulty = Column(Integer, nullable=False)
    cooking_time = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="recipes")
    q_values = relationship("QValue", back_populates="recipe")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owned_ingredients = Column(JSON, default={})
    cooking_skill = Column(Integer, nullable=False)
    preferred_cooking_time = Column(Integer)
    recipe_history = Column(JSON, default=[])
    ratings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")

class QValue(Base):
    __tablename__ = "q_values"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    value = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="q_values")
    recipe = relationship("Recipe", back_populates="q_values")
    

class GroupPurchaseStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    COMPLETED = "completed"

class GroupPurchase(Base):
    __tablename__ = "group_purchases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    price = Column(Float, nullable=False)
    max_participants = Column(Integer, nullable=False)
    current_participants = Column(Integer, default=0)
    status = Column(
        String,
        nullable=False,
        default='open'
    )
    updated_at = Column(DateTime(timezone=False), default=datetime.utcnow)
    end_date = Column(DateTime(timezone=False), nullable=False)
    closed_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="group_purchases")
    participants = relationship("GroupPurchaseParticipant", back_populates="group_purchase")

class GroupPurchaseParticipant(Base):
    __tablename__ = "group_purchase_participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 공동구매에 참여한 사용자 ID
    group_buy_id = Column(Integer, ForeignKey("group_purchases.id"), nullable=False)  # 참여한 공동구매 ID
    joined_at = Column(DateTime, default=datetime.utcnow)  # 참여 날짜와 시간

    # Relationships
    group_purchase = relationship("GroupPurchase", back_populates="participants")
    user = relationship("User", back_populates="group_purchase_participations")

# 기존 User 테이블에 관계 추가
User.group_purchases = relationship("GroupPurchase", back_populates="creator", lazy="dynamic")
User.group_purchase_participations = relationship("GroupPurchaseParticipant", back_populates="user", lazy="dynamic")
