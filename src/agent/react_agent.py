import os
import asyncio
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from model.factor import chat_model
from utils.prompt_loader import load_system_prompt
from utils.path_tool import get_project_root
from utils.logger_hander import logger
from agent.tools.agent_tools import (
    rag_summarize, get_user_id, get_current_month,
    fetch_external_data, fill_context_for_report,
)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch


class ReactAgent:
    def __init__(self):
        self.messages = []
        mcp_tools = asyncio.run(self._init_mcp_tools())

        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[
                rag_summarize,
                *mcp_tools,          # get_location, get_weather（MCP → 同步壳）
                get_user_id,
                get_current_month,
                fetch_external_data,
                fill_context_for_report,
            ],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    async def _init_mcp_tools(self):
        server_path = os.path.join(
            get_project_root(), "src", "mcp_server", "weather_server.py"
        )
        self.mcp_client = MultiServerMCPClient({
            "weather": {
                "command": "python",
                "args": [server_path],
                "env": {"AMAP_KEY": os.getenv("AMAP_KEY", "")},
                "transport": "stdio",
            }
        })
        async_tools = await self.mcp_client.get_tools()
        return [self._to_sync(t) for t in async_tools]

    @staticmethod
    def _to_sync(async_tool):
        """把 MCP 的异步工具包装成同步 @tool，兼容 LangGraph 同步调用"""
        @tool(description=async_tool.description or "")
        def wrapper(**kwargs):
            result = asyncio.run(async_tool.ainvoke(kwargs))
            logger.info(f"[MCP wrapper] {async_tool.name} 原始返回: {result}, type: {type(result)}")
            if isinstance(result, list) and result:
                item = result[0]
                if isinstance(item, dict):
                    return item.get("text", str(item))
                if hasattr(item, "text"):
                    return item.text
            return str(result)
        wrapper.name = async_tool.name
        return wrapper

    def execute_stream(self, query: str):
        self.messages.append({"role": "user", "content": query})

        last_chunk = None
        for chunk in self.agent.stream(
            {"messages": self.messages},
            stream_mode="values",
            context={"report": False},
        ):
            last_chunk = chunk
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

        if last_chunk:
            self.messages = last_chunk["messages"]

    def clear_history(self):
        self.messages = []


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("北京今天天气怎么样？"):
        print(chunk, end="", flush=True)
