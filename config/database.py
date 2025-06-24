from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=10,           # Max number of connections in the pool
    max_overflow=20,        # Allow temporary extra connections
    pool_timeout=30,        # Time to wait for a connection from the pool
    pool_recycle=1800,      # Recycle connections every 30 minutes (1800 seconds)
    pool_pre_ping=True      # Test connections before using them
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
   async with async_session_maker() as session:
       yield session