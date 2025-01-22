from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    # Relationship with IngredientRequest
    requests = relationship("IngredientRequest", back_populates="user", cascade="all, delete-orphan")
        # Relationships
    chats_as_user1 = relationship("Chat", foreign_keys="[Chat.user1_id]", back_populates="user1")
    chats_as_user2 = relationship("Chat", foreign_keys="[Chat.user2_id]", back_populates="user2")