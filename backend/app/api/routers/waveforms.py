from fastapi import APIRouter, Request, status

from ...schemas.waveform import WaveformIngestRequest, WaveformIngestResponse
from ...services.pipeline.context import ProcessingContext, WaveformPayload
from ...services.pipeline.queue import RealtimeQueue
from ...services.utils.persistence import WaveformPersistenceService

router = APIRouter(prefix="/waveforms", tags=["waveforms"])


@router.post("/ingest", response_model=WaveformIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_waveform(request: Request, payload: WaveformIngestRequest) -> WaveformIngestResponse:
    services = request.app.state
    persistence: WaveformPersistenceService = services.waveform_persistence
    queue: RealtimeQueue = services.realtime_queue

    waveform_payload = WaveformPayload(
        station_code=payload.station_code,
        network=payload.network,
        start_time=payload.start_time,
        end_time=payload.end_time,
        samples=payload.samples,
        sampling_rate=payload.sampling_rate,
        metadata=payload.metadata or {},
    )

    waveform_file = persistence.store_waveform(waveform_payload)

    context = ProcessingContext(waveform=waveform_payload)
    await queue.submit(context)

    queue_size = queue.queue.qsize()

    return WaveformIngestResponse(
        waveform_file_id=waveform_file.id,
        file_path=waveform_file.file_path,
        queue_position=queue_size,
    )
