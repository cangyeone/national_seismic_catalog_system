from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from ..db.session import get_session


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()
