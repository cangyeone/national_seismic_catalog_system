from __future__ import annotations

import asyncio
import logging
from typing import Callable

from ..processing.associator import AssociatorConfig, AssociatorService
from ..processing.locator import LocatorConfig, LocatorService
from ..processing.magnitude import MagnitudeConfig, MagnitudeService
from ..processing.mechanism import MechanismConfig, MechanismService
from ..processing.phase_picker import PhasePickerConfig, PhasePickerService
from ..processing.result_types import PhaseDetection
from .context import (
    AssociationResult,
    LocationResult,
    MagnitudeResult,
    MechanismResult,
    PhasePickResult,
    ProcessingContext,
)

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Coordinates the end-to-end processing of incoming waveform data."""

    def __init__(
        self,
        phase_picker: PhasePickerService,
        associator: AssociatorService,
        locator: LocatorService,
        magnitude: MagnitudeService,
        mechanism: MechanismService,
    ):
        self.phase_picker = phase_picker
        self.associator = associator
        self.locator = locator
        self.magnitude = magnitude
        self.mechanism = mechanism

    async def run(self, context: ProcessingContext) -> ProcessingContext:
        try:
            picks = await self._run_sync(self.phase_picker.pick_phases, context.waveform.samples)
            context.phase_picks = PhasePickResult(
                picks=[pick.__dict__ for pick in picks],
                raw_output={"count": len(picks)},
            )
        except Exception as exc:  # pragma: no cover - protective
            logger.exception("Phase picking failed")
            context.add_error(f"phase_picking: {exc}")
            return context

        try:
            associations = await self._run_sync(
                self.associator.associate,
                [PhaseDetection(**pick) for pick in context.phase_picks.picks],
            )
            context.association = AssociationResult(
                candidate_events=[candidate.__dict__ for candidate in associations]
            )
        except Exception as exc:  # pragma: no cover - protective
            logger.exception("Association failed")
            context.add_error(f"association: {exc}")
            return context

        if not context.association.candidate_events:
            logger.info("No association candidates produced")
            return context

        try:
            location_estimate = await self._run_sync(
                self.locator.locate,
                [PhaseDetection(**pick) for pick in context.phase_picks.picks],
            )
            if location_estimate:
                context.location = LocationResult(**location_estimate.__dict__)
        except Exception as exc:  # pragma: no cover - protective
            logger.exception("Location failed")
            context.add_error(f"location: {exc}")

        try:
            magnitude_estimate = await self._run_sync(
                self.magnitude.estimate,
                [PhaseDetection(**pick) for pick in context.phase_picks.picks],
            )
            if magnitude_estimate:
                context.magnitude = MagnitudeResult(**magnitude_estimate.__dict__)
        except Exception as exc:  # pragma: no cover - protective
            logger.exception("Magnitude estimation failed")
            context.add_error(f"magnitude: {exc}")

        try:
            mechanism_estimate = await self._run_sync(
                self.mechanism.invert,
                [PhaseDetection(**pick) for pick in context.phase_picks.picks],
            )
            if mechanism_estimate:
                context.mechanism = MechanismResult(**mechanism_estimate.__dict__)
        except Exception as exc:  # pragma: no cover - protective
            logger.exception("Mechanism inversion failed")
            context.add_error(f"mechanism: {exc}")

        return context

    async def _run_sync(self, func: Callable[..., object], *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def build_default_pipeline() -> ProcessingPipeline:
    phase_picker = PhasePickerService(PhasePickerConfig())
    associator = AssociatorService(AssociatorConfig())
    locator = LocatorService(LocatorConfig())
    magnitude = MagnitudeService(MagnitudeConfig())
    mechanism = MechanismService(MechanismConfig())
    return ProcessingPipeline(phase_picker, associator, locator, magnitude, mechanism)


__all__ = ["ProcessingPipeline", "build_default_pipeline"]
