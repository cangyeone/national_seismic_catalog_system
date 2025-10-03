from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import events, stations, waveforms
from .core.config import get_settings
from .db.session import init_db, session_factory
from .services.pipeline.context import ProcessingContext
from .services.pipeline.orchestrator import build_default_pipeline
from .services.pipeline.queue import RealtimeQueue
from .services.storage.mseed import MSeedStorage
from .services.utils.persistence import WaveformPersistenceService, persist_processing_result

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    storage = MSeedStorage(Path(settings.data_root))
    waveform_persistence = WaveformPersistenceService(storage, session_factory)
    pipeline = build_default_pipeline()

    async def handle_completion(context: ProcessingContext) -> None:
        await persist_processing_result(context, session_factory)

    realtime_queue = RealtimeQueue(
        pipeline=pipeline,
        maxsize=settings.realtime_queue_maxsize,
        on_complete=handle_completion,
    )

    app.state.waveform_persistence = waveform_persistence
    app.state.realtime_queue = realtime_queue

    await realtime_queue.start()
    try:
        yield
    finally:
        await realtime_queue.stop()


def create_application() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(stations.router)
    app.include_router(waveforms.router)
    app.include_router(events.router)
    return app


app = create_application()
