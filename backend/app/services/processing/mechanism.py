from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .result_types import MechanismEstimate, PhaseDetection


@dataclass
class MechanismConfig:
    inversion_settings: dict | None = None


class MechanismService:
    """Estimate source mechanism using first motion polarities."""

    def __init__(self, config: MechanismConfig):
        self.config = config

    def invert(self, picks: Iterable[PhaseDetection]) -> MechanismEstimate | None:
        # TODO: integrate mechanism inversion workflow
        return None


__all__ = ["MechanismService", "MechanismConfig"]
