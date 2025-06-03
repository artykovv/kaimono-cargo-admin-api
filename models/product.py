from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    DECIMAL,
    Table,
    func
)
from sqlalchemy.orm import relationship
from config.config import Base

from .payment import payment_products

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_code = Column(String(255), nullable=False, index=True)
    weight = Column(DECIMAL(10, 2), nullable=True)
    price = Column(Integer, nullable=True)
    date = Column(Date, nullable=False, index=True)
    take_time = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, server_default=func.now())
    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)
    
    status = relationship("Status", back_populates="products")
    client = relationship("Client", back_populates="products")
    branch = relationship("Branch", back_populates="products")
    payments = relationship("Payment", secondary=payment_products, back_populates="products")
