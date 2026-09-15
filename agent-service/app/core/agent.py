from anthropic import AsyncAnthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.core.config import settings

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = (
    'You are an HR analytics assistant for a Ukrainian company. '
    'Use the available tools to answer questions about employees, departments, '
    'salaries, and vacations. Always inspect the database schema before writing SQL. '
    'Respond in the language the user asked in.'
)

async def ask_agent(question: str) -> str:
    async with streamable_http_client(settings.mcp_server_url) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            await mcp_client.initialize()
            tools_result = await mcp_client.list_tools()

            runner = client.beta.messages.tool_runner(
                model='claude-opus-5',
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{'role': 'user', 'content': question}],
                tools=[async_mcp_tool(t, mcp_client) for t in tools_result.tools]
            )

            final_text = ''
            async for message in runner:
                for block in message.content:
                    if block.type == 'text':
                        final_text = block.text
            return final_text