import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import anyio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()
DATABASE_URL = os.getenv('FILAMENT_DB_URI', 'sqlite+aiosqlite:///filament.db')

_AIO_ENGINE_KWARGS = {
    'sqlite+aiosqlite': {},
    'postgresql+asyncpg': {
        'pool_size': 10,
        'max_overflow': 100,
    },
}

def _get_create_engine_kwargs(url):
    parts = urlparse(url)
    scheme = parts.scheme
    if scheme not in _AIO_ENGINE_KWARGS:
        raise ValueError(f'Unsupported async scheme: {scheme}')
    return _AIO_ENGINE_KWARGS[scheme]

engine_kwargs = _get_create_engine_kwargs(DATABASE_URL)
engine = create_async_engine(DATABASE_URL, **engine_kwargs)
AsyncSession = async_sessionmaker(bind=engine)


@asynccontextmanager
async def async_session_scope(commit=True, autoflush=True):
    with anyio.CancelScope(shield=True):
        async with AsyncSession(autoflush=autoflush) as session:
            yield session
            if commit:
                await session.commit()
