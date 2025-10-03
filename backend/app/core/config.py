from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field("National Seismic Catalog System", description="Application name")
    database_url: str = Field(
        "sqlite:///./catalog.db",
        description="SQLAlchemy database URL for persistent storage.",
    )
    data_root: str = Field(
        "./data", description="Root directory for transient waveform staging before upload."
    )
    object_store_bucket: str = Field(
        "seismic-waveforms",
        description="Bucket used to archive waveform MiniSEED files.",
    )
    object_store_cache: str = Field(
        "./object_store_cache",
        description="Local cache directory that mirrors object storage uploads.",
    )
    object_store_endpoint: str | None = Field(
        default=None, description="Custom object storage endpoint if not using public cloud."
    )
    object_store_scheme: str = Field(
        "s3", description="URI scheme used when generating object storage links."
    )
    streaming_driver: str = Field(
        "inmemory",
        description="Streaming driver identifier: inmemory (default) or kafka.",
    )
    kafka_bootstrap_servers: str = Field(
        "localhost:9092", description="Kafka bootstrap servers for realtime ingestion."
    )
    kafka_security_protocol: str | None = Field(default=None)
    kafka_sasl_mechanism: str | None = Field(default=None)
    kafka_sasl_username: str | None = Field(default=None)
    kafka_sasl_password: str | None = Field(default=None)
    topic_waveforms_raw: str = Field("waveforms.raw", description="Raw waveform topic name")
    topic_waveforms_phase_picks: str = Field(
        "waveforms.phase_picks", description="Phase pick stream topic"
    )
    topic_waveforms_associations: str = Field(
        "waveforms.associations", description="Association topic name"
    )
    topic_waveforms_locations: str = Field(
        "waveforms.locations", description="Location refinement topic"
    )
    flink_job_manager_url: str | None = Field(
        default=None,
        description="Optional Apache Flink job manager endpoint for managing processing jobs.",
    )
    columnar_dsn: str = Field(
        "clickhouse://localhost:9000",
        description="Columnar analytics database DSN (e.g., ClickHouse).",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
