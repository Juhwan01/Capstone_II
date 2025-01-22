from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base

class UserModel(Base):
    __tablename__ = "users"

    serial_num = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

class RequestModel(Base):
    __tablename__ = "request"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.serial_num"), nullable=False)
    ingredient_id = Column(Integer, nullable=False)
    request_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)

    user = relationship("UserModel", back_populates="requests")

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey('users.serial_num'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.serial_num'), nullable=False)
    request_id = Column(Integer, ForeignKey('request.id'), nullable=False)
    transaction_location = Column(String(255), nullable=False)

    seller = relationship('UserModel', foreign_keys=[seller_id], backref='sold_transactions')
    buyer = relationship('UserModel', foreign_keys=[buyer_id], backref='bought_transactions')
    request = relationship('RequestModel', backref='transactions')

class IngredientModel(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    expire_date = Column(DateTime, nullable=False)
    amount = Column(Integer, nullable=False)

UserModel.requests = relationship("RequestModel", order_by=RequestModel.id, back_populates="user")