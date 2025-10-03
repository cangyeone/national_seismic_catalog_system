from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import events, stations, waveforms
from .core.config import get_settings
from .db.session import init_db, session_factory
from .services.storage.mseed import MSeedStorage
from .services.storage.object_store import ObjectStorageClient
from .services.streaming.message_bus import InMemoryMessageBus, KafkaMessageBus, MessageBus
from .services.streaming.publisher import WaveformStreamPublisher, WaveformStreamTopics
from .services.utils.persistence import WaveformPersistenceService

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    storage = MSeedStorage(Path(settings.data_root))
    object_store = ObjectStorageClient(
        settings.object_store_bucket,
        base_path=settings.object_store_cache,
        endpoint=settings.object_store_endpoint,
        scheme=settings.object_store_scheme,
    )
    waveform_persistence = WaveformPersistenceService(
        storage,
        session_factory,
        object_store=object_store,
    )

    bus: MessageBus
    if settings.streaming_driver.lower() == "kafka":
        bus = KafkaMessageBus(
            settings.kafka_bootstrap_servers,
            security_protocol=settings.kafka_security_protocol,
            sasl_mechanism=settings.kafka_sasl_mechanism,
            sasl_username=settings.kafka_sasl_username,
            sasl_password=settings.kafka_sasl_password,
        )
    else:
        bus = InMemoryMessageBus()
    await bus.start()

    topics = WaveformStreamTopics(
        raw_waveforms=settings.topic_waveforms_raw,
        phase_picks=settings.topic_waveforms_phase_picks,
        associations=settings.topic_waveforms_associations,
        locations=settings.topic_waveforms_locations,
    )
    stream_publisher = WaveformStreamPublisher(bus, topics)

    app.state.waveform_persistence = waveform_persistence
    app.state.waveform_stream_publisher = stream_publisher
    app.state.message_bus = bus
    app.state.stream_topics = topics
    try:
        yield
    finally:
        await bus.stop()


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
