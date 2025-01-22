from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from db.base import Base

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
