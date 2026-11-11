"""Strict allow-list of existing platform *read-only* API operations.

We deliberately do not expose arbitrary HTTP, SQL or any business write API.
The adapter preserves native responses; no guessed universal form or BPM schema.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

IDENTIFIER = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")
UUID = re.compile(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$")


def valid_key(value: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError("invalid identifier: use a safe platform key or ID (1-128 chars)")
    return value


@dataclass(frozen=True)
class ReadCall:
    method: str
    path: str
    params: dict[str, str] | None = None
    body: dict[str, Any] | None = None


class UnsupportedCapability(ValueError):
    pass


class Adapter:
    platform: str
    engine: str
    capabilities: tuple[str, ...]

    def resolve(self, capability: str, identifier: str) -> ReadCall:
        raise NotImplementedError

    def discover(self) -> dict:
        return {
            "platform": self.platform,
            "engine": self.engine,
            "capabilities": {key: {"declared": True, "access": "read"} for key in self.capabilities},
            "versionStatus": "deployment-not-probed",
            "writesEnabled": False,
        }


class EapObpmAdapter(Adapter):
    platform = "eap-obpm"
    engine = "OpenBPM/Activiti"
    capabilities = ("model.inspect", "form.inspect", "workflow.inspect", "workflow.nodes")

    def resolve(self, capability: str, identifier: str) -> ReadCall:
        key = valid_key(identifier)
        # These routes are grounded in bpm-core REST controllers. Some legacy
        # paths accept POST even for reads; only this exact POST is allowlisted.
        calls = {
            "model.inspect": ReadCall("GET", "/bus/businessObject/getBoStruct", {"key": key}),
            "form.inspect": ReadCall("GET", "/form/formDef/getObject", {"key": key}),
            "workflow.inspect": ReadCall("GET", "/bpm/definition/get", {"id": key}),
            "workflow.nodes": ReadCall("POST", "/bpm/definition/getAllUserTaskNode", body={"defKey": key}),
        }
        try:
            return calls[capability]
        except KeyError:
            raise UnsupportedCapability(f"{capability} is not supported for {self.platform}") from None


class ExtnAdapter(Adapter):
    platform = "extn"
    engine = "EXTN/Flowable"
    capabilities = (
        "form.catalog",
        "form.inspect",
        "form.context",
        "model.inspect",
        "workflow.catalog",
        "workflow.inspect",
        "workflow.definition.inspect",
        "workflow.versions.inspect",
        "workflow.form.inspect",
        "dictionary.inspect",
    )

    def resolve(self, capability: str, identifier: str) -> ReadCall:
        # Catalog operations are read-only, bounded and accept no freeform query.
        if capability in ("form.catalog", "workflow.catalog"):
            if identifier:
                raise ValueError(f"{capability} does not take an identifier")
            return ReadCall(
                "GET",
                "/api/visualdev/Base/list" if capability == "form.catalog" else "/api/workflow/template",
                {"currentPage": "1", "pageSize": "20"},
            )
        path_id = quote(valid_key(identifier), safe="")
        calls = {
            "model.inspect": ReadCall("GET", f"/api/visualdev/Base/{path_id}/FormDataFields", {"filterType": "0"}),
            "form.inspect": ReadCall("GET", f"/api/visualdev/Base/{path_id}"),
            "form.context": ReadCall("GET", f"/api/visualdev/Base/{path_id}"),
            "workflow.inspect": ReadCall("GET", f"/api/workflow/template/{path_id}"),
            "workflow.definition.inspect": ReadCall("GET", f"/api/workflow/template/Info/{path_id}"),
            "workflow.versions.inspect": ReadCall("GET", f"/api/workflow/template/Version/{path_id}"),
            # This ID is a workflow VERSION ID, not a template ID.
            "workflow.form.inspect": ReadCall("GET", f"/api/workflow/template/{path_id}/FormInfo"),
            "dictionary.inspect": ReadCall("GET", f"/api/system/DictionaryData/{path_id}/Data/Selector"),
        }
        try:
            return calls[capability]
        except KeyError:
            raise UnsupportedCapability(f"{capability} is not supported for {self.platform}") from None


class CloudFileAdapter(Adapter):
    """File capability adapter; do not duplicate cloudfile-toolkit Skills/CLI."""

    platform = "cloudfile"
    engine = "CloudFile/Seafile CE"
    capabilities = ("files.features", "files.libraries", "files.library.inspect")

    def resolve(self, capability: str, identifier: str) -> ReadCall:
        if capability == "files.features":
            if identifier:
                raise ValueError("files.features requires no identifier")
            return ReadCall("GET", "/api/v2.1/cloudfile/features/")
        if capability == "files.libraries":
            if identifier:
                raise ValueError("files.libraries requires no identifier")
            return ReadCall("GET", "/api2/repos/")
        if capability == "files.library.inspect":
            if not UUID.fullmatch(identifier):
                raise ValueError("CloudFile repository ID must be a UUID")
            return ReadCall("GET", f"/api/v2.1/repos/{identifier}/")
        raise UnsupportedCapability(f"{capability} is not supported for {self.platform}")


ADAPTERS: dict[str, type[Adapter]] = {
    EapObpmAdapter.platform: EapObpmAdapter,
    ExtnAdapter.platform: ExtnAdapter,
    CloudFileAdapter.platform: CloudFileAdapter,
}


def create_adapter(platform: str) -> Adapter:
    try:
        return ADAPTERS[platform]()
    except KeyError:
        raise ValueError(f"unsupported platform: {platform}; expected one of {', '.join(ADAPTERS)}") from None
