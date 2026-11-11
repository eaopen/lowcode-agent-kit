"""EXTN form definition → bounded AI-friendly context (never executable code).

The native VisualDev formData, columnData and tables may be JSON-encoded strings.
This inspector works on *copies* and returns field/dependency summaries only.
It intentionally omits JS event handlers, rich content, generated code and data rows.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

MAX_INPUT_BYTES = 1024 * 1024
MAX_FIELDS = 500
MAX_DEPTH = 14
MAX_TEXT = 220


def _load(value: Any, title: str) -> Any:
    if not isinstance(value, str):
        return value
    if len(value.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError(f"{title} exceeds 1 MiB")
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"{title} is not valid JSON") from exc


def _short(value: Any) -> str:
    return value[:MAX_TEXT] if isinstance(value, str) else ""


def _extract_root(payload: Any) -> dict[str, Any]:
    payload = _load(payload, "definition")
    if not isinstance(payload, dict):
        raise ValueError("EXTN form definition must be a JSON object")
    if "code" in payload and "data" in payload:
        if str(payload["code"]) not in ("200", "0"):
            raise ValueError("EXTN API did not return a successful form definition")
        payload = payload["data"]
    if not isinstance(payload, dict):
        raise ValueError("EXTN form response has no object data")
    return payload


def analyze_form_definition(payload: Any) -> dict[str, Any]:
    """Summarize EXTN VisualDevInfoVO or an EXTN API response envelope.

    No API, DB or filesystem accesses; no form mutation or script evaluation.
    """
    definition = _extract_root(payload)
    form = _load(definition.get("formData"), "formData") or {}
    if not isinstance(form, dict):
        raise ValueError("formData must be an object")
    fields = form.get("fields", [])
    if not isinstance(fields, list):
        raise ValueError("formData.fields must be a list")

    tables_data = _load(definition.get("tables"), "tables")
    warnings: list[str] = []
    if tables_data is not None and not isinstance(tables_data, (dict, list)):
        warnings.append("tables has an unsupported shape; table dependencies omitted")
        tables_data = None

    result_fields: list[dict[str, Any]] = []
    dependencies: dict[str, set[str]] = {
        "dictionaryTypeIds": set(),
        "tableNames": set(),
    }
    _seen_nodes: set[int] = set()

    def walk(nodes: list[Any], path: str, depth: int, table: str = "") -> None:
        if depth > MAX_DEPTH:
            raise ValueError("form nesting depth exceeds limit")
        for index, node in enumerate(nodes):
            if len(result_fields) >= MAX_FIELDS:
                raise ValueError("form contains too many field components")
            if not isinstance(node, dict):
                warnings.append("non-object form component skipped")
                continue
            if id(node) in _seen_nodes:
                continue
            _seen_nodes.add(id(node))
            config = node.get("__config__")
            config = config if isinstance(config, dict) else {}
            place = f"{path}[{index}]"
            component = _short(config.get("compKey"))
            field_key = _short(node.get("__vModel__"))
            label = _short(config.get("label"))
            current_table = _short(config.get("tableName")) or table
            dictionary_type = _short(config.get("dictionaryType"))
            if dictionary_type:
                dependencies["dictionaryTypeIds"].add(dictionary_type)
            if current_table:
                dependencies["tableNames"].add(current_table)
            result_fields.append(
                {
                    "path": place,
                    "component": component,
                    "model": field_key,
                    "label": label,
                    "required": config.get("required") is True,
                    "table": current_table or None,
                    "dataSource": _short(config.get("dataType")) or None,
                    "dictionaryType": dictionary_type or None,
                    "hasExplicitLabelI18n": bool(config.get("labelI18nCode")),
                }
            )
            for location, children in (
                ("__config__.children", config.get("children")),
                ("children", node.get("children")),
            ):
                if isinstance(children, list):
                    walk(children, f"{place}.{location}", depth + 1, current_table)

    walk(fields, "fields", 0)

    duplicates = Counter(
        (field["table"], field["model"])
        for field in result_fields
        if field["model"]
    )
    duplicate_models = sorted(
        [
            {"table": table, "model": model}
            for (table, model), count in duplicates.items()
            if count > 1
        ],
        key=lambda value: (value["table"] or "", value["model"]),
    )

    if not fields:
        warnings.append("form has no design fields; may be a system form or incomplete draft")

    if duplicate_models:
        warnings.append("duplicate field model keys exist; review table scope before editing")

    if isinstance(tables_data, list):
        for table in tables_data:
            if isinstance(table, dict):
                for key in ("table", "tableName", "name"):
                    value = _short(table.get(key))
                    if value:
                        dependencies["tableNames"].add(value)
                        break

    return {
        "format": "extn-visualdev-context/v1",
        "identity": {
            "id": _short(definition.get("id")) or None,
            "code": _short(definition.get("enCode")) or None,
            "name": _short(definition.get("fullName")) or None,
            "type": definition.get("type"),
            "state": definition.get("state"),
        },
        "source": "read-only VisualDev definition",
        "summary": {
            "componentCount": len(result_fields),
            "requiredCount": sum(field["required"] for field in result_fields),
            "hasColumnDesign": bool(definition.get("columnData")),
            "hasWorkflow": definition.get("enableFlow") == 1,
            "hasCustomDataInterface": bool(definition.get("interfaceId")),
        },
        "dependencies": {
            "dictionaryTypeIds": sorted(dependencies["dictionaryTypeIds"]),
            "tableNames": sorted(dependencies["tableNames"]),
            "dbLinkId": _short(definition.get("dbLinkId")) or None,
            "dataInterfaceId": _short(definition.get("interfaceId")) or None,
        },
        "fields": result_fields,
        "duplicateModels": duplicate_models,
        "warnings": warnings,
        "omitted": ["event scripts", "rich content", "form-data rows", "SQL", "credentials"],
        "applied": False,
    }



def compare_form_definitions(before_payload: Any, after_payload: Any) -> dict[str, Any]:
    """Offline EXTN-aware field/dependency change plan; *never* writes state.

    Field identity is table+model (not label/index), so reordering and UI
    layout changes do not masquerade as destructive data-column changes.
    Duplicate field keys make that mapping ambiguous and are rejected.
    """
    before = analyze_form_definition(before_payload)
    after = analyze_form_definition(after_payload)
    a_code = before["identity"]["code"]
    b_code = after["identity"]["code"]
    if a_code and b_code and a_code != b_code:
        raise ValueError("cannot compare different form codes")
    if before["duplicateModels"] or after["duplicateModels"]:
        raise ValueError("ambiguous duplicate field models; inspect the original form first")

    def indexed(context: dict) -> dict[tuple[str, str], dict]:
        return {
            (str(field["table"] or ""), field["model"]): field
            for field in context["fields"]
            if field["model"]
        }

    first = indexed(before)
    second = indexed(after)
    old_keys = set(first)
    new_keys = set(second)
    removed = [
        {"table": table or None, "model": model, "component": first[table, model]["component"]}
        for table, model in sorted(old_keys - new_keys)
    ]
    added = [second[key] for key in sorted(new_keys - old_keys)]
    critical_properties = {"component", "dataSource", "dictionaryType"}
    properties = ("component", "label", "required", "dataSource", "dictionaryType", "hasExplicitLabelI18n")
    modified = []
    for key in sorted(old_keys & new_keys):
        changes = {
            name: {"from": first[key][name], "to": second[key][name]}
            for name in properties
            if first[key][name] != second[key][name]
        }
        if changes:
            modified.append({"table": key[0] or None, "model": key[1], "changes": changes})

    dependency_changes = {}
    for name in ("dictionaryTypeIds", "tableNames", "dbLinkId", "dataInterfaceId"):
        old_value = before["dependencies"][name]
        new_value = after["dependencies"][name]
        if old_value != new_value:
            dependency_changes[name] = {"from": old_value, "to": new_value}
    if before["summary"]["hasWorkflow"] != after["summary"]["hasWorkflow"]:
        dependency_changes["hasWorkflow"] = {
            "from": before["summary"]["hasWorkflow"],
            "to": after["summary"]["hasWorkflow"],
        }

    high = bool(removed or dependency_changes) or any(
        critical_properties.intersection(field["changes"])
        for field in modified
    )
    medium = bool(added) or any(
        "required" in field["changes"] for field in modified
    )
    risk_level = "high" if high else "medium" if medium else "low"
    changed = bool(removed or added or modified or dependency_changes)
    return {
        "format": "extn-form-change-preview/v1",
        "formCode": a_code or b_code,
        "mode": "offline-preview-only",
        "changed": changed,
        "riskLevel": risk_level if changed else "none",
        "fieldsAdded": added,
        "fieldsRemoved": removed,
        "fieldsModified": modified,
        "dependencyChanges": dependency_changes,
        "warnings": sorted(set(before["warnings"] + after["warnings"])),
        "requiresReview": changed,
        "applied": False,
        "note": "High risk means manual impact review, not automatic rejection; no deployment or data migration performed.",
    }
