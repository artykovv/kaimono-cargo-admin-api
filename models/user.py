from config.config import Base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, DateTime, String, Integer, UUID, ForeignKey, Table
from sqlalchemy.orm import relationship

# Таблица связи многие-ко-многим для пользователей и филиалов
user_branches = Table(
    'user_branches',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('user.id'), primary_key=True),
    Column('branch_id', Integer, ForeignKey('branches.id'), primary_key=True)
)

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'user'
    
    name = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    register_at = Column(DateTime, nullable=True)
    
    branches = relationship("Branch", secondary=user_branches, back_populates="users")
    payments = relationship("Payment", back_populates="taken_by")
    product_actions = relationship("ProductHistory", back_populates="action_by")

