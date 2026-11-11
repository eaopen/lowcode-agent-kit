import os
import unittest
from unittest.mock import patch

from lowcode_agent_kit.config import Config
from lowcode_agent_kit.service import LowcodeService


class ConfigAndPlanTests(unittest.TestCase):
    def test_token_is_never_in_discover(self):
        config = Config(platform="eap-obpm", token="SUPER_SECRET", base_url="https://example.org")
        result = LowcodeService(config).discover()
        self.assertNotIn("SUPER_SECRET", str(result))

    def test_remote_plain_http_requires_explicit_optin(self):
        config = Config(platform="extn", base_url="http://intranet.test", token="x")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                config.validate()
        with patch.dict(os.environ, {"LOWCODE_ALLOW_INSECURE_HTTP": "true"}):
            config.validate()

    def test_base_url_cannot_have_embedded_credentials(self):
        with self.assertRaises(ValueError):
            Config(platform="cloudfile", base_url="https://user:pass@example.org").validate()

    def test_cloudfile_uses_native_token_header_default(self):
        with patch.dict(os.environ, {"LOWCODE_PLATFORM": "cloudfile"}, clear=True):
            config = Config.from_env()
        self.assertEqual(config.auth_scheme, "token")

    def test_preview_has_no_side_effects_and_hashes(self):
        before = {"label": "客户名称", "required": False}
        after = {"label": "客户名称", "required": True, "tip": "请填写"}
        result = LowcodeService.plan_change(before, after)
        self.assertFalse(result["applied"])
        self.assertEqual({x["field"] for x in result["changes"]}, {"required", "tip"})
        self.assertEqual(before, {"label": "客户名称", "required": False})
        self.assertEqual(len(result["beforeSha256"]), 64)

    def test_preview_rejects_non_objects_and_limits(self):
        with self.assertRaises(ValueError):
            LowcodeService.plan_change(["a"], ["b"])
        with self.assertRaises(ValueError):
            LowcodeService.plan_change({}, {"large": "a" * 200_000})

    def test_not_configured_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "LOWCODE_API_BASE_URL"):
            LowcodeService(Config(platform="extn")).inspect("form.inspect", "abc")


if __name__ == "__main__":
    unittest.main()
