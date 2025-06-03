from config.config import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Table, Text
from sqlalchemy.orm import relationship


class NotificationTask(Base):
    __tablename__ = 'notification_tasks'
    
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    error_message = Column(Text, nullable=True)
    
    recipients = relationship("Client", secondary="notification_task_recipients")
    images = relationship("NotificationImage", back_populates="task")  # Добавлена связь


class NotificationImage(Base):
    __tablename__ = 'notification_images'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('notification_tasks.id'))
    image = Column(String(255), nullable=False)  # Путь к файлу
    
    task = relationship("NotificationTask", back_populates="images")  # Исправлено


# Таблица связи многие-ко-многим для задач уведомлений и получателей
notification_task_recipients = Table(
    'notification_task_recipients',
    Base.metadata,
    Column('notification_task_id', Integer, ForeignKey('notification_tasks.id'), primary_key=True),
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True)
)