from __future__ import annotations

import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkloadTls:
    """mTLS material shared by internal Gateway servers and workload clients."""

    ca_file: str = ""
    cert_file: str = ""
    key_file: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.ca_file and self.cert_file and self.key_file)

    def validate(self, *, required: bool = False) -> WorkloadTls:
        configured = tuple(bool(value) for value in (self.ca_file, self.cert_file, self.key_file))
        if any(configured) and not all(configured):
            raise ValueError("workload mTLS requires CA, certificate, and private key")
        if required and not self.enabled:
            raise ValueError("production mode requires workload mTLS")
        if self.enabled:
            for path in (self.ca_file, self.cert_file, self.key_file):
                if not Path(path).is_file():
                    raise ValueError(f"workload mTLS file does not exist: {path}")
        return self

    def client_context(self) -> ssl.SSLContext | None:
        if not self.enabled:
            return None
        context = ssl.create_default_context(cafile=self.ca_file)
        context.load_cert_chain(self.cert_file, self.key_file)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context

    def uvicorn_options(self) -> dict[str, Any]:
        if not self.enabled:
            return {}
        return {
            "ssl_ca_certs": self.ca_file,
            "ssl_certfile": self.cert_file,
            "ssl_keyfile": self.key_file,
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
        }
