# EXTN single-field Patch proposal — v0

> **POC only.** The `extn_preview_field_patch` MCP tool validates supplied EXTN form data **offline**. It does **not** generate changes using an LLM, modify the form, call an EXTN server, save data, or publish an application.

## Contract shared with FormGenerator

```json
{
  "format": "extn-field-patch/v0",
  "formId": "demo-form-id",
  "target": { "formItemId": "formItem123", "model": "remark" },
  "changes": [
    {
      "path": "__config__.label",
      "expected": "备注",
      "value": "申请说明"
    }
  ],
  "mode": "proposal"
}
```

A proposal may contain **one or two distinct** changes, limited to `__config__.label` (non-empty string, max 100 characters) and `__config__.required` (boolean). The `formId` must match the existing VisualDev form ID, and `formItemId` and `model` must uniquely identify the same field. The `expected` value must exactly match the current configuration; **no-op** edits, unknown properties, arbitrary JSON paths, scripts, field IDs, data table or workflow changes are rejected. A field missing the expected property is refused instead of silently adding it.

Pass the **exact original EXTN form detail** as JSON (the REST API wrapper, its `data` object, or a compatible JSON object with `id` and `formData.fields`). It can contain nested EXTN fields. Do not send production business data or secrets to external AI models; this tool is local to the provided process.

## Preview and integration

Run `LOWCODE_PLATFORM=extn uv run lowcode-mcp`. Call `extn_preview_field_patch(form_definition_json, patch_json)`. It returns `extn-field-patch-preview/v0` with target identifiers, the requested before/after values, risk level and warnings, with `applied: false` and `published: false`. It **never** returns original script bodies, complete form configuration or data rows.

The companion EXTN frontend PR imports the **same v0 JSON proposal**, revalidates against the **currently selected field** in FormGenerator and shows a user-reviewable diff. The reviewer may then accept the local change into the **existing editor undo history**. This UI implementation is independently validated against the same contract; there is no runtime Python/JS dependency.

**Important:** A valid offline proposal does not prove that server permissions, tenant, current revision, database schema, model-generated advice, translations or runtime rules are correct. The initial frontend POC **does not save** via `PUT /api/visualdev/Base/{id}` or call a release endpoint. A later authenticated DEV test must use the normal EXTN designer save/release permissions and verify runtime behavior separately.

## Safety limitations

- Exact schema, allowlisted paths and types, max 4 KiB patch, max 1 MiB definition, at most 500 fields and 14 nesting levels.
- Duplicate `formItemId`, mismatched field model, stale `expected`, and unrecognized forms are rejected.
- `labelI18nCode` takes precedence over raw `label` for translated display; the preview warns, it does not rewrite translations.
- `required` can be influenced by runtime scripts and conditional validation; manual preview is mandatory.
- This is not a general JSON Patch interpreter; it does not execute scripts or perform server authorization, apply, rollback or migration.
