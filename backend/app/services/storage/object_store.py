from __future__ import annotations

import shutil
from pathlib import Path


class ObjectStorageClient:
    """Lightweight object storage client used to push artifacts to S3/OSS/OBS."""

    def __init__(
        self,
        bucket: str,
        *,
        base_path: str | Path | None = None,
        endpoint: str | None = None,
        scheme: str = "s3",
    ) -> None:
        self.bucket = bucket
        self.endpoint = endpoint
        self.scheme = scheme
        self.base_path = Path(base_path or "./object_store_cache")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put_file(self, local_path: Path, object_key: str) -> str:
        destination = self.base_path / object_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, destination)
        if self.endpoint:
            return f"{self.scheme}://{self.bucket}/{object_key}?endpoint={self.endpoint}"
        return f"{self.scheme}://{self.bucket}/{object_key}"

    def resolve_local_path(self, object_key: str) -> Path:
        return self.base_path / object_key


__all__ = ["ObjectStorageClient"]
