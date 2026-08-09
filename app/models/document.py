from sqlalchemy import Column, Integer, String
from app.db.session import Base
from sqlalchemy.orm import relationship


class Document(Base):

    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename=Column(String)
    filepath=Column(String)
    chunks=relationship('DocumentChunk',
                        back_populates='document',
                        cascade='all,delete-orphan')
    