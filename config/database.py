from os import getenv

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.settings import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=getenv("SQL_ECHO") == "1")

async_session = async_sessionmaker(engine, expire_on_commit=False)
