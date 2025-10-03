from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field("National Seismic Catalog System", description="Application name")
    database_url: str = Field(
        "sqlite:///./catalog.db",
        description="SQLAlchemy database URL for persistent storage.",
    )
    data_root: str = Field(
        "./data", description="Root directory where waveform files and artifacts are stored."
    )
    realtime_queue_maxsize: int = Field(
        1000, description="Maximum number of waveform jobs kept in memory for realtime processing."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
