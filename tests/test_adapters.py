import unittest

from lowcode_agent_kit.adapters import (
    CloudFileAdapter,
    EapObpmAdapter,
    ExtnAdapter,
    UnsupportedCapability,
    create_adapter,
)
from lowcode_agent_kit.config import Config
from lowcode_agent_kit.service import LowcodeService


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, params=None, body=None):
        self.calls.append((method, path, params, body))
        return {"ok": True, "path": path}


class AdapterTests(unittest.TestCase):
    def test_platforms_only_not_customer_overlays(self):
        self.assertEqual(EapObpmAdapter.platform, "eap-obpm")
        self.assertEqual(ExtnAdapter.platform, "extn")
        self.assertEqual(CloudFileAdapter.platform, "cloudfile")
        with self.assertRaises(ValueError):
            create_adapter("unsupported-business-app")
        with self.assertRaises(ValueError):
            create_adapter("jeecg")

    def test_eap_form_and_workflow_nodes(self):
        r = FakeTransport()
        service = LowcodeService(Config(platform="eap-obpm"), r)
        service.inspect("form.inspect", "purchase_FormV2")
        service.inspect("workflow.nodes", "purchase_flow")
        self.assertEqual(r.calls, [
            ("GET", "/form/formDef/getObject", {"key": "purchase_FormV2"}, None),
            ("POST", "/bpm/definition/getAllUserTaskNode", None, {"defKey": "purchase_flow"}),
        ])
        self.assertFalse(service.discover()["runtimeCapabilitiesVerified"])

    def test_extn_endpoints(self):
        r = FakeTransport()
        service = LowcodeService(Config(platform="extn"), r)
        service.inspect("form.inspect", "id-123")
        service.inspect("workflow.inspect", "flow-7")
        service.inspect("dictionary.inspect", "lookup")
        self.assertEqual(
            [c[1] for c in r.calls],
            ["/api/visualdev/Base/id-123",
             "/api/workflow/template/flow-7",
             "/api/system/DictionaryData/lookup/Data/Selector"],
        )

    def test_cloudfile_is_not_lowcode_engine(self):
        r = FakeTransport()
        service = LowcodeService(Config(platform="cloudfile"), r)
        service.inspect("files.features")
        service.inspect("files.libraries")
        self.assertEqual(r.calls[0][1], "/api/v2.1/cloudfile/features/")
        self.assertEqual(r.calls[1][1], "/api2/repos/")
        self.assertNotIn("form.inspect", service.discover()["capabilities"])

    def test_strict_identifiers_and_no_write_api(self):
        for adapter in (EapObpmAdapter(), ExtnAdapter(), CloudFileAdapter()):
            with self.assertRaises(ValueError):
                adapter.resolve(next(iter(adapter.capabilities)), "../admin")
            with self.assertRaises(UnsupportedCapability):
                adapter.resolve("change.apply", "test")
        with self.assertRaises(ValueError):
            CloudFileAdapter().resolve("files.library.inspect", "not-uuid")

    def test_mcp_discover_does_not_require_credentials(self):
        d = LowcodeService(Config(platform="extn")).discover()
        self.assertFalse(d["connected"])
        self.assertFalse(d["writesEnabled"])


if __name__ == "__main__":
    unittest.main()
