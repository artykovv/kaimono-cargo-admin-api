from sqlalchemy import (
    Column,
    Integer,
    UUID,
    DateTime,
    String,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from config.config import Base

class ProductHistory(Base):
    __tablename__ = 'product_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # Например, 'created', 'issued', 'updated'
    action_by_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    action_at = Column(DateTime, nullable=False, server_default=func.now())
    description = Column(String(255), nullable=True)  # Дополнительное описание действия
    
    product = relationship("Product", back_populates="history")
    action_by = relationship("User", back_populates="product_actions")