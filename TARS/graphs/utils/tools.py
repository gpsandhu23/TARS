import asyncio

# Use server from examples/servers/streamable-http-stateless/
from langchain_mcp_adapters.client import MultiServerMCPClient

async def _get_tools():
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "streamable_http",
                "url": "http://host.docker.internal:8000/mcp",
            },
        }
    )
    return await client.get_tools()

# Initialize tools synchronously
tools = asyncio.run(_get_tools())


