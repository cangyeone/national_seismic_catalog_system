from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ...models.base import Event
from ...schemas.events import EventRead
from ..deps import get_db_session

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[EventRead])
def list_events(session: Session = Depends(get_db_session)) -> List[Event]:
    return session.exec(select(Event).order_by(Event.event_time.desc())).all()


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: Session = Depends(get_db_session)) -> Event:
    return session.get(Event, event_id)
