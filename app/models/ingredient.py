from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from db.base import Base
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
