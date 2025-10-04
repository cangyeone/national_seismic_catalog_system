from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.deps import get_usgs_client
from app.main import app


class DummyUSGSClient:
    async def fetch_events(self, **_: dict) -> dict:
        return {
            "metadata": {
                "generated": 1_710_000_000_000,
                "title": "USGS Real-time",
                "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
                "count": 1,
            },
            "features": [
                {
                    "id": "us7000abcd",
                    "properties": {
                        "time": 1_710_000_000_500,
                        "mag": 4.2,
                        "magType": "ml",
                        "place": "Demo Location",
                        "status": "reviewed",
                        "type": "earthquake",
                        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000abcd",
                    },
                    "geometry": {
                        "coordinates": [-122.3, 37.5, 8.1],
                    },
                }
            ],
        }

    async def fetch_stations(self, **_: dict) -> dict:
        return {
            "metadata": {
                "generated": datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000,
                "title": "USGS Station Feed",
                "url": "https://earthquake.usgs.gov/fdsnws/station/1/query",
                "count": 1,
            },
            "features": [
                {
                    "id": "NC.TEST..BHZ",
                    "properties": {
                        "network": "NC",
                        "stationcode": "TEST",
                        "name": "Test Station",
                        "starttime": "2023-01-01T00:00:00Z",
                        "endtime": None,
                    },
                    "geometry": {
                        "coordinates": [-121.5, 36.1, 1200.0],
                    },
                }
            ],
        }


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_usgs_events_endpoint_returns_normalised_payload():
    dummy_client = DummyUSGSClient()
    app.dependency_overrides[get_usgs_client] = lambda: dummy_client
    try:
        with TestClient(app) as client:
            response = client.get("/usgs/events/live")
        assert response.status_code == 200
        payload = response.json()
        assert payload["metadata"]["count"] == 1
        assert payload["events"][0]["event_id"] == "us7000abcd"
        assert payload["events"][0]["magnitude"] == 4.2
    finally:
        app.dependency_overrides.pop(get_usgs_client, None)


def test_usgs_stations_endpoint_returns_station_coordinates():
    dummy_client = DummyUSGSClient()
    app.dependency_overrides[get_usgs_client] = lambda: dummy_client
    try:
        with TestClient(app) as client:
            response = client.get("/usgs/stations/live")
        assert response.status_code == 200
        payload = response.json()
        assert payload["metadata"]["count"] == 1
        station = payload["stations"][0]
        assert station["network"] == "NC"
        assert station["latitude"] == 36.1
        assert station["longitude"] == -121.5
    finally:
        app.dependency_overrides.pop(get_usgs_client, None)
