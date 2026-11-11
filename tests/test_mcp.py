import unittest

from lowcode_agent_kit.config import Config
from lowcode_agent_kit.mcp_server import create_server
from lowcode_agent_kit.service import LowcodeService


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_tools(self):
        server = create_server(LowcodeService(Config(platform="eap-obpm")))
        registered = await server.list_tools()
        names = {x.name for x in registered}
        self.assertEqual(names, {"platform_discover", "platform_inspect", "preview_change"})


if __name__ == "__main__":
    unittest.main()
