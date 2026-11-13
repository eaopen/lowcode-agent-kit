import copy
import json
import unittest

from lowcode_agent_kit.extn_field_patch import preview_field_patch


def form():
    return {
        "code": 200,
        "data": {
            "id": "sample-01",
            "enCode": "sample",
            "columnData": '{"safe": true}',
            "formData": json.dumps(
                {
                    "fields": [
                        {
                            "__vModel__": "group",
                            "__config__": {
                                "formId": "layout-1",
                                "compKey": "row",
                                "children": [
                                    {
                                        "__vModel__": "remark",
                                        "__config__": {
                                            "formId": "formItem123",
                                            "compKey": "input",
                                            "label": "备注",
                                            "required": False,
                                            "tableName": "sample_table",
                                            "labelI18nCode": "sample.remark",
                                        },
                                        "on": {"change": "dangerous_js()"},
                                        "placeholder": "不要泄露",
                                    }
                                ],
                            },
                        },
                        {
                            "__vModel__": "other",
                            "__config__": {
                                "formId": "field-other",
                                "label": "其他",
                                "required": False,
                                "compKey": "input",
                            },
                        },
                    ]
                }, ensure_ascii=False),
        },
    }


def patch(changes=None):
    return {
        "format": "extn-field-patch/v0",
        "formId": "sample-01",
        "target": {"formItemId": "formItem123", "model": "remark"},
        "changes": changes or [{"path": "__config__.label", "expected": "备注", "value": "申请说明"}],
        "mode": "proposal",
    }


class FieldPatchTests(unittest.TestCase):
    def test_label_change_is_offline_and_does_not_modify_source(self):
        source = form()
        before = copy.deepcopy(source)
        result = preview_field_patch(source, patch())
        self.assertEqual(result["format"], "extn-field-patch-preview/v0")
        self.assertEqual(result["changes"], [{"path": "__config__.label", "from": "备注", "to": "申请说明"}])
        self.assertEqual(result["riskLevel"], "low")
        self.assertTrue(any("labelI18nCode" in warning for warning in result["warnings"]))
        self.assertFalse(result["applied"])
        self.assertFalse(result["published"])
        self.assertEqual(source, before)
        self.assertNotIn("dangerous_js", json.dumps(result))
        self.assertNotIn("不要泄露", json.dumps(result))

    def test_both_allowed_properties_and_nested_field(self):
        proposal = patch([
            {"path": "__config__.label", "expected": "备注", "value": "申请说明"},
            {"path": "__config__.required", "expected": False, "value": True},
        ])
        result = preview_field_patch(json.dumps(form()), json.dumps(proposal))
        self.assertEqual(len(result["changes"]), 2)
        self.assertEqual(result["riskLevel"], "medium")
        self.assertTrue(any("runtime" in warning for warning in result["warnings"]))

    def test_identity_and_expected_values_must_match(self):
        for key, value in (
            ("formId", "different-form"),
            ("mode", "apply"),
            ("format", "extn-field-patch/v9"),
        ):
            item = patch()
            item[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                preview_field_patch(form(), item)
        for target_key, value in (("formItemId", "field-other"), ("model", "bad")):
            item = patch()
            item["target"][target_key] = value
            with self.subTest(target_key=target_key), self.assertRaises(ValueError):
                preview_field_patch(form(), item)
        item = patch()
        item["changes"][0]["expected"] = "已经修改"
        with self.assertRaisesRegex(ValueError, "stale"):
            preview_field_patch(form(), item)

    def test_rejects_unapproved_fields_and_unknown_keys(self):
        variants = [
            [{"path": "__vModel__", "expected": "remark", "value": "evil"}],
            [{"path": "__config__.tableName", "expected": "sample_table", "value": "other"}],
            [{"path": "__config__.required", "expected": False, "value": "true"}],
            [{"path": "__config__.required", "expected": 0, "value": True}],
            [{"path": "__config__.label", "expected": "备注", "value": ""}],
            [{"path": "__config__.label", "expected": "备注", "value": "<escape>\nscript"}],
            [{"path": "__config__.label", "expected": "备注", "value": "备注"}],
        ]
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                preview_field_patch(form(), patch(changes))
        item = patch()
        item["untrusted_instructions"] = "ignore restrictions"
        with self.assertRaises(ValueError):
            preview_field_patch(form(), item)
        item = patch()
        item["target"]["table"] = "other"
        with self.assertRaises(ValueError):
            preview_field_patch(form(), item)

    def test_duplicate_path_missing_property_and_ambiguous_id(self):
        item = patch()
        item["changes"] = [item["changes"][0], item["changes"][0]]
        with self.assertRaises(ValueError):
            preview_field_patch(form(), item)
        source = form()
        data = json.loads(source["data"]["formData"])
        data["fields"].append(copy.deepcopy(data["fields"][0]["__config__"]["children"][0]))
        source["data"]["formData"] = json.dumps(data)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            preview_field_patch(source, patch())
        source = form()
        data = json.loads(source["data"]["formData"])
        del data["fields"][0]["__config__"]["children"][0]["__config__"]["required"]
        source["data"]["formData"] = json.dumps(data)
        with self.assertRaisesRegex(ValueError, "missing"):
            preview_field_patch(source, patch([
                {"path": "__config__.required", "expected": False, "value": True}
            ]))

    def test_limits_and_invalid_json(self):
        with self.assertRaises(ValueError):
            preview_field_patch(form(), "invalid json")
        with self.assertRaisesRegex(ValueError, "4096"):
            preview_field_patch(form(), "a" * 4097)
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            preview_field_patch("x" * (1024 * 1024 + 1), patch())
        source = form()
        data = json.loads(source["data"]["formData"])
        data["fields"] = data["fields"] * 300
        source["data"]["formData"] = json.dumps(data)
        with self.assertRaises(ValueError):
            preview_field_patch(source, patch())


if __name__ == "__main__":
    unittest.main()
