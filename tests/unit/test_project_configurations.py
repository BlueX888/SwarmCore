from __future__ import annotations

from pathlib import Path

import pytest
from swarmcore_application import ConfigurationKind, ProjectConfigurationService


@pytest.mark.parametrize(
    ("kind", "source_ref"),
    [
        (ConfigurationKind.AGENT, "inline/agno"),
        (ConfigurationKind.AGENT, "agent://builtin/researcher@1"),
        (ConfigurationKind.TOOL, "tool://search@1"),
        (ConfigurationKind.MODEL, "model://general@1"),
    ],
)
def test_saved_configuration_accepts_supported_registry_sources(
    kind: ConfigurationKind, source_ref: str
) -> None:
    ProjectConfigurationService().validate(
        kind=kind,
        name="可复用配置",
        source_ref=source_ref,
        configuration={"enabled": True},
    )


@pytest.mark.parametrize(
    ("kind", "source_ref"),
    [
        (ConfigurationKind.AGENT, "agent://missing@1"),
        (ConfigurationKind.TOOL, "tool://missing@1"),
        (ConfigurationKind.MODEL, "model://missing@1"),
    ],
)
def test_saved_configuration_rejects_unknown_registry_sources(
    kind: ConfigurationKind, source_ref: str
) -> None:
    with pytest.raises(ValueError, match="not present"):
        ProjectConfigurationService().validate(
            kind=kind,
            name="无效配置",
            source_ref=source_ref,
            configuration={"enabled": True},
        )


def test_filesystem_tool_configuration_rejects_host_absolute_paths() -> None:
    with pytest.raises(ValueError, match="host absolute paths"):
        ProjectConfigurationService().validate(
            kind=ConfigurationKind.TOOL,
            name="fs-bad",
            source_ref="tool://filesystem/read-text@1",
            configuration={
                "tool-1": {
                    "type": "tool",
                    "tool": "tool://filesystem/read-text@1",
                    "input": {"mount": "workspace", "path": "/etc/passwd"},
                }
            },
        )


def test_project_configuration_migration_enforces_tenant_and_project_rls() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0007_project_configurations.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0006_m4_governance"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration
    assert "app.project_id" in migration
