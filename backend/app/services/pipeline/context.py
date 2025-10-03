from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WaveformPayload:
    """Container for waveform data traveling through the processing pipeline."""

    station_code: str
    network: str | None
    start_time: datetime
    end_time: datetime
    samples: Any  # numpy array or bytes depending on ingest source
    sampling_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Path | None = None
    object_uri: str | None = None
    storage_key: str | None = None
    stream_offset: int | None = None
    stream_partition: int | None = None


@dataclass
class PhasePickResult:
    picks: List[Dict[str, Any]]
    raw_output: Dict[str, Any] | None = None


@dataclass
class AssociationResult:
    candidate_events: List[Dict[str, Any]]


@dataclass
class LocationResult:
    latitude: float
    longitude: float
    depth_km: float
    uncertainty_km: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MagnitudeResult:
    magnitude: float
    magnitude_type: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MechanismResult:
    strike: float
    dip: float
    rake: float
    method: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingContext:
    """State object that is passed through the processing pipeline."""

    waveform: WaveformPayload
    phase_picks: Optional[PhasePickResult] = None
    association: Optional[AssociationResult] = None
    location: Optional[LocationResult] = None
    magnitude: Optional[MagnitudeResult] = None
    mechanism: Optional[MechanismResult] = None
    errors: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
