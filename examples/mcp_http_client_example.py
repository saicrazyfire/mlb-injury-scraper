"""Example MCP client using HTTP/SSE transport."""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# For HTTP/SSE transport
import httpx
from mcp.client.sse import sse_client

async def test_mcp_http():
    """Test MCP server over HTTP/SSE transport."""
    print("🔗 Testing MCP server over HTTP/SSE transport...")
    
    async with httpx.AsyncClient() as client:
        async with sse_client("http://localhost:8000/sse") as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print(f"\n📋 Available tools: {len(tools.tools)}")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description}")
                
                # Test get_available_teams
                print("\n🏟️  Testing get_available_teams...")
                result = await session.call_tool("get_available_teams", {})
                print(f"   Result: {result.content[0].text[:200]}...")
                
                # Test get_team_injuries
                print("\n⚕️  Testing get_team_injuries for Mets...")
                result = await session.call_tool("get_team_injuries", {"team": "mets"})
                print(f"   Result: {result.content[0].text[:200]}...")

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_http())
        print("\n✅ MCP HTTP/SSE transport test successful!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

