from collections.abc import Generator

from sqlalchemy import Connection, create_engine

from app.config import settings

engine = create_engine(settings.sqlalchemy_url, fast_executemany=True, pool_pre_ping=True)


def get_connection() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn
