from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    event_time: datetime
    latitude: float | None = None
    longitude: float | None = None
    depth_km: float | None = None
    magnitude: float | None = None
    magnitude_type: str | None = None


class EventRead(EventCreate):
    id: int
    location_uncertainty_km: float | None
    processing_status: str
    created_at: datetime
    updated_at: datetime


class EventUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth_km: Optional[float] = None
    magnitude: Optional[float] = None
    magnitude_type: Optional[str] = None
    location_uncertainty_km: Optional[float] = None
    processing_status: Optional[str] = None
