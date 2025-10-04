from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .result_types import MagnitudeEstimate, PhaseDetection


@dataclass
class MagnitudeConfig:
    reference_model: str | None = None


class MagnitudeService:
    """Computes magnitude based on processed waveform data."""

    def __init__(self, config: MagnitudeConfig):
        self.config = config

    def estimate(self, picks: Iterable[PhaseDetection]) -> MagnitudeEstimate | None:
        # TODO: implement magnitude estimation (e.g., ML or empirical relations)
        return None


__all__ = ["MagnitudeService", "MagnitudeConfig"]
