"""Restricted REST transport. Paths come only from audited adapters."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .config import Config

MAX_RESPONSE_BYTES = 1024 * 1024


class PlatformReadError(Exception):
    """Credential-free, host-free remote error."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RestTransport:
    def __init__(self, config: Config):
        config.validate()
        self.config = config
        # Avoid implicit OS proxies passing private platform tokens to an
        # unintended gateway. Proxy support requires an explicit design later.
        self._opener = build_opener(NoRedirect(), ProxyHandler({}))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        self.config.validate(require_connection=True)
        if method not in {"GET", "POST"}:
            raise PlatformReadError("unsupported method")
        if not path.startswith("/") or ".." in path or "//" in path or "?" in path or "#" in path:
            raise PlatformReadError("invalid adapter path")
        # No arbitrary hosts, routes, SQL or user-provided HTTP methods.
        url = self.config.base_url.rstrip("/") + path
        if params:
            url += "?" + urlencode(params)
        headers = {"Accept": "application/json"}
        scheme = self.config.auth_scheme
        if scheme == "bearer":
            value = "Bearer " + self.config.token
        elif scheme == "token":
            value = "Token " + self.config.token
        else:
            value = self.config.token
        headers[self.config.auth_header] = value
        payload = None
        if method == "POST":
            payload = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=12) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise PlatformReadError("response exceeds the 1 MiB limit")
                try:
                    return json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise PlatformReadError("platform returned non-JSON data") from None
        except HTTPError as exc:
            raise PlatformReadError(f"platform read rejected: HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError):
            raise PlatformReadError("platform connection failed") from None
