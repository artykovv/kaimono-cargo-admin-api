from sqlalchemy import Column, Integer, String, Text
from config.config import Base

class Configuration(Base):
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)