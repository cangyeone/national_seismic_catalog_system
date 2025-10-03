from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TimeStampedModel(SQLModel):
    """Base model that records creation and update timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


class StationBase(SQLModel):
    code: str = Field(index=True)
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m: float | None = None
    is_active: bool = Field(default=True)


class Station(StationBase, TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    network: str | None = Field(default=None, index=True)
    location: str | None = None


class StationStatus(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="station.id")
    is_online: bool = Field(default=True)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    status_detail: str | None = None


class WaveformFile(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="station.id")
    start_time: datetime
    end_time: datetime
    file_path: str
    checksum: str | None = None


class PhasePick(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="station.id")
    waveform_file_id: int | None = Field(default=None, foreign_key="waveformfile.id")
    phase_type: str
    pick_time: datetime
    quality: float | None = None
    probability: float | None = None
    polarity: str | None = None


class Event(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_time: datetime
    latitude: float | None = None
    longitude: float | None = None
    depth_km: float | None = None
    magnitude: float | None = None
    magnitude_type: str | None = None
    location_uncertainty_km: float | None = None
    processing_status: str = Field(default="pending")


class EventAssociation(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    pick_id: int = Field(foreign_key="phasepick.id")
    associator: str = Field(default="REAL")
    residual: float | None = None


class SourceMechanism(TimeStampedModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    strike: float | None = None
    dip: float | None = None
    rake: float | None = None
    method: str = Field(default="first_motion")
    quality: float | None = None
