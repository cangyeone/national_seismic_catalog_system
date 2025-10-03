from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from .result_types import PhaseDetection


@dataclass
class PhasePickerConfig:
    model_path: str | None = None
    batch_size: int = 32
    probability_threshold: float = 0.5


class PhasePickerService:
    """Interface to the neural network based phase picking system."""

    def __init__(self, config: PhasePickerConfig):
        self.config = config

    def pick_phases(self, waveform: Any) -> List[PhaseDetection]:
        """Run the neural network on the waveform samples.

        The implementation here is a stub that returns synthetic results but retains
        the interface required by the rest of the system. Integration with the
        actual model should replace this method.
        """

        # TODO: replace with real model inference
        return []


__all__ = ["PhasePickerService", "PhasePickerConfig"]
