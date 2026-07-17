from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlsplit


class WebhookError(RuntimeError):
    pass


@dataclass(frozen=True)
class WebhookEnvelope:
    delivery_id: str
    timestamp: int
    event_type: str
    payload: dict[str, object]

    def body(self) -> bytes:
        return json.dumps(
            {
                "deliveryId": self.delivery_id,
                "timestamp": self.timestamp,
                "type": self.event_type,
                "data": self.payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()


class WebhookSigner:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise WebhookError("webhook secret must contain at least 32 bytes")
        self._secret = secret

    def sign(self, envelope: WebhookEnvelope) -> str:
        return "v1=" + hmac.new(self._secret, envelope.body(), hashlib.sha256).hexdigest()

    def verify(self, envelope: WebhookEnvelope, signature: str, *, now: int | None = None) -> None:
        current = int(time.time()) if now is None else now
        if abs(current - envelope.timestamp) > 300:
            raise WebhookError("webhook is outside the replay window")
        if not hmac.compare_digest(signature, self.sign(envelope)):
            raise WebhookError("webhook signature is invalid")


def validate_webhook_target(
    url: str, allowed_hosts: frozenset[str]
) -> tuple[str, int, tuple[str, ...]]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise WebhookError("webhook URL must be an authenticated-free HTTPS URL")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname not in allowed_hosts:
        raise WebhookError("webhook host is not allowlisted")
    port = parsed.port or 443
    addresses = tuple(
        sorted(
            {
                str(address[4][0])
                for address in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
            }
        )
    )
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise WebhookError("webhook target resolves to a non-public address")
    if not addresses:
        raise WebhookError("webhook target did not resolve")
    return hostname, port, addresses
