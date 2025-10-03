from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .result_types import LocationEstimate, PhaseDetection


@dataclass
class LocatorConfig:
    model_checkpoint: str | None = None
    maximum_iterations: int = 200


class LocatorService:
    """Interface for the PINNLocation localization algorithm."""

    def __init__(self, config: LocatorConfig):
        self.config = config

    def locate(self, picks: Iterable[PhaseDetection]) -> LocationEstimate | None:
        """Return the location estimate for the event."""

        # TODO: integrate actual PINNLocation model.
        return None


__all__ = ["LocatorService", "LocatorConfig"]
