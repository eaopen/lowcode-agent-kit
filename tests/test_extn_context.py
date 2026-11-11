import json
import unittest

from lowcode_agent_kit.adapters import ExtnAdapter
from lowcode_agent_kit.config import Config
from lowcode_agent_kit.extn_context import analyze_form_definition, compare_form_definitions
from lowcode_agent_kit.service import LowcodeService


def sample_form():
    # Invented test values; never use a real user's or tenant's form.
    return {
        "code": 200,
        "data": {
            "id": "demo-form-01",
            "enCode": "purchase_request",
            "fullName": "示例申请表",
            "type": 1,
            "state": 1,
            "enableFlow": 1,
            "dbLinkId": "db-01",
            "interfaceId": "dataset-02",
            "columnData": json.dumps({"columns": [{"key": "name"}]}),
            "tables": json.dumps([{"table": "sample_request"}, {"table": "sample_detail"}]),
            "formData": json.dumps({
                "fields": [
                    {
                        "__vModel__": "requester",
                        "__config__": {
                            "compKey": "input",
                            "label": "申请人",
                            "required": True,
                            "tableName": "sample_request",
                            "labelI18nCode": "demo.requester",
                        },
                        "placeholder": "请输入",
                        "on": {"change": "(event) => dangerousCall()"},
                    },
                    {
                        "__vModel__": "status",
                        "__config__": {
                            "compKey": "select",
                            "label": "状态",
                            "tableName": "sample_request",
                            "dataType": "dictionary",
                            "dictionaryType": "dict-123",
                        },
                    },
                    {
                        "__config__": {
                            "compKey": "row",
                            "label": "布局",
                            "children": [
                                {
                                    "__vModel__": "quantity",
                                    "__config__": {
                                        "compKey": "inputNumber",
                                        "label": "数量",
                                        "required": True,
                                        "tableName": "sample_detail",
                                    },
                                }
                            ],
                        }
                    },
                ]
            }, ensure_ascii=False),
        },
    }


class NativeResponse:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def request(self, method, path, *, params=None, body=None):
        self.calls.append((method, path, params, body))
        return self.value


class ExtnContextTests(unittest.TestCase):
    def test_inventory_and_dependencies(self):
        raw = sample_form()
        before = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        result = analyze_form_definition(raw)
        self.assertEqual(result["format"], "extn-visualdev-context/v1")
        self.assertEqual(result["identity"]["code"], "purchase_request")
        self.assertEqual(result["summary"]["componentCount"], 4)
        self.assertEqual(result["summary"]["requiredCount"], 2)
        self.assertTrue(result["summary"]["hasWorkflow"])
        self.assertEqual(result["dependencies"]["dictionaryTypeIds"], ["dict-123"])
        self.assertEqual(result["dependencies"]["tableNames"], ["sample_detail", "sample_request"])
        self.assertEqual(result["dependencies"]["dataInterfaceId"], "dataset-02")
        self.assertEqual(result["fields"][3]["path"], "fields[2].__config__.children[0]")
        self.assertEqual(result["fields"][0]["hasExplicitLabelI18n"], True)
        self.assertFalse(result["applied"])
        self.assertEqual(json.dumps(raw, ensure_ascii=False, sort_keys=True), before)
        self.assertNotIn("dangerousCall", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("请输入", json.dumps(result, ensure_ascii=False))

    def test_json_string_and_direct_form(self):
        raw = sample_form()
        self.assertEqual(analyze_form_definition(json.dumps(raw))["summary"]["componentCount"], 4)
        self.assertEqual(analyze_form_definition(raw["data"])["summary"]["componentCount"], 4)
        self.assertEqual(analyze_form_definition({"formData": {"fields": []}})["summary"]["componentCount"], 0)

    def test_duplicates_are_reported_in_same_table(self):
        raw = {"formData": {"fields": [
            {"__vModel__": "x", "__config__": {"compKey": "input", "tableName": "table-a"}},
            {"__vModel__": "x", "__config__": {"compKey": "select", "tableName": "table-a"}},
        ]}}
        result = analyze_form_definition(raw)
        self.assertEqual(result["duplicateModels"], [{"table": "table-a", "model": "x"}])
        self.assertTrue(result["warnings"])

    def test_malformed_or_oversized_json_fails_closed(self):
        for raw in (
            [],
            "{not-json",
            {"code": 403, "data": {}},
            {"formData": "{invalid"},
            {"formData": {"fields": 12}},
            "a" * (1024 * 1024),
        ):
            with self.subTest(raw=str(raw)[:38]), self.assertRaises(ValueError):
                analyze_form_definition(raw)

    def test_max_depth_and_component_count(self):
        node = {"__config__": {"compKey": "row"}}
        top = node
        for _ in range(18):
            child = {"__config__": {"compKey": "row"}}
            node["__config__"]["children"] = [child]
            node = child
        with self.assertRaisesRegex(ValueError, "depth"):
            analyze_form_definition({"formData": {"fields": [top]}})
        fields = [{"__config__": {"compKey": "input"}} for _ in range(501)]
        with self.assertRaisesRegex(ValueError, "too many"):
            analyze_form_definition({"formData": {"fields": fields}})

    def test_real_service_context_redacts_raw(self):
        reader = NativeResponse(sample_form())
        service = LowcodeService(Config(platform="extn"), reader)
        response = service.inspect("form.context", "demo-form-01")
        self.assertEqual(reader.calls[0][:2], ("GET", "/api/visualdev/Base/demo-form-01"))
        self.assertNotIn("raw", response)
        self.assertEqual(response["context"]["summary"]["componentCount"], 4)
        self.assertNotIn("dangerousCall", str(response))

    def test_semantic_change_ignores_layout_order(self):
        before = sample_form()
        after = json.loads(json.dumps(before))
        form = json.loads(after["data"]["formData"])
        form["fields"].reverse()
        after["data"]["formData"] = json.dumps(form)
        result = compare_form_definitions(before, after)
        self.assertFalse(result["changed"])
        self.assertFalse(result["applied"])
        self.assertEqual(result["riskLevel"], "none")

    def test_semantic_change_levels(self):
        before = sample_form()
        after = json.loads(json.dumps(before))
        form = json.loads(after["data"]["formData"])
        form["fields"][1]["__config__"]["required"] = True
        after["data"]["formData"] = json.dumps(form)
        delta = compare_form_definitions(before, after)
        self.assertEqual(delta["riskLevel"], "medium")
        self.assertIn("required", delta["fieldsModified"][0]["changes"])
        self.assertFalse(delta["applied"])

        form["fields"][1]["__config__"]["dictionaryType"] = "other-dict"
        after["data"]["formData"] = json.dumps(form)
        delta = compare_form_definitions(before, after)
        self.assertEqual(delta["riskLevel"], "high")
        self.assertIn("dictionaryTypeIds", delta["dependencyChanges"])

        form["fields"].pop(0)
        after["data"]["formData"] = json.dumps(form)
        delta = compare_form_definitions(before, after)
        self.assertEqual(delta["riskLevel"], "high")
        self.assertEqual(delta["fieldsRemoved"][0]["model"], "requester")

    def test_cannot_compare_different_form_codes_or_ambiguous_models(self):
        before = sample_form()
        after = json.loads(json.dumps(before))
        after["data"]["enCode"] = "unrelated_form"
        with self.assertRaisesRegex(ValueError, "different form codes"):
            compare_form_definitions(before, after)

        after["data"]["enCode"] = before["data"]["enCode"]
        form = json.loads(after["data"]["formData"])
        form["fields"].append(form["fields"][0])
        after["data"]["formData"] = json.dumps(form)
        with self.assertRaisesRegex(ValueError, "duplicate field models"):
            compare_form_definitions(before, after)

    def test_manifest_additional_read_routes(self):
        adapter = ExtnAdapter()
        cases = {
            "form.catalog": ("/api/visualdev/Base/list", {"currentPage": "1", "pageSize": "20"}),
            "workflow.catalog": ("/api/workflow/template", {"currentPage": "1", "pageSize": "20"}),
            "workflow.versions.inspect": ("/api/workflow/template/Version/def1", None),
            "workflow.definition.inspect": ("/api/workflow/template/Info/def1", None),
            "workflow.form.inspect": ("/api/workflow/template/def1/FormInfo", None),
        }
        for capability, (path, params) in cases.items():
            with self.subTest(capability=capability):
                call = adapter.resolve(capability, "" if capability.endswith(".catalog") else "def1")
                self.assertEqual(call.path, path)
                self.assertEqual(call.params, params)
        with self.assertRaises(ValueError):
            adapter.resolve("form.catalog", "ignored-id")


if __name__ == "__main__":
    unittest.main()
