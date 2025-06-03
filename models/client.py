from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.config import Base

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    code = Column(String(255), nullable=True, index=True)
    numeric_code = Column(Integer, nullable=True)
    number = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(255), nullable=True)
    registered_at = Column(DateTime, server_default=func.now())
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)
    
    branch = relationship("Branch", back_populates="clients")
    products = relationship("Product", back_populates="client")
    payments = relationship("Payment", back_populates="client")
    notification_tasks = relationship("NotificationTask", secondary="notification_task_recipients")