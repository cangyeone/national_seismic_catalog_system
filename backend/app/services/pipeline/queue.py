from __future__ import annotations

import asyncio
import logging
from asyncio import Queue
from collections.abc import Awaitable, Callable

from .context import ProcessingContext
from .orchestrator import ProcessingPipeline

logger = logging.getLogger(__name__)

CompletionCallback = Callable[[ProcessingContext], Awaitable[None]]


class RealtimeQueue:
    """Async queue that drives waveform processing in the background."""

    def __init__(
        self,
        pipeline: ProcessingPipeline,
        maxsize: int = 1000,
        on_complete: CompletionCallback | None = None,
    ):
        self.pipeline = pipeline
        self.queue: Queue[ProcessingContext] = Queue(maxsize=maxsize)
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self.on_complete = on_complete

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task

    async def submit(self, context: ProcessingContext) -> None:
        await self.queue.put(context)

    async def _worker(self) -> None:
        while not self._stop_event.is_set():
            context = await self.queue.get()
            try:
                processed = await self.pipeline.run(context)
                logger.debug("Pipeline completed with errors=%s", processed.errors)
                if self.on_complete:
                    await self.on_complete(processed)
            except Exception:  # pragma: no cover - protective
                logger.exception("Pipeline execution failed")
            finally:
                self.queue.task_done()


__all__ = ["RealtimeQueue", "CompletionCallback"]
