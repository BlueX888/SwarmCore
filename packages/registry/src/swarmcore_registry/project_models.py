from __future__ import annotations

from uuid import UUID

from .models import ModelRegistration

PROJECT_MODEL_PREFIX = "model://project/"
RUNTIME_PROVIDER_NAME_PREFIX = "__runtime_provider__:"


def is_project_model_ref(reference: str) -> bool:
    return project_model_logical_id(reference).startswith(PROJECT_MODEL_PREFIX)


def project_model_logical_id(reference: str) -> str:
    return reference.rsplit("@", 1)[0]


def parse_project_model_id(reference: str) -> UUID | None:
    logical = project_model_logical_id(reference)
    if not logical.startswith(PROJECT_MODEL_PREFIX):
        return None
    suffix = logical.removeprefix(PROJECT_MODEL_PREFIX)
    try:
        return UUID(suffix)
    except ValueError:
        return None


def is_runtime_provider_name(name: str) -> bool:
    return name.startswith(RUNTIME_PROVIDER_NAME_PREFIX)


def runtime_provider_name(logical_model: str) -> str:
    return f"{RUNTIME_PROVIDER_NAME_PREFIX}{project_model_logical_id(logical_model)}"


def synthesize_project_model_registration(reference: str) -> ModelRegistration | None:
    model_id = parse_project_model_id(reference)
    if model_id is None:
        return None
    logical = f"{PROJECT_MODEL_PREFIX}{model_id}"
    version = "1"
    if "@" in reference:
        version_text = reference.rsplit("@", 1)[1]
        if version_text.isdigit() and int(version_text) >= 1:
            version = version_text
    return ModelRegistration(
        ref=f"{logical}@{version}",
        version=version,
        runtime="agno",
        providerModel=logical,
        description="项目级模型路由配置。",
        environments=("development", "production"),
    )
