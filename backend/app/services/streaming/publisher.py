from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from ..pipeline.context import WaveformPayload
from .message_bus import MessageBus, PublishResult


@dataclass
class WaveformStreamTopics:
    """Holds topic names used throughout the streaming pipeline."""

    raw_waveforms: str = "waveforms.raw"
    phase_picks: str = "waveforms.phase_picks"
    associations: str = "waveforms.associations"
    locations: str = "waveforms.locations"


class WaveformStreamPublisher:
    """Publishes waveform metadata into the realtime streaming bus."""

    def __init__(self, bus: MessageBus, topics: WaveformStreamTopics | None = None):
        self.bus = bus
        self.topics = topics or WaveformStreamTopics()

    async def publish_waveform(self, payload: WaveformPayload) -> PublishResult:
        record = self._build_payload(payload)
        key = f"{payload.network or 'NA'}:{payload.station_code}:{payload.start_time.isoformat()}"
        return await self.bus.publish(self.topics.raw_waveforms, key=key, value=record)

    def _build_payload(self, payload: WaveformPayload) -> Dict[str, Any]:
        window_seconds = (payload.end_time - payload.start_time).total_seconds()
        return {
            "station_code": payload.station_code,
            "network": payload.network,
            "start_time": payload.start_time.isoformat(),
            "end_time": payload.end_time.isoformat(),
            "sampling_rate": payload.sampling_rate,
            "sample_count": len(payload.samples) if hasattr(payload.samples, "__len__") else None,
            "window_seconds": window_seconds,
            "object_uri": payload.object_uri,
            "object_key": payload.storage_key,
            "metadata": payload.metadata,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        }


__all__ = ["WaveformStreamPublisher", "WaveformStreamTopics"]
