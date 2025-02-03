from enum import Enum
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base

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
    requests = relationship("IngredientRequest", back_populates="user", cascade="all, delete-orphan")


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

class IngredientRequest(Base):
    __tablename__ = 'ingredient_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)  # 사용자 ID
    ingredient_id = Column(Integer, ForeignKey('ingredients.id', ondelete="CASCADE"), nullable=False)  # 식재료 ID
    request_type = Column(String(50), nullable=False)  # 요청 유형 ('Request', 'Offer')
    status = Column(String(50), default='Pending')  # 요청 상태 ('Pending', 'Completed', 'Rejected')
    created_at = Column(DateTime, default=datetime.utcnow)  # 요청 생성 시간

    # 관계 정의
    user = relationship("User", back_populates="requests")
    ingredient = relationship("Ingredient", back_populates="requests")

class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    nutrition = Column(JSON, nullable=True)

    requests = relationship("IngredientRequest", back_populates="ingredient", cascade="all, delete-orphan")

    

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
    username = Column(String, ForeignKey("users.username"), nullable=False)  # user_id 대신 username으로 변경
    group_buy_id = Column(Integer, ForeignKey("group_purchases.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group_purchase = relationship("GroupPurchase", back_populates="participants")
    user = relationship("User", back_populates="group_purchase_participations", foreign_keys=[username])  # foreign_key 변경

# 기존 User 테이블에 관계 추가
User.group_purchases = relationship("GroupPurchase", back_populates="creator", lazy="dynamic")
User.group_purchase_participations = relationship("GroupPurchaseParticipant", back_populates="user", lazy="dynamic")

class TempReceipt(Base):
    __tablename__ = 'temp_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
