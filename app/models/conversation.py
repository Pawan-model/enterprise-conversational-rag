from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func

class Conversation(Base):
    __tablename__='conversations'
    id=Column(Integer,primary_key=True,index=True)
    created_at=Column(DateTime,default=func.now())
    messages=relationship("Message",
                          back_populates='conversation',
                          cascade="all,delete-orphan")
    