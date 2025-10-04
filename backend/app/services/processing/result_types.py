from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class PhaseDetection:
    station_code: str
    phase_type: str
    pick_time: datetime
    probability: float
    polarity: str | None = None
    extra: Dict[str, Any] | None = None


@dataclass
class AssociationCandidate:
    origin_time: datetime
    latitude: float | None
    longitude: float | None
    depth_km: float | None
    score: float
    method: str


@dataclass
class LocationEstimate:
    latitude: float
    longitude: float
    depth_km: float
    uncertainty_km: float
    diagnostics: Dict[str, Any]


@dataclass
class MagnitudeEstimate:
    magnitude: float
    magnitude_type: str
    diagnostics: Dict[str, Any]


@dataclass
class MechanismEstimate:
    strike: float
    dip: float
    rake: float
    method: str
    diagnostics: Dict[str, Any]
