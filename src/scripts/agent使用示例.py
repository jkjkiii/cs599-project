from langchain.agents import AgentState, create_agent
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.tools import tool
from langchain.agents.middleware import (
    before_agent,
    after_agent,
    before_model,
    after_model,
    wrap_model_call,
    wrap_tool_call
)
# ===================== 1. 工具定义（你的代码不变） =====================
@tool(description="获取指定地点的天气信息")
def get_weather(location) -> str:
    return f"{location}明天天气晴朗，气温在15到25摄氏度之间。"

@tool(description="获取指定地点的空气质量信息")
def get_air_quality(location) -> str:
    return f"{location}明天空气质量优，PM2.5指数30。"

# ===================== 2. 节点式钩子（before/after，和你截图一致） =====================
@before_agent
def log_before_agent(state: AgentState, runtime) -> None:
    # agent执行前调用，传入state和runtime
    print(f"[before agent]agent启动，附带{len(state['messages'])}条消息")

@after_agent
def log_after_agent(state: AgentState, runtime) -> None:
    # agent执行结束后调用，传入state和runtime
    print(f"[after agent]agent执行结束，最终附带{len(state['messages'])}条消息")

@before_model
def log_before_model(state: AgentState, runtime) -> None:
    # 每次调用大模型前调用
    print(f"[before model]准备调用大模型，当前消息数：{len(state['messages'])}")

@after_model
def log_after_model(state: AgentState, runtime) -> None:
    # 大模型返回结果后调用
    print(f"[after model]大模型响应完成，当前消息数：{len(state['messages'])}")

# ===================== 3. 包裹式钩子（wrap_*，和你给的@wrap_tool_call示例格式一致） =====================
@wrap_model_call
def model_call_hook(request, handler):
    # 包裹大模型调用，必须调用handler(request)并返回结果
    print(f"[wrap model call]模型调用请求：{request}")
    result = handler(request)
    print(f"[wrap model call]模型调用结果：{result}")
    return result

@wrap_tool_call
def monitor_tool(request, handler):
    # 包裹工具调用，和你截图里的示例完全一样
    print(f"工具执行：{request.tool_call['name']}")
    print(f"工具执行传入参数：{request.tool_call['args']}")
    return handler(request)

# ===================== 4. 创建Agent（和你截图的middleware写法一致） =====================
agent = create_agent(
    model=ChatTongyi(model="qwen3-max"),
    tools=[get_weather, get_air_quality],
    # 直接把所有装饰器标记的函数加到middleware列表里
    middleware=[
        log_before_agent,
        log_after_agent,
        log_before_model,
        log_after_model,
        model_call_hook,
        monitor_tool
    ],
    system_prompt="你是严格遵循ReAct框架的智能助手，必须按照[思考-》行动-》观察]的流程解决问题，且每轮思考只能调用一个工具，禁止同时调用多个工具。并告知我你的思考过程，工具的调用原因，按思考-》行动-》观察的格式输出。"
)

# ===================== 5. 你的流式输出代码（不变） =====================
for chunk in agent.stream(
    {
        "messages": [
            {"role": "user", "content": "明天江西天气和空气质量如何？"}
        ]
    },
    stream_mode="values"
):
    latest_message = chunk['messages'][-1]
    if latest_message.content:
        print(type(latest_message).__name__, latest_message.content)
    try:
        if latest_message.tool_calls:
            print(f"工具调用: {[tc['name'] for tc in latest_message.tool_calls]}，参数: {[tc['args'] for tc in latest_message.tool_calls]}")
    except AttributeError:
        pass