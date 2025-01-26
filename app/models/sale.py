from sqlalchemy import Column, Integer, String, Float, DateTime, JSON , ForeignKey
from db.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime

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
    
    ingredient = relationship('Ingredient', back_populates='sales')  # Ingredient와의 관계 정의
