from sqlalchemy import Column, Integer, String, Text, UUID, ForeignKey, Table
from sqlalchemy.orm import relationship
from config.config import Base
from .user import user_branches

class Branch(Base):
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    code = Column(String(25), nullable=False)
    address = Column(Text, nullable=False)
    
    products = relationship("Product", back_populates="branch")
    clients = relationship("Client", back_populates="branch")
    payments = relationship("Payment", back_populates="branch")
    users = relationship("User", secondary=user_branches, back_populates="branches")
    
    def __str__(self):
        return self.name


    