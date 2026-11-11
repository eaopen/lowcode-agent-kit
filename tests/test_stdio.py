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


if __name__ == "__main__":
    unittest.main()
