from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ...models.base import Station
from ...schemas.station import StationCreate, StationRead, StationUpdate
from ..deps import get_db_session

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/", response_model=List[StationRead])
def list_stations(session: Session = Depends(get_db_session)) -> List[Station]:
    return session.exec(select(Station)).all()


@router.post("/", response_model=StationRead, status_code=status.HTTP_201_CREATED)
def create_station(
    payload: StationCreate, session: Session = Depends(get_db_session)
) -> Station:
    station = Station.from_orm(payload)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station


@router.get("/{station_id}", response_model=StationRead)
def get_station(station_id: int, session: Session = Depends(get_db_session)) -> Station:
    station = session.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    return station


@router.patch("/{station_id}", response_model=StationRead)
def update_station(
    station_id: int, payload: StationUpdate, session: Session = Depends(get_db_session)
) -> Station:
    station = session.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(station, key, value)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(station_id: int, session: Session = Depends(get_db_session)) -> None:
    station = session.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    session.delete(station)
    session.commit()
