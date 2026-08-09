from sqlalchemy import Column,Integer,Text,DateTime,String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func

class Message(Base):
    __tablename__="message"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id=Column(Integer,ForeignKey("conversations.id"))
    role=Column(String)
    content=Column(Text)
    created_at=Column(DateTime,default=func.now())
    conversation=relationship("Conversation",back_populates="messages")
