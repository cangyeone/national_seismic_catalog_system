from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from ..core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=False, future=True)


def init_db() -> None:
    """Create database tables if they do not exist."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def session_factory() -> Session:
    return Session(engine)
