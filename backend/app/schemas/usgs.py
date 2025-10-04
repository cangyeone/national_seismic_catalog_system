"""Pydantic schemas for USGS realtime feeds."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Values from USGS feeds are usually in milliseconds since epoch
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, datetime):
        return value
    return None


class USGSMeta(BaseModel):
    """Metadata describing a USGS feed."""

    generated: datetime | None = Field(
        default=None, description="Timestamp when the feed payload was generated."
    )
    title: str | None = Field(default=None, description="Human readable feed title")
    api: HttpUrl | None = Field(default=None, description="Source API endpoint")
    count: int | None = Field(default=None, description="Number of records returned")

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "USGSMeta":
        payload = payload or {}
        return cls(
            generated=_to_datetime(payload.get("generated")),
            title=payload.get("title"),
            api=payload.get("url"),
            count=payload.get("count"),
        )


class USGSEvent(BaseModel):
    """Simplified representation of a USGS realtime event."""

    event_id: str = Field(..., description="USGS event identifier")
    time: datetime | None = Field(default=None, description="Event origin time")
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    depth_km: float | None = Field(default=None)
    magnitude: float | None = Field(default=None)
    magnitude_type: str | None = Field(default=None)
    place: str | None = Field(default=None)
    status: str | None = Field(default=None)
    event_type: str | None = Field(default=None)
    detail_url: HttpUrl | None = Field(default=None)

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> "USGSEvent":
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [None, None, None]
        return cls(
            event_id=feature.get("id", ""),
            time=_to_datetime(properties.get("time")),
            latitude=coordinates[1],
            longitude=coordinates[0],
            depth_km=coordinates[2],
            magnitude=properties.get("mag"),
            magnitude_type=properties.get("magType"),
            place=properties.get("place"),
            status=properties.get("status"),
            event_type=properties.get("type"),
            detail_url=properties.get("url"),
        )


class USGSEventCollection(BaseModel):
    metadata: USGSMeta
    events: list[USGSEvent]

    @classmethod
    def from_geojson(cls, payload: dict[str, Any]) -> "USGSEventCollection":
        features = payload.get("features") or []
        return cls(
            metadata=USGSMeta.from_payload(payload.get("metadata")),
            events=[USGSEvent.from_feature(feature) for feature in features],
        )


class USGSStation(BaseModel):
    """Representation of a station returned by the USGS station feed."""

    station_id: str = Field(..., description="Unique station identifier")
    network: str | None = None
    code: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m: float | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> "USGSStation":
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [None, None, None]
        return cls(
            station_id=feature.get("id", ""),
            network=properties.get("network") or properties.get("net"),
            code=properties.get("station") or properties.get("stationcode"),
            name=properties.get("name"),
            latitude=coordinates[1],
            longitude=coordinates[0],
            elevation_m=coordinates[2] if len(coordinates) > 2 else properties.get("elevation"),
            start_time=_to_datetime(properties.get("starttime")),
            end_time=_to_datetime(properties.get("endtime")),
        )


class USGSStationCollection(BaseModel):
    metadata: USGSMeta
    stations: list[USGSStation]

    @classmethod
    def from_geojson(cls, payload: dict[str, Any]) -> "USGSStationCollection":
        features = payload.get("features") or []
        return cls(
            metadata=USGSMeta.from_payload(payload.get("metadata")),
            stations=[USGSStation.from_feature(feature) for feature in features],
        )


__all__ = [
    "USGSEventCollection",
    "USGSEvent",
    "USGSStationCollection",
    "USGSStation",
    "USGSMeta",
]
