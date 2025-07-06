
from config.config import Base
from sqlalchemy import Column, Integer, String, Boolean

class AddressPhoto(Base):
    __tablename__ = 'address_photos'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=False)

class AddressVideo(Base):
    __tablename__ = 'address_videos'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=False)