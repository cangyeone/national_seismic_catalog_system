"""USGS realtime data client implementation."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class USGSFeedError(RuntimeError):
    """Exception raised when fetching USGS feeds fails."""


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M:%S")


class USGSLiveClient:
    """Thin HTTP wrapper around the public USGS FDSN feeds."""

    def __init__(
        self,
        base_url: str,
        event_path: str = "/fdsnws/event/1/query",
        station_path: str = "/fdsnws/station/1/query",
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._event_path = event_path
        self._station_path = station_path
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": "NSCS-USGS-Client/1.0"},
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_events(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        min_magnitude: float | None = None,
        limit: int | None = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "format": "geojson",
            "orderby": "time",
        }
        formatted_start = _format_datetime(start_time)
        if formatted_start:
            params["starttime"] = formatted_start
        formatted_end = _format_datetime(end_time)
        if formatted_end:
            params["endtime"] = formatted_end
        if min_magnitude is not None:
            params["minmagnitude"] = min_magnitude
        if limit is not None:
            params["limit"] = limit

        logger.debug("Fetching USGS events", extra={"params": params})
        try:
            response = await self._client.get(self._event_path, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Failed to fetch USGS events", exc_info=exc)
            raise USGSFeedError("Unable to fetch USGS events feed") from exc
        return response.json()

    async def fetch_stations(
        self,
        *,
        network: str | None = None,
        channel: str | None = None,
        level: str = "station",
        format_type: str = "geojson",
        include_availability: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "format": format_type,
            "level": level,
        }
        if network:
            params["network"] = network
        if channel:
            params["channel"] = channel
        if include_availability:
            params["includeavailability"] = "true"

        logger.debug("Fetching USGS stations", extra={"params": params})
        try:
            response = await self._client.get(self._station_path, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Failed to fetch USGS stations", exc_info=exc)
            raise USGSFeedError("Unable to fetch USGS station feed") from exc
        return response.json()


__all__ = ["USGSLiveClient", "USGSFeedError"]
