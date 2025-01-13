from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
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
    ingredients = Column(JSON, nullable=False)  # {ingredient_name: amount}
    difficulty = Column(Integer, nullable=False)  # 1-5 scale
    cooking_time = Column(Integer, nullable=False)  # in minutes
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
    owned_ingredients = Column(JSON, default={})  # {ingredient_name: amount}
    cooking_skill = Column(Integer, nullable=False)  # 1-5 scale
    preferred_cooking_time = Column(Integer)  # in minutes
    recipe_history = Column(JSON, default=[])  # List of recipe IDs
    ratings = Column(JSON, default={})  # {recipe_id: rating}
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