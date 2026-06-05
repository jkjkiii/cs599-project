# Specs 规格文档

## 一、Product Spec（产品规格）

### 1.1 产品定位

智扫通是一款面向扫地/扫拖一体机器人用户的 **Agentic RAG 智能客服系统**，采用**多智能体协作架构**：主控 Agent（ReAct）负责对话编排与知识检索，气象 Agent（MCP）独立负责天气与定位服务，两者通过 MCP 协议协同工作，提供专业问答、环境分析和个性化使用报告服务。

### 1.2 目标用户

- 扫地/扫拖机器人潜在购买者（选购咨询）
- 已购用户（使用技巧、故障排查、维护保养）
- 产品运营方（用户使用数据分析与报告）

### 1.3 核心功能

| 编号 | 功能 | 描述 | 优先级 |
|------|------|------|--------|
| F1 | RAG 专业知识问答 | 基于向量知识库检索故障排除、选购指南、维护保养等内容，LLM 总结后回答 | P0 |
| F2 | 天气环境分析 | 获取用户所在城市天气，分析环境对机器人使用的影响并给出建议 | P1 |
| F3 | 个人使用报告生成 | 查询用户月度使用记录（清洁效率、耗材状态、对比数据），生成结构化报告 | P1 |
| F4 | IP 自动定位 | 自动获取用户城市，无需手动输入 | P2 |
| F5 | 流式对话交互 | Web 端实时流式输出，打字机效果 | P2 |

### 1.4 用户故事

| ID | 作为 | 我想要 | 以便 |
|----|------|--------|------|
| US1 | 用户 | 询问扫地机器人故障怎么处理 | 快速解决使用问题 |
| US2 | 用户 | 了解小户型适合什么机器人 | 做出正确的购买决策 |
| US3 | 用户 | 知道今天天气是否适合拖地 | 合理安排清洁计划 |
| US4 | 用户 | 查看本月机器人使用报告 | 了解清洁效率和耗材情况 |
| US5 | 用户 | 输入自然语言即可得到回答 | 无需学习复杂操作 |

### 1.5 能力边界

- 仅能回答知识库覆盖的扫地/扫拖机器人相关问题
- 超出知识库范围的问题，Agent 自行判断后回复"不知道"
- 用户使用数据为模拟数据（10 个用户，2025 年全年）
- 天气数据依赖高德 API 可用性

### 1.6 非功能需求

| 编号 | 类型 | 要求 | 指标 |
|------|------|------|------|
| NF1 | 性能 | 首次回答延迟 | < 10s |
| NF2 | 性能 | 流式首字延迟 | < 3s |
| NF3 | 可用性 | 系统正常运行时间 | 开发阶段 ≥ 95% |
| NF4 | 可维护性 | 配置热更新 | YAML 文件修改后重启生效 |
| NF5 | 安全性 | API Key 保护 | .env.example 本地化，不提交至仓库 |
| NF6 | 可观测性 | 关键路径日志 | Agent 每步推理、工具调用、模型请求均可追溯 |

---

## 二、Architecture Spec（架构规格）

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                      │
│              st.chat_input() / st.write_stream()         │
└────────────────────────┬────────────────────────────────┘
                         │ query
                         ▼
┌─────────────────────────────────────────────────────────┐
│              主控 Agent: ReactAgent (LangGraph)           │
│                                                         │
│   create_agent(model, tools, middleware, system_prompt)  │
│                                                         │
│   ┌──────────┐    ┌──────────────┐    ┌────────────┐   │
│   │  Think   │───▶│  Tool Call   │───▶│  Observe   │   │
│   └──────────┘    └──────────────┘    └────────────┘   │
│         ▲                                    │          │
│         └────────────────────────────────────┘          │
│                   (ReAct Loop, max 5 rounds)             │
└────────────────────────┬────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  工具层   │    │   中间件 (3)  │    │   LLM Qwen3-Max │
│  (5个)    │    │ 监控/日志/   │    └─────────────────┘
│           │    │  动态提示词  │
└─────┬─────┘    └──────────────┘
      │
      ├─ rag_summarize ──── RagSummaryService ──── Chroma Vector Store
      │        │                    │                    │
      │        │                    ├─ retriever (k=8)   ├─ src/data/*.txt
      │        │                    └─ LLM summary       ├─ src/data/*.pdf
      │        │                                         └─ chunk_size=500
      │        │
      ├─ get_user_id ────── random(1001~1010)
      ├─ get_current_month ─ random(2025-01~12)
      ├─ fetch_external_data ─ src/data/external/records.csv
      └─ fill_context_for_report ─ 触发 runtime.context["report"]=True

                         ┌─── MCP 协议 (stdio) ───┐
                         │                       │
                         ▼                       ▼
              ┌──────────────────────────────────────┐
              │      气象 Agent: WeatherServer        │
              │      (独立进程, FastMCP)              │
              │                                      │
              │  ┌──────────────────────────────┐    │
              │  │ get_weather(city?) → 天气查询  │    │
              │  │ get_location()     → IP 定位   │    │
              │  └──────────┬───────────────────┘    │
              └─────────────┼────────────────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              高德天气 API    高德 IP 定位 / ip-api.com
```

### 2.2 Agent 交互流程

```
用户输入 "帮我生成6月使用报告"
        │
        ▼
┌─────────────────┐
│  Think: 用户要生成报告          │
│  → 先获取用户ID                │
└────────┬────────┘
         │ 调用 get_user_id()
         ▼
┌─────────────────┐
│  Observe: user_id = "1003"     │
│  → 需要月份信息                │
└────────┬────────┘
         │ 调用 get_current_month()
         ▼
┌─────────────────┐
│  Observe: month = "2025-06"    │
│  → 先调用 fill_context_for_report │
└────────┬────────┘
         │ 调用 fill_context_for_report()
         │ → middleware 设置 context["report"] = True
         ▼
┌─────────────────┐
│  Observe: 上下文已切换为报告模式   │
│  → 获取使用数据                │
└────────┬────────┘
         │ 调用 fetch_external_data("1003", "2025-06")
         ▼
┌─────────────────┐
│  Observe: 获取到清洁效率、耗材等   │
│  → 信息足够，生成报告           │
└────────┬────────┘
         │ 切换到 report_prompt
         ▼
     输出 Markdown 格式报告
```

### 2.3 数据流

```
用户 query → ReactAgent.execute_stream()
                    │
                    ▼
           create_agent.stream(input, context={"report": False})
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    LLM 推理            中间件拦截
    (Qwen3-Max)         - monitor_tool: 记录工具调用
                        - log_before_model: 记录消息数
                        - report_prompt_switch: 检查 context["report"]
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    工具执行              动态提示词
    - RAG检索 (本地)       - report=False → main_prompt.txt
    - 数据查询 (本地)      - report=True  → report_prompt.txt
    - 天气定位 ──────────→ 委托给气象 Agent (MCP 跨进程)
          │
          ▼
    ToolMessage → 回到 LLM 推理 → 继续循环或输出答案
                    │
                    ▼
          stream_mode="values" → yield content → Streamlit UI
```

### 2.4 多智能体协作模型

系统采用**双智能体协作**架构，主控 Agent 与气象 Agent 职责分离、松耦合通信：

```
┌─────────────────────────────────────────────────────────┐
│                    主控 Agent (ReAct)                    │
│  职责: 对话编排、意图理解、RAG 检索、报告生成           │
│  工具: rag_summarize / fetch_external_data / ...        │
│  LLM:  Qwen3-Max                                       │
└─────────────────────┬───────────────────────────────────┘
                      │ 需要天气/定位时
                      │ → 通过 MCP 协议委托
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    气象 Agent (MCP)                      │
│  职责: 天气查询、IP 定位、API 容错回退                  │
│  工具: get_weather / get_location                        │
│  进程: 独立 Python 子进程 (FastMCP + stdio)              │
│  后端: 高德天气 API / 高德 IP 定位 / ip-api.com         │
└─────────────────────────────────────────────────────────┘
```

**协作流程**：用户询问天气 → 主控 Agent 推理需要天气信息 → 调用 MCP 工具 → `MultiServerMCPClient` 通过 stdio 向气象 Agent 子进程发送请求 → 气象 Agent 调用高德 API → 结果沿 MCP 返回 → 主控 Agent 整合到回答中。

### 2.5 组件说明

| 组件 | 层级 | 职责 | 技术 |
|------|------|------|------|
| Streamlit UI | 表现层 | Web 交互界面，会话管理 | Streamlit |
| ReactAgent (主控) | 编排层 | 对话编排，ReAct 循环 | LangGraph `create_agent` |
| WeatherAgent (气象) | 服务层 | 天气/定位，独立进程 | FastMCP + 高德 API |
| Agent Tools × 5 | 工具层 | 主控 Agent 本地工具 | `@tool` + requests / Chroma |
| Middleware × 3 | 横切层 | 日志、动态提示词 | `@wrap_tool_call` / `@before_model` / `@dynamic_prompt` |
| RagSummaryService | 知识层 | 检索 + LLM 摘要 | Chroma retriever + Qwen |
| VectorStoreService | 数据层 | 文档管理、向量存储 | Chroma + text-embedding-v4 |
| ModelFactory | 基础设施 | LLM / Embedding 实例化 | 抽象工厂 + ChatTongyi + DashScope |
| MultiServerMCPClient | 通信层 | MCP 客户端，连接气象 Agent | langchain-mcp-adapters |

---

## 三、API Spec（接口规格）

### 3.1 工具接口

#### Tool 1: `rag_summarize`

```
名称:       rag_summarize
描述:       从向量存储中检索参考资料并生成摘要
入参:
  query     str  (必填)  检索关键词，如 "小户型适合什么机器人"
出参:
  result    str          基于检索文档的 LLM 摘要回答
异常:
  知识库无匹配 → 返回空上下文下的 LLM 回答
依赖:
  Chroma 向量库 (collection: "agent")
  DashScope text-embedding-v4
  Qwen3-Max
```

#### Tool 2: `get_weather`

```
名称:       get_weather
描述:       获取指定城市天气（不传则自动定位）
入参:
  city      str  (可选)  城市名，如 "北京"，默认自动定位
出参:
  result    str          天气描述，如 "北京今天晴，气温15~25℃"
异常:
  API 超时/失败 → 返回错误描述字符串
依赖:
  高德天气 API (restapi.amap.com/v3/weather/weatherInfo)
  AMAP_KEY 环境变量
```

#### Tool 3: `get_user_location`

```
名称:       get_user_location
描述:       通过 IP 自动获取用户当前城市
入参:       无
出参:
  city      str          城市名称，如 "北京市"
异常:
  高德失败 → 回退 ip-api.com
  全部失败 → 返回 "北京"
```

#### Tool 4: `get_user_id`

```
名称:       get_user_id
描述:       获取用户 ID（模拟）
入参:       无
出参:
  user_id   str          用户 ID，如 "1003"
范围:
  从 ["1001"..."1010"] 中随机返回
```

#### Tool 5: `get_current_month`

```
名称:       get_current_month
描述:       获取当前月份（模拟）
入参:       无
出参:
  month     str          月份，格式 YYYY-MM，如 "2025-06"
范围:
  从 2025-01 至 2025-12 中随机返回
```

#### Tool 6: `fetch_external_data`

```
名称:       fetch_external_data
描述:       查询指定用户在指定月份的使用记录
入参:
  user_id   str  (必填)  用户 ID，如 "1003"
  month     str  (必填)  月份，格式 YYYY-MM
出参:
  result    dict/str      使用记录，包含:
    - 特征:  房屋面积、家庭结构、地面类型
    - 效率:  覆盖率、日均清扫、漏扫区域
    - 耗材:  主刷寿命、滤网状态、边刷磨损
    - 对比:  同类用户排名/建议
异常:
  用户/月份不存在 → 返回空字符串
数据源:
  data/external/records.csv (121 行，10 用户 × 12 月)
```

#### Tool 7: `fill_context_for_report`

```
名称:       fill_context_for_report
描述:       触发中间件将运行时上下文切换为报告生成模式
入参:       无
出参:       无返回值（仅副作用）
副作用:
  runtime.context["report"] = True
  → report_prompt_switch 中间件读取该标记
  → 后续 LLM 调用切换为 report_prompt.txt
调用约束:
  仅在用户明确要求生成报告时调用
  非报告场景严禁调用
```

### 3.2 中间件接口

```python
# 1. 工具调用监控 + 报告模式触发
@wrap_tool_call
def monitor_tool(request: ToolCallRequest,
                 handler: Callable) -> ToolMessage | Command:
    """
    前置: 记录工具名和参数
    后置: 若调用 fill_context_for_report，设置 context["report"] = True
    """

# 2. LLM 调用日志
@before_model
def log_before_model(state: AgentState,
                     runtime: Runtime) -> None:
    """
    每次 LLM 调用前记录当前消息数量
    """

# 3. 动态提示词切换
@dynamic_prompt
def report_prompt_switch(request: ModelRequest) -> str:
    """
    读取 runtime.context["report"]:
      True  → 返回 prompts/report_prompt.txt
      False → 返回 prompts/main_prompt.txt
    """
```

### 3.3 运行时上下文

```python
# Agent.stream() 传入的初始上下文
context = {
    "report": False    # bool, 标记是否为报告生成模式
}

# 中间件可读写 runtime.context
# fill_context_for_report 工具触发后 → context["report"] = True
# report_prompt_switch 每次 LLM 调用前读取 context["report"]
```

### 3.4 配置规格

```yaml
# agent.yml - Agent 外部依赖配置
AMAP_WEATHER_URL: "https://restapi.amap.com/v3/weather/weatherInfo"
CITY_CODE_URL: "https://restapi.amap.com/v3/config/district"
external_data_path: "src/data/external/records.csv"

# rag.yml - 模型配置
chat_model_name: "qwen3-max"
embedding_model_name: "text-embedding-v4"

# chroma.yml - 向量库配置
collection_name: "agent"
persist_directory: "chroma_db"
k: 8                      # 检索返回 Top-K
chunk_size: 500
chunk_overlap: 50

# prompts.yml - 提示词路径
main_prompt_path: "src/prompts/main_prompt.txt"
rag_summary_prompt_path: "src/prompts/rag_summary_prompt.txt"
report_prompt_path: "src/prompts/report_prompt.txt"
```

### 3.5 环境变量

```bash
AMAP_KEY             # 高德地图 Web API Key（必填）
DASHSCOPE_API_KEY    # 阿里云 DashScope API Key（必填，ChatTongyi / Embedding 自动读取）
```

### 3.6 气象 Agent (MCP) 接口

气象 Agent 作为独立智能体，通过 MCP（Model Context Protocol）与主控 Agent 松耦合协作：

```json
// 气象 Agent: src/mcp_server/weather_server.py
// 运行时: 独立 Python 子进程 (FastMCP)
// 传输: stdio (标准输入输出管道)
{
  "agent": "WeatherAgent",
  "role": "天气与定位服务专家",
  "protocol": "MCP (Model Context Protocol)",
  "tools": [
    {
      "name": "get_weather",
      "description": "查询指定城市天气，返回天气描述与气温",
      "parameters": {
        "city": "str (optional) — 城市名，如\"武汉\"，不填则自动 IP 定位"
      },
      "fault_tolerance": "API 超时 → 返回错误描述字符串，不抛异常"
    },
    {
      "name": "get_location",
      "description": "IP 定位获取当前城市",
      "parameters": {},
      "fault_tolerance": "高德失败 → 回退 ip-api.com → 全部失败返回\"北京\""
    }
  ],
  "env": {
    "AMAP_KEY": "从父进程 os.environ 继承"
  }
}
```

**Agent 间通信流程**：

```
主控 Agent 决策需要天气
  → 调用 MCP 工具 (get_weather/get_location)
  → MultiServerMCPClient 序列化请求 → stdio 管道
  → 气象 Agent 子进程接收 → 调用高德 API
  → 结果通过 stdio 返回 → MultiServerMCPClient 反序列化
  → _to_sync() 包装器转为 ToolMessage
  → 主控 Agent 整合到用户回复
```

主 Agent 通过 `MultiServerMCPClient` 自动发现并加载气象 Agent 暴露的工具，`_to_sync()` 包装器将异步 MCP 调用转为同步 `@tool`，无缝集成到 LangGraph 工具列表。

---

## 四、Design Spec（设计规格）

### 4.1 核心数据结构

```python
# AgentState — LangGraph 内部状态（消息列表）
# 类型: list[BaseMessage]
# 由 create_agent 自动管理，含 HumanMessage / AIMessage / ToolMessage
# 示例:
[
    HumanMessage(content="北京今天天气怎么样"),
    AIMessage(content=None, tool_calls=[{"name": "get_weather", "args": {"city": "北京"}}]),
    ToolMessage(content="北京今天晴，气温15~25℃", tool_call_id="..."),
    AIMessage(content="北京今天天气晴，气温15~25℃，适合扫地机器人工作。")
]

# Runtime Context — 跨轮次上下文
context = {
    "report": False    # bool, 报告模式标记
                       # fill_context_for_report 调用后 → True
                       # report_prompt_switch 读取 → 切换提示词
}

# External Data Record — CSV 解析后的内存结构
external_data = {
    "1003": {
        "2025-06": {
            "特征": "80㎡/两口之家/木地板",
            "效率": "覆盖率92%/日均1.2次/漏扫阳台",
            "耗材": "主刷70%/滤网45%/边刷60%",
            "对比": "同类排名前30%/建议增加边角清洁"
        }
    }
}

# RAG 检索结果
retrieved_docs: list[Document] = [
    Document(
        page_content="选购指南：小户型建议选择机身轻薄...",
        metadata={"source": "src/data/选购指南.txt"}
    ),
    ...
]
```

### 4.2 抽象工厂模式

```python
# 模型实例化采用抽象工厂，便于切换 LLM / Embedding 厂商
# src/model/factor.py

class BaseModelFactor(ABC):
    @abstractmethod
    def generate(self) -> Embeddings | BaseChatModel: ...

class ChatModelFactor(BaseModelFactor):
    def generate(self): return ChatTongyi(model="qwen3-max")

class EmbeddingsFactor(BaseModelFactor):
    def generate(self): return DashScopeEmbeddings(model="text-embedding-v4")

chat_model = ChatModelFactor().generate()      # 全局单例
embedding_model = EmbeddingsFactor().generate()
```

### 4.3 中间件管道

```
Tool Call 请求
  │
  ├─ @wrap_tool_call (monitor_tool)
  │     ├─ before: 记录工具名 + 参数
  │     ├─ 执行工具
  │     └─ after: 若 fill_context_for_report → context["report"] = True
  │
  ▼
模型调用前
  │
  ├─ @before_model (log_before_model)
  │     └─ 记录当前消息数
  │
  ├─ @dynamic_prompt (report_prompt_switch)
  │     ├─ context["report"] == True  → report_prompt.txt
  │     └─ context["report"] == False → main_prompt.txt
  │
  ▼
LLM 推理 (Qwen3-Max)
```

---

## 五、Test Spec（测试规格）

### 5.1 测试策略

| 层级 | 类型 | 工具 | 覆盖范围 |
|------|------|------|----------|
| 单元测试 | 工具函数 | 手动验证 | 7 个 Tool 独立调通 |
| 集成测试 | Agent 端到端 | Streamlit 交互 | 天气查询、RAG 问答、报告生成 |
| 评估测试 | RAGAS 四大指标 | `src/tests/test_ragas.py` | 检索精准度/召回率、回答忠实度/相关性 |

### 5.2 RAGAS 评估结果

| 指标 | 分数 | 评级 | 说明 |
|------|------|------|------|
| context_precision | 0.82 | 良好 | 检索结果相关性强，chunk_size=500 优化后显著提升 |
| context_recall | 0.87 | 良好 | 知识库覆盖率大幅改善，k=8 确保充分召回 |
| faithfulness | 0.72 | 良好 | LLM 回答忠实于检索文档 |
| answer_relevancy | 0.76 | 良好 | 回答紧扣用户问题 |

### 5.3 测试用例设计

```python
test_queries = [
    {"question": "小户型适合买什么样的扫地机器人？",
     "ground_truth": "小户型建议选择机身轻薄、激光导航的机型..."},
    {"question": "扫地机器人故障：无法回充怎么办？",
     "ground_truth": "检查充电座是否通电、周围是否有障碍物..."},
    {"question": "扫地机器人日常怎么维护保养？",
     "ground_truth": "定期清理尘盒、滤网、主刷和边刷..."},
    {"question": "家里有宠物，选购扫地机器人要注意什么？",
     "ground_truth": "选择大吸力、毛发防缠绕设计、HEPA滤网的机型..."},
    {"question": "如何选购扫地机器人？激光导航和视觉导航哪个好？",
     "ground_truth": "激光导航精度高、黑暗环境可用；视觉导航成本低但光线依赖强..."},
]
```
