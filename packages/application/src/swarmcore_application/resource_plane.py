from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import ResourceAccessMode, ResourceKind, ResourceReplayability
from swarmcore_persistence import AuditRepository, IdempotencyConflictError
from swarmcore_persistence.models import (
    CapabilityPackVersion,
    CapabilityResourceBinding,
    Connection,
    ConnectionVersion,
    OutboxEvent,
    ProjectCapabilityBinding,
    ResourceDefinition,
    ResourceSnapshot,
)
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import CapabilityPackManifest

_CREDENTIAL_SCHEMES = ("vault://", "secret://", "aws-secretsmanager://", "azure-keyvault://")
_SECRET_KEYS = {"password", "secret", "token", "api_key", "apikey", "credential"}


@dataclass(frozen=True, slots=True)
class ResourceReadiness:
    ready: bool
    blockers: tuple[str, ...]
    cache_key: str


class FakeConnector:
    """Deterministic connector used only by tests and local qualification."""

    async def health(self, configuration: dict[str, Any]) -> bool:
        return not bool(configuration.get("unhealthy", False))

    async def read(self, locator: dict[str, Any]) -> dict[str, Any]:
        value = locator.get("value", {})
        return value if isinstance(value, dict) else {"value": value}


class ConnectionService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        connector_ref: str,
        configuration: dict[str, Any],
        credential_ref: str,
        policy_ref: str | None,
        actor: str,
    ) -> tuple[Connection, ConnectionVersion]:
        self._validate(connector_ref, configuration, credential_ref)
        connection = Connection(
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            connector_ref=connector_ref,
            current_version=1,
        )
        session.add(connection)
        await session.flush()
        version = self._version(
            connection,
            version=1,
            configuration=configuration,
            credential_ref=credential_ref,
            policy_ref=policy_ref,
            actor=actor,
        )
        session.add(version)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="connection.create",
            resource_type="connection",
            resource_id=str(connection.id),
            metadata={"connectorRef": connector_ref, "version": 1},
        )
        return connection, version

    async def add_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        connection_id: UUID,
        configuration: dict[str, Any],
        credential_ref: str,
        policy_ref: str | None,
        actor: str,
    ) -> tuple[ConnectionVersion, bool]:
        connection = await session.scalar(
            select(Connection)
            .where(
                Connection.id == connection_id,
                Connection.tenant_id == tenant_id,
                Connection.project_id == project_id,
            )
            .with_for_update()
        )
        if connection is None:
            raise LookupError("CONNECTION_NOT_FOUND")
        self._validate(connection.connector_ref, configuration, credential_ref)
        digest = _connection_hash(configuration, credential_ref, policy_ref)
        existing = await session.scalar(
            select(ConnectionVersion).where(
                ConnectionVersion.connection_id == connection_id,
                ConnectionVersion.configuration_hash == digest,
            )
        )
        if existing is not None:
            return existing, False
        connection.current_version += 1
        version = self._version(
            connection,
            version=connection.current_version,
            configuration=configuration,
            credential_ref=credential_ref,
            policy_ref=policy_ref,
            actor=actor,
        )
        session.add(version)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="connection.version",
            resource_type="connection",
            resource_id=str(connection.id),
            metadata={"configurationHash": version.configuration_hash, "version": version.version},
        )
        return version, True

    async def list(
        self, session: AsyncSession, *, tenant_id: UUID, project_id: UUID
    ) -> list[Connection]:
        return list(
            await session.scalars(
                select(Connection)
                .where(Connection.tenant_id == tenant_id, Connection.project_id == project_id)
                .order_by(Connection.name)
            )
        )

    async def queue_health_check(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        connection_id: UUID,
        idempotency_key: str,
        actor: str,
    ) -> tuple[UUID, ConnectionVersion]:
        _, version = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            connection_id=connection_id,
        )
        command_id = uuid5(
            NAMESPACE_URL,
            f"swarmcore:{tenant_id}:{project_id}:{connection_id}:health:{idempotency_key}",
        )
        payload = {
            "commandId": str(command_id),
            "connectionId": str(connection_id),
            "connectionVersionId": str(version.id),
            "actor": actor,
        }
        existing = await session.scalar(
            select(OutboxEvent).where(
                OutboxEvent.destination == "tool",
                OutboxEvent.source_id == command_id,
            )
        )
        if existing is not None:
            if existing.payload != payload:
                raise IdempotencyConflictError(
                    "connection health idempotency key was reused after the connection changed"
                )
            return command_id, version
        session.add(
            OutboxEvent(
                tenant_id=tenant_id,
                aggregate_id=connection_id,
                destination="tool",
                partition_key=str(connection_id),
                source_id=command_id,
                type="connection.health-check.requested",
                payload=payload,
            )
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="connection.health-check.requested",
            resource_type="connection",
            resource_id=str(connection_id),
            metadata={"commandId": str(command_id), "connectionVersionId": str(version.id)},
        )
        await session.flush()
        return command_id, version

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        connection_id: UUID,
    ) -> tuple[Connection, ConnectionVersion]:
        connection = await session.scalar(
            select(Connection).where(
                Connection.id == connection_id,
                Connection.tenant_id == tenant_id,
                Connection.project_id == project_id,
            )
        )
        if connection is None:
            raise LookupError("CONNECTION_NOT_FOUND")
        version = await session.scalar(
            select(ConnectionVersion).where(
                ConnectionVersion.connection_id == connection.id,
                ConnectionVersion.version == connection.current_version,
            )
        )
        if version is None:
            raise RuntimeError("connection current version is missing")
        return connection, version

    @staticmethod
    def _validate(connector_ref: str, configuration: dict[str, Any], credential_ref: str) -> None:
        if not connector_ref.startswith("connector://") or "@" not in connector_ref:
            raise ValueError("CONNECTOR_NOT_REGISTERED")
        if not credential_ref.startswith(_CREDENTIAL_SCHEMES):
            raise ValueError("CONNECTION_SECRET_UNAVAILABLE")
        if _contains_secret(configuration):
            raise ValueError("CONNECTION_CONFIGURATION_CONTAINS_SECRET")

    @staticmethod
    def _version(
        connection: Connection,
        *,
        version: int,
        configuration: dict[str, Any],
        credential_ref: str,
        policy_ref: str | None,
        actor: str,
    ) -> ConnectionVersion:
        return ConnectionVersion(
            tenant_id=connection.tenant_id,
            project_id=connection.project_id,
            connection_id=connection.id,
            version=version,
            configuration=configuration,
            credential_ref=credential_ref,
            policy_ref=policy_ref,
            configuration_hash=_connection_hash(configuration, credential_ref, policy_ref),
            created_by=actor,
        )


class ResourceCatalogService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        connection_id: UUID,
        resource_kind: str,
        name: str,
        locator: dict[str, Any],
        schema_ref: str | None,
        media_type: str | None,
        sensitivity: str,
        actor: str,
    ) -> ResourceDefinition:
        try:
            ResourceKind(resource_kind)
        except ValueError as exc:
            raise ValueError("RESOURCE_KIND_INVALID") from exc
        if _contains_secret(locator):
            raise ValueError("RESOURCE_LOCATOR_CONTAINS_SECRET")
        connection = await session.scalar(
            select(Connection).where(
                Connection.id == connection_id,
                Connection.tenant_id == tenant_id,
                Connection.project_id == project_id,
            )
        )
        if connection is None:
            raise ValueError("OBJECT_RELATION_SCOPE_MISMATCH")
        resource = ResourceDefinition(
            tenant_id=tenant_id,
            project_id=project_id,
            connection_id=connection_id,
            resource_kind=resource_kind,
            name=name,
            locator=locator,
            schema_ref=schema_ref,
            media_type=media_type,
            sensitivity=sensitivity,
        )
        session.add(resource)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="resource.create",
            resource_type="resource_definition",
            resource_id=str(resource.id),
        )
        return resource

    async def list(
        self, session: AsyncSession, *, tenant_id: UUID, project_id: UUID
    ) -> list[ResourceDefinition]:
        return list(
            await session.scalars(
                select(ResourceDefinition)
                .where(
                    ResourceDefinition.tenant_id == tenant_id,
                    ResourceDefinition.project_id == project_id,
                )
                .order_by(ResourceDefinition.name)
            )
        )


class ResourceSnapshotService:
    async def record(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation_id: UUID,
        slot: str,
        resource_definition_id: UUID,
        snapshot_key: str,
        connection_version_id: UUID,
        direction: str,
        replayability: str,
        observed_version: str | None = None,
        etag: str | None = None,
        content_hash: str | None = None,
        artifact_id: UUID | None = None,
        blob_id: UUID | None = None,
        non_replayable_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[ResourceSnapshot, bool]:
        try:
            replay = ResourceReplayability(replayability)
        except ValueError as exc:
            raise ValueError("RESOURCE_SNAPSHOT_FAILED") from exc
        if replay is ResourceReplayability.NON_REPLAYABLE and not non_replayable_reason:
            raise ValueError("RESOURCE_NOT_REPLAYABLE")
        if artifact_id is not None and blob_id is not None:
            raise ValueError("RESOURCE_SNAPSHOT_FAILED")
        if metadata is not None and _contains_secret(metadata):
            raise ValueError("RESOURCE_SNAPSHOT_FAILED")
        existing = await session.scalar(
            select(ResourceSnapshot).where(
                ResourceSnapshot.evaluation_id == evaluation_id,
                ResourceSnapshot.slot == slot,
                ResourceSnapshot.snapshot_key == snapshot_key,
            )
        )
        if existing is not None:
            return existing, False
        snapshot = ResourceSnapshot(
            tenant_id=tenant_id,
            project_id=project_id,
            evaluation_id=evaluation_id,
            slot=slot,
            resource_definition_id=resource_definition_id,
            snapshot_key=snapshot_key,
            connection_version_id=connection_version_id,
            direction=direction,
            observed_version=observed_version,
            etag=etag,
            content_hash=content_hash,
            artifact_id=artifact_id,
            blob_id=blob_id,
            replayability=replay.value,
            non_replayable_reason=non_replayable_reason,
            metadata_json=metadata or {},
        )
        session.add(snapshot)
        await session.flush()
        return snapshot, True


class ResourceReadinessService:
    async def inspect(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        binding: CapabilityResourceBinding,
        executor_available: bool,
        secret_available: bool,
        healthy: bool,
        policy_allowed: bool,
    ) -> ResourceReadiness:
        resource = await session.scalar(
            select(ResourceDefinition).where(
                ResourceDefinition.id == binding.resource_definition_id,
                ResourceDefinition.tenant_id == tenant_id,
                ResourceDefinition.project_id == project_id,
            )
        )
        if resource is None:
            return ResourceReadiness(False, ("RESOURCE_BINDING_MISSING",), "missing")
        connection = await session.scalar(
            select(Connection).where(
                Connection.id == resource.connection_id,
                Connection.tenant_id == tenant_id,
                Connection.project_id == project_id,
            )
        )
        if connection is None:
            return ResourceReadiness(False, ("CONNECTION_VERSION_INVALID",), "missing")
        version = await session.scalar(
            select(ConnectionVersion).where(
                ConnectionVersion.connection_id == connection.id,
                ConnectionVersion.version == connection.current_version,
            )
        )
        blockers: list[str] = []
        if version is None:
            blockers.append("CONNECTION_VERSION_INVALID")
        if not executor_available:
            blockers.append("CONNECTOR_EXECUTOR_MISSING")
        if not secret_available:
            blockers.append("CONNECTION_SECRET_UNAVAILABLE")
        if not healthy:
            blockers.append("RESOURCE_HEALTH_CHECK_FAILED")
        if not policy_allowed:
            blockers.append("RESOURCE_POLICY_DENIED")
        cache_key = canonical_hash(
            {
                "tenantId": str(tenant_id),
                "projectId": str(project_id),
                "bindingId": str(binding.id),
                "resourceId": str(resource.id),
                "connectionVersionId": str(version.id) if version else None,
            }
        )
        return ResourceReadiness(not blockers, tuple(blockers), cache_key)


class CapabilityBindingService:
    async def bind_resource(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        project_capability_binding_id: UUID,
        slot: str,
        resource_definition_id: UUID,
        access_mode: str,
        mapping_configuration: dict[str, Any],
        actor: str,
        capability_pack_version_id: UUID | None = None,
    ) -> CapabilityResourceBinding:
        ResourceAccessMode(access_mode)
        pack_binding = await session.scalar(
            select(ProjectCapabilityBinding).where(
                ProjectCapabilityBinding.id == project_capability_binding_id,
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.project_id == project_id,
            )
        )
        resource = await session.scalar(
            select(ResourceDefinition).where(
                ResourceDefinition.id == resource_definition_id,
                ResourceDefinition.tenant_id == tenant_id,
                ResourceDefinition.project_id == project_id,
            )
        )
        if pack_binding is None or resource is None:
            raise ValueError("OBJECT_RELATION_SCOPE_MISMATCH")
        pack_version = await session.scalar(
            select(CapabilityPackVersion).where(
                CapabilityPackVersion.id
                == (capability_pack_version_id or pack_binding.pack_version_id),
                CapabilityPackVersion.tenant_id == tenant_id,
            )
        )
        if pack_version is None:
            raise ValueError("CAPABILITY_PACK_VERSION_NOT_FOUND")
        manifest = CapabilityPackManifest.model_validate(pack_version.manifest)
        slot_contract = next(
            (candidate for candidate in manifest.spec.resources if candidate.slot == slot), None
        )
        if slot_contract is None:
            raise ValueError("RESOURCE_SLOT_NOT_DECLARED")
        if (
            resource.resource_kind not in slot_contract.resource_kinds
            or access_mode != slot_contract.access_mode
        ):
            raise ValueError("RESOURCE_BINDING_SCHEMA_MISMATCH")
        binding = await session.scalar(
            select(CapabilityResourceBinding).where(
                CapabilityResourceBinding.project_capability_binding_id
                == project_capability_binding_id,
                CapabilityResourceBinding.slot == slot,
            )
        )
        if binding is None:
            binding = CapabilityResourceBinding(
                tenant_id=tenant_id,
                project_id=project_id,
                project_capability_binding_id=project_capability_binding_id,
                slot=slot,
                resource_definition_id=resource_definition_id,
                access_mode=access_mode,
                mapping_configuration=mapping_configuration,
                bound_by=actor,
            )
            session.add(binding)
        else:
            binding.resource_definition_id = resource_definition_id
            binding.access_mode = access_mode
            binding.mapping_configuration = mapping_configuration
            binding.bound_by = actor
        await session.flush()
        return binding


def _contains_secret(value: Any, key: str = "") -> bool:
    normalized = key.lower().replace("-", "_")
    if normalized in _SECRET_KEYS or any(token in normalized for token in ("password", "token")):
        return True
    if isinstance(value, dict):
        return any(_contains_secret(nested, str(name)) for name, nested in value.items())
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return False


def _connection_hash(
    configuration: dict[str, Any], credential_ref: str, policy_ref: str | None
) -> str:
    return canonical_hash(
        {
            "configuration": configuration,
            "credentialRef": credential_ref,
            "policyRef": policy_ref,
        }
    )
