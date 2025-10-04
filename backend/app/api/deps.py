from collections.abc import Generator

from fastapi import Depends, Request
from sqlmodel import Session

from ..db.session import get_session
from ..services.usgs import USGSLiveClient


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()


def get_usgs_client(request: Request) -> USGSLiveClient:
    client = getattr(request.app.state, "usgs_client", None)
    if client is None:
        raise RuntimeError("USGS client has not been initialised")
    return client
