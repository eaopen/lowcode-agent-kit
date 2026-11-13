"""Strict, offline-only preview of an EXTN FormGenerator single-field patch.

This module never writes to EXTN. All input is untrusted JSON; scripts and
business records remain in the supplied payload and are never evaluated or
returned in the preview.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from .extn_context import MAX_DEPTH, MAX_FIELDS, MAX_INPUT_BYTES, _extract_root, _load

PATCH_FORMAT = "extn-field-patch/v0"
PREVIEW_FORMAT = "extn-field-patch-preview/v0"
MAX_PATCH_BYTES = 4096
MAX_LABEL_LENGTH = 100
PATHS = {"__config__.label", "__config__.required"}


def _object(value: Any, what: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{what} must contain exactly: {', '.join(sorted(keys))}")
    return value


def _nonempty_text(value: Any, what: str, limit: int = 128) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{what} must be nonempty text up to {limit} characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{what} must not contain control characters")
    return value


def _parse_patch(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_PATCH_BYTES:
            raise ValueError("patch exceeds 4096 bytes")
        try:
            value = json.loads(value)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("patch is not valid JSON") from exc
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > MAX_PATCH_BYTES:
        raise ValueError("patch exceeds 4096 bytes")
    patch = _object(value, "patch", {"format", "formId", "target", "changes", "mode"})
    if patch["format"] != PATCH_FORMAT or patch["mode"] != "proposal":
        raise ValueError("unsupported patch format or mode")
    _nonempty_text(patch["formId"], "formId")
    target = _object(patch["target"], "target", {"formItemId", "model"})
    _nonempty_text(target["formItemId"], "target.formItemId")
    _nonempty_text(target["model"], "target.model")
    changes = patch["changes"]
    if not isinstance(changes, list) or not (1 <= len(changes) <= 2):
        raise ValueError("changes must contain one or two allowed field edits")
    seen: set[str] = set()
    for change in changes:
        change = _object(change, "change", {"path", "expected", "value"})
        path = change["path"]
        if path not in PATHS or path in seen:
            raise ValueError("duplicate or forbidden patch path")
        seen.add(path)
        before, after = change["expected"], change["value"]
        if path == "__config__.required":
            if type(before) is not bool or type(after) is not bool:
                raise ValueError("required must be boolean")
        else:
            if not isinstance(before, str) or not isinstance(after, str):
                raise ValueError("label must be text")
            _nonempty_text(after, "label", MAX_LABEL_LENGTH)
            if len(before) > MAX_LABEL_LENGTH:
                raise ValueError("expected label exceeds limit")
        if before == after:
            raise ValueError("patch contains a no-op edit")
    return patch


def _select_field(fields: list[Any], form_item_id: str, model: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    visited = 0

    def visit(nodes: Any, depth: int) -> None:
        nonlocal visited
        if depth > MAX_DEPTH:
            raise ValueError("form nesting depth exceeds limit")
        if not isinstance(nodes, list):
            raise ValueError("form fields must be a list")
        for node in nodes:
            visited += 1
            if visited > MAX_FIELDS:
                raise ValueError("too many field components")
            if not isinstance(node, dict):
                raise ValueError("invalid field component")
            config = node.get("__config__")
            if not isinstance(config, dict):
                raise ValueError("field config must be an object")
            if config.get("formId") == form_item_id:
                matches.append(node)
            for children in (config.get("children"), node.get("children")):
                if children is not None:
                    visit(children, depth + 1)

    visit(fields, 0)
    if len(matches) != 1:
        raise ValueError("field formItemId is missing or ambiguous")
    field = matches[0]
    if field.get("__vModel__") != model:
        raise ValueError("target model does not match selected field")
    return field


def preview_field_patch(form_definition: Any, proposal: Any) -> dict[str, Any]:
    """Validate a v0 field patch on a *copy* of a native EXTN form definition.

    A successful preview means the requested edit is well-formed and matches
    supplied form data, NOT that any current server revision is unchanged.
    """
    if isinstance(form_definition, str) and len(form_definition.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("form definition exceeds 1 MiB")
    patch = _parse_patch(proposal)
    definition = _extract_root(form_definition)
    if definition.get("id") != patch["formId"]:
        raise ValueError("formId does not match EXTN definition")
    form = _load(definition.get("formData"), "formData")
    if not isinstance(form, dict) or not isinstance(form.get("fields"), list):
        raise ValueError("EXTN formData.fields must be a list")
    # No changes to the original source even when supplied as a dict.
    draft_fields = copy.deepcopy(form["fields"])
    target = patch["target"]
    node = _select_field(draft_fields, target["formItemId"], target["model"])
    config = node["__config__"]
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    for item in patch["changes"]:
        path = item["path"]
        name = path.removeprefix("__config__.")
        if name not in config:
            raise ValueError(f"field property is missing: {path}")
        current = config[name]
        expected = item["expected"]
        if type(current) is not type(expected) or current != expected:
            raise ValueError(f"stale expected value for {path}")
        config[name] = item["value"]
        normalized.append({"path": path, "from": expected, "to": item["value"]})
        if name == "label" and config.get("labelI18nCode"):
            warnings.append("labelI18nCode overrides the visible label in translated locales")
        if name == "required":
            warnings.append("required may also be controlled by existing runtime rules; verify in Form Preview")
    return {
        "format": PREVIEW_FORMAT,
        "formId": patch["formId"],
        "target": copy.deepcopy(target),
        "changes": normalized,
        "riskLevel": "medium" if any(x["path"] == "__config__.required" for x in normalized) else "low",
        "warnings": warnings,
        "source": "supplied formData only; no live revision verification",
        "applied": False,
        "published": False,
    }
