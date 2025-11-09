import contextlib
from typing import Any, AsyncIterator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from os import environ

from sqlalchemy.orm.decl_api import DeclarativeBase

SQLALCHEMY_DATABASE_URL = environ.get("SQLALCHEMY_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("SQLALCHEMY_DATABASE_URL is not set")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

Base: DeclarativeBase = declarative_base()


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        default_kwargs = {
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "echo_pool": False,
        }
        default_kwargs.update(engine_kwargs)

        self._engine = create_async_engine(host, **default_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine
        )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(SQLALCHEMY_DATABASE_URL)


def get_sessionmanager():
    return sessionmanager


async def get_db():
    async with sessionmanager.session() as session:
        yield session
