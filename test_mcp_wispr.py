import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def test():
    try:
        print("Connecting to Wispr Flow MCP...")
        async with sse_client("https://api.wisprflow.ai/connect/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("Wispr Flow MCP Connected! Available Tools:", len(tools.tools))
                for t in tools.tools[:5]:
                    print(f" - {t.name}: {t.description[:60]}...")
    except Exception as e:
        print("MCP Connection Error:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test())
