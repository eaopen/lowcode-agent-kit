"""Exercise a real MCP stdio handshake without any platform credentials."""
import os
import sys
import unittest

from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class StdioMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_handshake_and_readonly_tools(self):
        env = dict(os.environ)
        env.pop("LOWCODE_API_BASE_URL", None)
        env.pop("LOWCODE_TOKEN", None)
        env["LOWCODE_PLATFORM"] = "eap-obpm"
        process = StdioServerParameters(
            command=sys.executable,
            args=["-m", "lowcode_agent_kit.mcp_server"],
            env=env,
        )
        async with stdio_client(process) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {x.name for x in tools.tools}
                self.assertEqual(names, {"platform_discover", "platform_inspect", "preview_change"})
                response = await session.call_tool("platform_discover", {})
                self.assertFalse(response.is_error)
                self.assertIn("eap-obpm", str(response.structured_content or response.content))
                response = await session.call_tool(
                    "preview_change",
                    {"before_json": '{"label":"旧"}', "after_json": '{"label":"新"}'},
                )
                self.assertFalse(response.is_error)
                self.assertIn("offline-preview-only", str(response.structured_content or response.content))


    async def test_extn_offline_context_tool_through_stdio(self):
        env = dict(os.environ)
        env.pop("LOWCODE_API_BASE_URL", None)
        env.pop("LOWCODE_TOKEN", None)
        env["LOWCODE_PLATFORM"] = "extn"
        process = StdioServerParameters(
            command=sys.executable,
            args=["-m", "lowcode_agent_kit.mcp_server"],
            env=env,
        )
        payload = {
            "formData": '{"fields":[{"__vModel__":"name","__config__":{"compKey":"input","label":"姓名"}}]}',
        }
        import json

        async with stdio_client(process) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                self.assertIn("extn_analyze_definition", names)
                result = await session.call_tool(
                    "extn_analyze_definition",
                    {"form_definition_json": json.dumps(payload)},
                )
                self.assertFalse(result.is_error)
                body = result.structured_content or result.content
                self.assertIn("extn-visualdev-context/v1", str(body))
                self.assertIn("componentCount", str(body))
                self.assertIn("extn_preview_definition_change", names)
                planned = await session.call_tool(
                    "extn_preview_definition_change",
                    {
                        "before_definition_json": json.dumps(payload),
                        "after_definition_json": json.dumps(payload),
                    },
                )
                self.assertFalse(planned.is_error)
                self.assertIn("extn-form-change-preview/v1", str(planned.structured_content or planned.content))
                self.assertIn("extn_preview_field_patch", names)
                safe_form = {
                    "id": "demo-form-01",
                    "formData": json.dumps({
                        "fields": [{"__vModel__": "name", "__config__": {
                            "formId": "field1", "label": "旧名称", "required": False,
                        }}],
                    }),
                }
                patch = {
                    "format": "extn-field-patch/v0", "formId": "demo-form-01",
                    "target": {"formItemId": "field1", "model": "name"},
                    "changes": [{"path": "__config__.label", "expected": "旧名称", "value": "新名称"}],
                    "mode": "proposal",
                }
                preview = await session.call_tool(
                    "extn_preview_field_patch",
                    {"form_definition_json": json.dumps(safe_form), "patch_json": json.dumps(patch)},
                )
                self.assertFalse(preview.is_error)
                self.assertIn("extn-field-patch-preview/v0", str(preview.structured_content or preview.content))
                invalid_patch = {**patch, "mode": "apply"}
                denied_patch = await session.call_tool(
                    "extn_preview_field_patch",
                    {"form_definition_json": json.dumps(safe_form), "patch_json": json.dumps(invalid_patch)},
                )
                self.assertTrue(denied_patch.is_error)
                # A tool cannot connect to the platform merely because the
                # offline analyzer was used without credentials.
                denied = await session.call_tool(
                    "platform_inspect",
                    {"capability": "form.context", "identifier": "abc"},
                )
                self.assertTrue(denied.is_error)


if __name__ == "__main__":
    unittest.main()
