from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_governance import WorkloadTls


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
    capability_center_v2: bool = True
    environment: str = "development"
    tool_gateway_url: str = "http://localhost:8090"
    model_gateway_url: str = "http://localhost:8093"
    agent_readiness_url: str = "http://localhost:8094"
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=10)
    auth_mode: str = "local"
    jwt_issuer: str = ""
    jwt_audience: str = "swarmcore-api"
    jwt_jwks_url: str = ""
    jwt_algorithms: tuple[str, ...] = ("RS256", "ES256")
    policy_mode: str = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    artifact_root: str = ".tmp/artifacts"
    artifact_gateway_url: str = ""
    artifact_capability_secret: str = "development-artifact-capability-secret-32-bytes"
    webhook_allowed_hosts: frozenset[str] = frozenset()
    cors_origins: tuple[str, ...] = ()
    deployment_mode: Literal["local", "production"] = "local"
    workload_tls_ca_file: str = ""
    workload_tls_cert_file: str = ""
    workload_tls_key_file: str = ""

    def workload_tls(self) -> WorkloadTls:
        return WorkloadTls(
            self.workload_tls_ca_file,
            self.workload_tls_cert_file,
            self.workload_tls_key_file,
        )

    @model_validator(mode="after")
    def production_boundaries_are_configured(self) -> Settings:
        self.workload_tls().validate(required=self.deployment_mode == "production")
        if self.auth_mode not in {"local", "jwt"}:
            raise ValueError("auth_mode must be local or jwt")
        if self.policy_mode not in {"local", "opa"}:
            raise ValueError("policy_mode must be local or opa")
        if self.auth_mode == "jwt" and (not self.jwt_issuer or not self.jwt_jwks_url):
            raise ValueError("JWT mode requires issuer and JWKS URL")
        if self.policy_mode == "opa" and not self.artifact_gateway_url:
            raise ValueError("OPA mode requires Artifact Gateway routing")
        if any(value == "*" for value in self.cors_origins):
            raise ValueError("wildcard CORS origins are forbidden")
        if self.deployment_mode == "production":
            if self.artifact_capability_secret.startswith("development-"):
                raise ValueError("production API requires a managed capability secret")
            if self.auth_mode != "jwt" or self.policy_mode != "opa":
                raise ValueError("production API requires JWT authentication and OPA")
            if not self.artifact_gateway_url.startswith("https://"):
                raise ValueError("production API requires HTTPS Artifact Gateway")
        return self
