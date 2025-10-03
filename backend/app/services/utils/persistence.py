from __future__ import annotations


import numpy as np
from obspy import Stream, Trace, UTCDateTime
from sqlmodel import Session, select

from ...models.base import Event, Station, WaveformFile
from ...services.pipeline.context import ProcessingContext, WaveformPayload
from ..storage.mseed import MSeedStorage

SessionFactory = Callable[[], Session]


class WaveformPersistenceService:
    """Handles conversion of raw waveform samples into stored MiniSEED files."""

    def __init__(self, storage: MSeedStorage, session_factory: SessionFactory):
        self.storage = storage
        self.session_factory = session_factory

    def store_waveform(self, payload: WaveformPayload) -> WaveformFile:
        samples = np.asarray(payload.samples, dtype="float32")
        stats = {
            "network": payload.network or "",
            "station": payload.station_code,
            "starttime": UTCDateTime(payload.start_time),
            "sampling_rate": payload.sampling_rate,
        }
        trace = Trace(data=samples, header=stats)
        stream = Stream(traces=[trace])
        path = self.storage.save_stream(payload.station_code, payload.start_time, stream)
        checksum = self.storage.compute_checksum(path)

        with self.session_factory() as session:
            station = session.exec(
                select(Station).where(Station.code == payload.station_code)
            ).first()
            if not station:
                station = Station(code=payload.station_code, network=payload.network)
                session.add(station)
                session.commit()
                session.refresh(station)

            waveform_file = WaveformFile(
                station_id=station.id,
                start_time=payload.start_time,
                end_time=payload.end_time,
                file_path=str(path),
                checksum=checksum,
            )
            session.add(waveform_file)
            session.commit()
            session.refresh(waveform_file)

        payload.file_path = path
        return waveform_file


async def persist_processing_result(
    context: ProcessingContext, session_factory: SessionFactory
) -> None:
    """Persist processing results produced by the pipeline."""

    def _persist() -> None:
        with session_factory() as session:
            if context.location:
                event = Event(
                    event_time=context.waveform.start_time,
                    latitude=context.location.latitude,
                    longitude=context.location.longitude,
                    depth_km=context.location.depth_km,
                    location_uncertainty_km=context.location.uncertainty_km,
                    processing_status="located" if not context.errors else "error",
                )
                if context.magnitude:
                    event.magnitude = context.magnitude.magnitude
                    event.magnitude_type = context.magnitude.magnitude_type
                session.add(event)
                session.commit()
            else:
                session.add(
                    Event(
                        event_time=context.waveform.start_time,
                        processing_status="pending",
                    )
                )
                session.commit()

    await asyncio.to_thread(_persist)
