from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import structlog

logger = structlog.get_logger()

# Async SQLite DB for persistence
DATABASE_URL = "sqlite+aiosqlite:///./nvsn_production.db"

class Base(DeclarativeBase):
    pass

class Database:
    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_async_engine(
            db_url,
            echo=False,
            future=True
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        self.logger = logger.bind(component="Database")

    async def init_models(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all) # For dev reset
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database initialized", url=DATABASE_URL)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_maker() as session:
            yield session

# Singleton instance
db = Database()
