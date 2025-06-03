from config.config import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, DECIMAL, UUID, Table
from sqlalchemy.orm import relationship

# Таблица связи многие-ко-многим для платежей и продуктов
payment_products = Table(
    'payment_products',
    Base.metadata,
    Column('payment_id', Integer, ForeignKey('payments.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    payments = relationship("Payment", back_populates="payment_method")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=True)
    paid_at = Column(DateTime, server_default=func.now())
    taken_by_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=True)
    
    client = relationship("Client", back_populates="payments")
    branch = relationship("Branch", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
    taken_by = relationship("User")
    products = relationship("Product", secondary=payment_products, back_populates="payments")