import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from os import environ

SQLALCHEMY_DATABASE_URL = environ.get("SQLALCHEMY_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("SQLALCHEMY_DATABASE_URL is not set")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=20, max_overflow=10
)

SessionLocalAsync = async_sessionmaker(bind=async_engine, autoflush=False)

Base = declarative_base()


async def get_db():
    db = async_scoped_session(
        async_sessionmaker(bind=async_engine, autoflush=False),
        lambda: asyncio.current_task(),
    )
    try:
        yield db
    finally:
        await db.close()
