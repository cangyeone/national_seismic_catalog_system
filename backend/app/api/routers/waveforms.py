from fastapi import APIRouter, Request, status

from ...schemas.waveform import WaveformIngestRequest, WaveformIngestResponse
from ...services.pipeline.context import WaveformPayload
from ...services.streaming.publisher import WaveformStreamPublisher
from ...services.utils.persistence import WaveformPersistenceService

router = APIRouter(prefix="/waveforms", tags=["waveforms"])


@router.post("/ingest", response_model=WaveformIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_waveform(request: Request, payload: WaveformIngestRequest) -> WaveformIngestResponse:
    services = request.app.state
    persistence: WaveformPersistenceService = services.waveform_persistence
    publisher: WaveformStreamPublisher = services.waveform_stream_publisher

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
    publish_result = await publisher.publish_waveform(waveform_payload)
    waveform_payload.stream_offset = publish_result.offset
    waveform_payload.stream_partition = publish_result.partition

    return WaveformIngestResponse(
        waveform_file_id=waveform_file.id,
        file_path=waveform_file.file_path,
        object_uri=waveform_payload.object_uri,
        stream_topic=publish_result.topic,
        stream_partition=publish_result.partition,
        stream_offset=publish_result.offset,
    )
