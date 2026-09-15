from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config.settings import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine, expire_on_commit=False)