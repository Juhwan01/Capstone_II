from enum import Enum
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime, Numeric, Enum as SQLAlchemyEnum, func, Text, UniqueConstraint
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
    profile_image_url = Column(String, nullable=True)  
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recipes = relationship("Recipe", back_populates="creator")
    q_values = relationship("QValue", back_populates="user")
    requests = relationship("IngredientRequest", back_populates="user", cascade="all, delete-orphan")
    chats_as_buyer = relationship("Chat", foreign_keys="[Chat.buyer_id]", back_populates="buyer")
    chats_as_seller = relationship("Chat", foreign_keys="[Chat.seller_id]", back_populates="seller")
    sales = relationship("Sale", back_populates="seller", cascade="all, delete-orphan")
    group_purchases = relationship("GroupPurchase", back_populates="creator", lazy="dynamic")
    group_purchase_participations = relationship("GroupPurchaseParticipant", back_populates="user", lazy="dynamic")  
    group_chat_participations = relationship("GroupChatParticipant", back_populates="user")
    messages = relationship("GroupChatMessage", back_populates="sender")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    nutrition_limits = Column(JSON, default={})  # 영양소 제한만 남김
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

    requests = relationship("IngredientRequest", back_populates="ingredient")
    sales = relationship("Sale", back_populates="ingredient")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 판매 고유 ID
    ingredient_name = Column(String)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=True, default=None)  # 식재료 ID (Foreign Key)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 판매자 ID (Foreign Key)
    value = Column(Float, nullable=False)  # 판매 가격
    category = Column(String , nullable=False)
    location_lat = Column(Float, nullable=False)  # 판매 위치 위도
    location_lon = Column(Float, nullable=False)  # 판매 위치 경도
    title = Column (String , nullable=False)
    status = Column(String, nullable=False, default="Available")  # 판매 상태
    expiry_date = Column(DateTime, nullable=False)
    contents = Column(String , nullable= False ) # 내용 추가
    amount = Column(Integer, nullable=False)
    
    seller = relationship("User", back_populates="sales")  # 판매자와의 관계
    ingredient = relationship("Ingredient", back_populates="sales")  # 식재료와의 관계
    images = relationship("Image", back_populates="sale", cascade="all, delete")  # 판매 이미지 관계
    chats = relationship("Chat", back_populates="item", cascade="all, delete")  # Chat과 연결됨 (새롭게 추가!)

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=True)
    image_url = Column(String, nullable=True)
    group_purchase_id = Column(Integer, ForeignKey("group_purchases.id", ondelete="CASCADE"), nullable=True)

    sale = relationship("Sale", back_populates="images")
    group_purchase = relationship("GroupPurchase", back_populates="images")

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)
    appointment_time = Column(DateTime, nullable=False)
    seller_time = Column(DateTime, nullable=True)
    buyer_time = Column(DateTime, nullable=True)
    status = Column(String(50), default='Trading')

    buyer = relationship('User', foreign_keys=[buyer_id], backref='bought_transactions')
    request = relationship('Sale', backref='transactions')
    __table_args__ = (
        UniqueConstraint('sale_id', 'status', name='uq_sale_status'),
    )

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("sales.id"), nullable=False)  # 상품 ID 추가
    created_at = Column(DateTime, default=func.now())

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="chats_as_buyer", lazy="joined")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="chats_as_seller", lazy="joined")
    item = relationship("Sale", back_populates="chats",lazy="joined")  # Sale(판매 상품)과의 관계
    messages = relationship("Message", back_populates="chat", lazy="joined")

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
    price = Column(Float, nullable=False)  # 공구 가격
    original_price = Column(Float, nullable=False)  # 원래 가격
    saving_price = Column(Float, nullable=False)  # 절약 가능 금액
    category = Column(String, nullable=False)  # 카테고리 추가
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
    # 기존 GroupPurchase 모델에 채팅방 관계 추가
    chatroom = relationship("GroupChatroom", back_populates="group_purchase", uselist=False)
    images = relationship("Image", back_populates="group_purchase", cascade="all, delete")  # 이미지 관계 추가

class GroupPurchaseParticipant(Base):
    __tablename__ = "group_purchase_participants"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username", onupdate="CASCADE"), nullable=False)
    group_buy_id = Column(Integer, ForeignKey("group_purchases.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group_purchase = relationship("GroupPurchase", back_populates="participants")
    user = relationship("User", back_populates="group_purchase_participations", foreign_keys=[username])

class GroupChatroom(Base):
    __tablename__ = "group_chatrooms"

    id = Column(Integer, primary_key=True, index=True)
    group_purchase_id = Column(Integer, ForeignKey("group_purchases.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group_purchase = relationship("GroupPurchase", back_populates="chatroom")
    messages = relationship("GroupChatMessage", back_populates="chatroom")
    participants = relationship("GroupChatParticipant", back_populates="chatroom")

class GroupChatParticipant(Base):
    __tablename__ = "group_chat_participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chatroom_id = Column(Integer, ForeignKey("group_chatrooms.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="group_chat_participations")
    chatroom = relationship("GroupChatroom", back_populates="participants")

class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(Integer, ForeignKey("group_chatrooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chatroom = relationship("GroupChatroom", back_populates="messages")
    sender = relationship("User", back_populates="messages")

    
class TempReceipt(Base):
    __tablename__ = 'temp_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)