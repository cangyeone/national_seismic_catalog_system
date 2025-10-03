from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WaveformIngestRequest(BaseModel):
    station_code: str = Field(..., description="Station code that produced the waveform")
    network: str | None = Field(default=None, description="Network code")
    sampling_rate: float = Field(..., description="Sampling rate in Hz")
    start_time: datetime
    end_time: datetime
    samples: List[float] = Field(..., description="Waveform samples in counts")
    metadata: dict | None = Field(default=None, description="Optional metadata dictionary")


class WaveformIngestResponse(BaseModel):
    waveform_file_id: int
    file_path: str
    queue_position: int | None = None
