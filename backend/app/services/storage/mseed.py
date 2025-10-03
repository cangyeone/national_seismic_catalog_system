from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from obspy import Stream

from ...core.config import get_settings

settings = get_settings()


class MSeedStorage:
    """Persists waveform data to MiniSEED files on disk."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root or settings.data_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _build_path(self, station_code: str, start_time: datetime) -> Path:
        date_path = start_time.strftime("%Y/%m/%d")
        directory = self.root / station_code / date_path
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{station_code}_{start_time.strftime('%H%M%S')}.mseed"
        return directory / filename

    def save_stream(self, station_code: str, start_time: datetime, stream: Stream) -> Path:
        path = self._build_path(station_code, start_time)
        stream.write(path, format="MSEED")
        return path

    @staticmethod
    def compute_checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()


__all__ = ["MSeedStorage"]
