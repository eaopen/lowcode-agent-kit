"""Stable agent-facing read surface and offline deterministic change preview."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from .adapters import Adapter, create_adapter
from .config import Config
from .transport import RestTransport

MAX_PLAN_BYTES = 120_000
MAX_PLAN_CHANGED_KEYS = 200


class Reader(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict | None = None,
    ) -> Any: ...


class LowcodeService:
    def __init__(self, config: Config, transport: Reader | None = None):
        config.validate()
        self.config = config
        self.adapter: Adapter = create_adapter(config.platform)
        self.transport = transport or RestTransport(config)

    def discover(self) -> dict:
        return {
            "protocol": "lowcode-agent-kit/v0",
            **self.config.masked_info(),
            **self.adapter.discover(),
            # Deployed capability may be absent even when current source supports it.
            "runtimeCapabilitiesVerified": False,
        }

    def inspect(self, capability: str, identifier: str = "") -> dict:
        call = self.adapter.resolve(capability, identifier)
        result = self.transport.request(call.method, call.path, params=call.params, body=call.body)
        return {
            "platform": self.adapter.platform,
            "capability": capability,
            "identifier": identifier,
            "source": "native REST",
            "raw": result,
        }

    @staticmethod
    def plan_change(before: Any, after: Any) -> dict:
        """Local plan only: no networking, persistence, dynamic code or apply."""
        a = json.dumps(before, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        b = json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(a.encode()) > MAX_PLAN_BYTES or len(b.encode()) > MAX_PLAN_BYTES:
            raise ValueError("input size limit exceeded")
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise ValueError("plan_change accepts two JSON objects")
        changes = []
        for name in sorted(set(before) | set(after)):
            if before.get(name) != after.get(name) or (name in before) != (name in after):
                changes.append({
                    "field": name,
                    "operation": ("added" if name not in before else "removed" if name not in after else "changed"),
                    "before": before.get(name),
                    "after": after.get(name),
                })
        if len(changes) > MAX_PLAN_CHANGED_KEYS:
            raise ValueError("too many changed top-level keys")
        return {
            "mode": "offline-preview-only",
            "changed": bool(changes),
            "beforeSha256": hashlib.sha256(a.encode()).hexdigest(),
            "afterSha256": hashlib.sha256(b.encode()).hexdigest(),
            "changes": changes,
            "applied": False,
            "safety": "A plan is not permission to write; obtain explicit approval and use the platform-native guarded workflow.",
        }
