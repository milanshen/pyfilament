import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()
DATABASE_URL = os.getenv('FILAMENT_DB_URI', 'sqlite://filament.db')

_AIO_SCHEMES = {
    'postgresql': 'postgresql+asyncpg',
}


def convert_to_async_url(url):
    parts = urlparse(url)
    scheme = parts.scheme
    if scheme not in _AIO_SCHEMES:
        raise ValueError(f'Unsupported async scheme: {scheme}')
    scheme = _AIO_SCHEMES[scheme]
    parts = parts._replace(scheme=scheme)
    return parts.geturl()


# use a null pool because we don't want to recycle connections
# engine = create_async_engine(convert_to_async_url(DATABASE_URL), poolclass=NullPool, echo_pool='debug')
engine = create_async_engine(convert_to_async_url(DATABASE_URL), poolclass=NullPool)
AsyncSession = async_sessionmaker(bind=engine)


@asynccontextmanager
async def async_session_scope(commit=True, autoflush=True):
    async with AsyncSession(autoflush=autoflush) as session:
        yield session
        if commit:
            await session.commit()
