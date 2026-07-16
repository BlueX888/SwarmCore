from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SWARMCORE_", env_file=".env", extra="ignore", case_sensitive=False
    )

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    event_poll_interval_seconds: float = Field(default=0.5, gt=0, le=5)
    event_heartbeat_seconds: float = Field(default=15, ge=5, le=60)
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
