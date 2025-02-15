from enum import Enum
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime, Numeric, Enum as SQLAlchemyEnum, func, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
from geoalchemy2 import Geometry

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
    nickname = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.NEWBIE)
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    address_name = Column(String, nullable=False)
    zone_no = Column(String, nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recipes = relationship("Recipe", back_populates="creator")
    q_values = relationship("QValue", back_populates="user")
    requests = relationship("IngredientRequest", back_populates="user", cascade="all, delete-orphan")
    chats_as_user1 = relationship("Chat", foreign_keys="[Chat.user1_id]", back_populates="user1")
    chats_as_user2 = relationship("Chat", foreign_keys="[Chat.user2_id]", back_populates="user2")
    sales = relationship("Sale", back_populates="seller", cascade="all, delete-orphan")
    group_purchases = relationship("GroupPurchase", back_populates="creator", lazy="dynamic")
    group_purchase_participations = relationship("GroupPurchaseParticipant", back_populates="user", lazy="dynamic")  

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owned_ingredients = Column(JSON, default={})
    nutrition_limits = Column(JSON, default={})  # 추가된 부분
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
    amount = Column(Integer , nullable= False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    requests = relationship("IngredientRequest", back_populates="ingredient", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="ingredient", cascade="all, delete-orphan")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 판매 고유 ID
    ingredient_name = Column(String)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)  # 식재료 ID (Foreign Key)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 판매자 ID (Foreign Key)
    value = Column(Float, nullable=False)  # 판매 가격
    location_lat = Column(Float, nullable=False)  # 판매 위치 위도
    location_lon = Column(Float, nullable=False)  # 판매 위치 경도
    status = Column(String, nullable=False, default="Available")  # 판매 상태
    expiry_date = Column(DateTime, nullable=False)
    contents = Column(String , nullable= False ) # 내용 추가
    image_url = Column(String, nullable=True)  # ✅ 이미지 URL 필드 추가

    ingredient = relationship('Ingredient', back_populates='sales')  # Ingredient와의 관계 정의
    seller = relationship("User", back_populates="sales")  # 관계 설정

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    seller_time = Column(DateTime, nullable=True)
    buyer_time = Column(DateTime, nullable=True)
    
    buyer = relationship('User', foreign_keys=[buyer_id], backref='bought_transactions')
    request = relationship('Sale', backref='transactions')

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="chats_as_user1", lazy="joined")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="chats_as_user2", lazy="joined")
    messages = relationship("Message", back_populates="chat", lazy="joined")  # 즉시 로드

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    chat = relationship("Chat", back_populates="messages")

class Recipe(Base):
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("users.id"),nullable=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255))
    calories = Column(Integer)
    carbs = Column(Numeric(10, 2))
    protein = Column(Numeric(10, 2))
    fat = Column(Numeric(10, 2))
    sodium = Column(Numeric(10, 2))
    image_small = Column(String(255))
    image_large = Column(String(255))
    ingredients = Column(JSONB)
    instructions = Column(JSONB)
    cooking_img = Column(JSONB)

    # Relationships
    creator = relationship("User", back_populates="recipes")
    q_values = relationship("QValue", back_populates="recipe")

class GroupPurchaseStatus(str, Enum):
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



class TempReceipt(Base):
    __tablename__ = 'temp_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)