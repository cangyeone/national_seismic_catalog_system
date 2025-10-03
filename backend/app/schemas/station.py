from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StationCreate(BaseModel):
    code: str
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m: float | None = None
    network: str | None = None
    location: str | None = None


class StationRead(StationCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StationUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    is_active: Optional[bool] = None
    network: Optional[str] = None
    location: Optional[str] = None
