import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
DATABASE_URL = os.getenv('FILAMENT_DB_URI', 'sqlite://filament.db')

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=100)
Session = sessionmaker(bind=engine)


@contextmanager
def session_scope(commit=True, autoflush=True):
    session = Session(autoflush=autoflush)
    try:
        yield session
        if commit:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
