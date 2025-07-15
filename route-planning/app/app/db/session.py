from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# Tworzenie silnika bazy danych
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Tworzenie sesji
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Baza dla modeli
Base = declarative_base()

# Dependency do pobierania sesji bazy danych
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
