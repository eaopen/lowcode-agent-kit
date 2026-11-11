"""Environment-only credentials. Never save credentials in Skills or Git."""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit

PLATFORMS = ("eap-obpm", "extn", "cloudfile")


@dataclass(frozen=True)
class Config:
    platform: str
    base_url: str = ""
    token: str = ""
    auth_header: str = "Authorization"
    auth_scheme: str = "bearer"
    profile: str = "local"
    declared_version: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            platform=os.environ.get("LOWCODE_PLATFORM", "").strip(),
            base_url=os.environ.get("LOWCODE_API_BASE_URL", "").strip(),
            token=os.environ.get("LOWCODE_TOKEN", "").strip(),
            auth_header=os.environ.get("LOWCODE_AUTH_HEADER", "Authorization").strip(),
            auth_scheme=os.environ.get(
                "LOWCODE_AUTH_SCHEME",
                "token" if os.environ.get("LOWCODE_PLATFORM", "").strip() == "cloudfile" else "bearer",
            ).strip(),
            profile=os.environ.get("LOWCODE_PROFILE", "local").strip(),
            declared_version=os.environ.get("LOWCODE_DECLARED_VERSION", "").strip(),
        )

    def validate(self, require_connection: bool = False) -> None:
        if self.platform not in PLATFORMS:
            raise ValueError("LOWCODE_PLATFORM must be eap-obpm, extn, or cloudfile")
        if self.auth_header not in {"Authorization", "X-Access-Token"}:
            raise ValueError("LOWCODE_AUTH_HEADER must be Authorization or X-Access-Token")
        if self.auth_scheme not in {"bearer", "raw", "token"}:
            raise ValueError("LOWCODE_AUTH_SCHEME must be bearer, token, or raw")
        if require_connection and (not self.base_url or not self.token):
            raise ValueError("set LOWCODE_API_BASE_URL and LOWCODE_TOKEN to connect; never paste secrets into prompts")
        if not self.base_url:
            return
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("LOWCODE_API_BASE_URL must be http(s) without embedded credentials, query or fragment")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            if os.environ.get("LOWCODE_ALLOW_INSECURE_HTTP") != "true":
                raise ValueError("remote HTTP is disabled; use HTTPS or explicitly allow trusted internal HTTP")

    def masked_info(self) -> dict:
        return {
            "profile": self.profile,
            "declaredVersion": self.declared_version or None,
            "connected": bool(self.base_url and self.token),
            "mode": "read-only",
        }
