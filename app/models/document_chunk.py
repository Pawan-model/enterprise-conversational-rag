from sqlalchemy import Column, Integer, ForeignKey, DateTime ,Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class DocumentChunk(Base):
    __tablename__="document_chunks"
    id=Column(Integer,primary_key=True, index=True)
    document_id= Column(Integer,ForeignKey("documents.id"))
    chunk_index=Column(Integer)
    page_number=Column(Integer)
    content=Column(Text)
    created_at=Column(DateTime,default=func.now())
    document=relationship('Document',
                          back_populates='chunks')