from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from datetime import datetime
from db.base import Base
from sqlalchemy.dialects.postgresql import POINT
from sqlalchemy.orm import relationship

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

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    # Relationship with IngredientRequest
    requests = relationship("IngredientRequest", back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey('users.serial_num'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.serial_num'), nullable=False)
    request_id = Column(Integer, ForeignKey('request.id'), nullable=False)
    transaction_location = Column(POINT, nullable=False)

    seller = relationship('User', foreign_keys=[seller_id], backref='sold_transactions')
    buyer = relationship('User', foreign_keys=[buyer_id], backref='bought_transactions')
    request = relationship('IngredientRequest', backref='transactions')