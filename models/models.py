from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ingredients = Column(JSON)
    difficulty = Column(Integer)
    cooking_time = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"))

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    owned_ingredients = Column(JSON, default={})
    cooking_skill = Column(Integer)
    preferred_cooking_time = Column(Integer)
    recipe_history = Column(JSON, default=[])
    ratings = Column(JSON, default={})
    
    user = relationship("User", back_populates="profile")

class QValue(Base):
    __tablename__ = "q_values"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    value = Column(Float, default=0.0)