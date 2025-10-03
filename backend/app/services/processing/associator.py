from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .result_types import AssociationCandidate, PhaseDetection


@dataclass
class AssociatorConfig:
    window_seconds: float = 120.0
    minimum_picks: int = 4


class AssociatorService:
    """Wrapper around REAL or similar associator algorithms."""

    def __init__(self, config: AssociatorConfig):
        self.config = config

    def associate(self, picks: Iterable[PhaseDetection]) -> List[AssociationCandidate]:
        """Associate phase picks into candidate events.

        In the production system this should call REAL. The stub implementation
        simply returns an empty list but the surrounding infrastructure can handle
        the results when integration happens.
        """

        # TODO: integrate REAL associator
        return []


__all__ = ["AssociatorService", "AssociatorConfig"]
