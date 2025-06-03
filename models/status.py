
from config.config import Base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship


class Status(Base):
    __tablename__ = 'statuses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    products = relationship("Product", back_populates="status")