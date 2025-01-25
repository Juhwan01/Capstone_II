from enum import Enum
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
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
    hashed_password = Column(String, nullable=False)
    trust_score = Column(Float, default=0.0)
    requests = relationship("IngredientRequest", back_populates="user")

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    request_id = Column(Integer, ForeignKey('ingredient_requests.id'), nullable=False)
    transaction_location = Column(Geometry(geometry_type='POINT', srid=4326))
    appointment_time = Column(DateTime, nullable=False)
    seller_time = Column(DateTime, nullable=True)
    buyer_time = Column(DateTime, nullable=True)
    seller_time = Column(DateTime, nullable=True)
    buyer_time = Column(DateTime, nullable=True)
    
    #관계
    seller = relationship('User', foreign_keys=[seller_id], backref='sold_transactions')
    buyer = relationship('User', foreign_keys=[buyer_id], backref='bought_transactions')
    request = relationship('IngredientRequest', backref='transactions')

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

    requests = relationship("IngredientRequest", back_populates="ingredient", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="ingredient", cascade="all, delete-orphan")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 판매 고유 ID
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)  # 식재료 ID (Foreign Key)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 판매자 ID (Foreign Key)
    value = Column(Float, nullable=False)  # 판매 가격
    location_lat = Column(Float, nullable=False)  # 판매 위치 위도
    location_lon = Column(Float, nullable=False)  # 판매 위치 경도
    status = Column(String, nullable=False, default="Available")  # 판매 상태
    created_at = Column(DateTime, default=datetime.utcnow)  # 등록일
    updated_at = Column(DateTime, onupdate=datetime.utcnow)  # 수정일
    
    ingredient = relationship('Ingredient', back_populates='sales')  # Ingredient와의 관계 정의

