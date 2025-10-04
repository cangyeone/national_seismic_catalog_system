"""FastAPI routes exposing USGS realtime data."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ...schemas.usgs import USGSEventCollection, USGSStationCollection
from ...services.usgs import USGSLiveClient, USGSFeedError
from ..deps import get_usgs_client

router = APIRouter(prefix="/usgs", tags=["usgs"])


@router.get("/events/live", response_model=USGSEventCollection)
async def get_usgs_live_events(
    client: USGSLiveClient = Depends(get_usgs_client),
    start_time: Annotated[
        datetime | None, Query(description="Filter events starting from this UTC timestamp")
    ] = None,
    end_time: Annotated[
        datetime | None, Query(description="Filter events ending before this UTC timestamp")
    ] = None,
    min_magnitude: Annotated[
        float | None, Query(ge=0, description="Minimum magnitude threshold")
    ] = None,
    limit: Annotated[
        int | None, Query(gt=0, le=500, description="Maximum number of events to return")
    ] = 50,
) -> USGSEventCollection:
    try:
        payload = await client.fetch_events(
            start_time=start_time,
            end_time=end_time,
            min_magnitude=min_magnitude,
            limit=limit,
        )
    except USGSFeedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return USGSEventCollection.from_geojson(payload)


@router.get("/stations/live", response_model=USGSStationCollection)
async def get_usgs_live_stations(
    client: USGSLiveClient = Depends(get_usgs_client),
    network: Annotated[
        str | None, Query(description="Restrict to a specific FDSN network code")
    ] = None,
    channel: Annotated[
        str | None,
        Query(description="Restrict to a specific channel code pattern (e.g., BH?)"),
    ] = None,
    include_availability: Annotated[
        bool, Query(description="Include availability/operational windows in the response")
    ] = False,
) -> USGSStationCollection:
    try:
        payload = await client.fetch_stations(
            network=network,
            channel=channel,
            include_availability=include_availability,
        )
    except USGSFeedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return USGSStationCollection.from_geojson(payload)
