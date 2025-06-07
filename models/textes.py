import re
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import validates

from config.config import Base

class Text(Base):
    __tablename__ = "textes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    name = Column(String)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None), onupdate=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None))

    @validates('key')
    def validate_key(self, key, value):
        if not re.match(r'^[a-z]+$', value):
            raise ValueError("Key может быть только на английском (a-z)")
        return value