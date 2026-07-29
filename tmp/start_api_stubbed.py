"""Start API with gRPC + greenlet stubs when Device Guard blocks native DLLs."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ensure_workspace_path() -> None:
    candidates = [
        ROOT / "apps" / "api" / "src",
        *[path / "src" for path in (ROOT / "packages").glob("*") if (path / "src").is_dir()],
        *[path / "src" for path in (ROOT / "apps").glob("*") if (path / "src").is_dir()],
    ]
    for candidate in candidates:
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)


def _install_greenlet_stub() -> None:
    try:
        import greenlet  # noqa: F401

        return
    except Exception:
        pass

    class _Greenlet:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            del args, kwargs

        def switch(self, *args, **kwargs):  # noqa: ANN002, ANN003
            del args, kwargs
            raise RuntimeError("greenlet stub cannot switch")

        @staticmethod
        def getcurrent():
            return _Greenlet()

    mod = types.ModuleType("greenlet")
    mod.greenlet = _Greenlet  # type: ignore[attr-defined]
    mod.getcurrent = _Greenlet.getcurrent  # type: ignore[attr-defined]
    sys.modules["greenlet"] = mod
    # sqlalchemy looks for greenlet.greenlet
    greenlet_mod = types.ModuleType("greenlet.greenlet")
    greenlet_mod.greenlet = _Greenlet  # type: ignore[attr-defined]
    sys.modules["greenlet.greenlet"] = greenlet_mod


def _install_grpc_stubs() -> None:
    try:
        from grpc._cython import cygrpc  # noqa: F401

        return
    except Exception:
        pass

    class _Dummy:
        def __call__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return self

        def __getattr__(self, name: str):  # noqa: ANN001
            return self

    dummy = _Dummy()
    grpc_mod = types.ModuleType("grpc")
    for name in (
        "ChannelCredentials",
        "Compression",
        "RpcError",
        "StatusCode",
        "UnaryUnaryMultiCallable",
        "Channel",
        "Server",
        "ssl_channel_credentials",
        "insecure_channel",
        "secure_channel",
        "aio",
    ):
        setattr(grpc_mod, name, dummy)
    sys.modules["grpc"] = grpc_mod
    sys.modules["grpc._cython"] = types.ModuleType("grpc._cython")
    sys.modules["grpc._cython.cygrpc"] = types.ModuleType("grpc._cython.cygrpc")
    sys.modules["grpc._compression"] = types.ModuleType("grpc._compression")
    for mod_name in (
        "opentelemetry.exporter.otlp.proto.grpc",
        "opentelemetry.exporter.otlp.proto.grpc.metric_exporter",
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    ):
        mod = types.ModuleType(mod_name)
        mod.OTLPMetricExporter = dummy  # type: ignore[attr-defined]
        mod.OTLPSpanExporter = dummy  # type: ignore[attr-defined]
        sys.modules[mod_name] = mod


if __name__ == "__main__":
    os.environ.setdefault("SWARMCORE_TELEMETRY_ENABLED", "false")
    _ensure_workspace_path()
    _install_greenlet_stub()
    _install_grpc_stubs()
    from swarmcore_api.main import run

    run()
