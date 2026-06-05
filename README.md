# 智扫通 — Agentic RAG 智能客服系统

扫地/扫拖一体机器人领域的 ReAct Agent 智能客服，基于 LangGraph + Chroma + Qwen3-Max 构建，支持 RAG 知识检索、天气环境分析、个人使用报告生成。

## 项目简介

本项目是 **CS599 企业级应用软件设计与开发** 课程期末大作业，选择 **方向一：Agentic AI 原生开发 → RAG 增强问答系统**。

核心能力：
- 基于向量知识库的 RAG 专业问答（故障排除、选购指南、维护保养）
- ReAct Agent 自主推理与多工具编排（天气查询、用户定位、外部数据检索）
- 动态提示词切换（常规问答 / 报告生成双模式）
- 流式对话交互（Streamlit 前端）

## 技术栈

| 类别 | 选型 |
|------|------|
| LLM | 阿里云通义千问 Qwen3-Max (ChatTongyi) |
| Embedding | DashScope text-embedding-v4 |
| Agent 框架 | LangGraph + LangChain (`create_agent`) |
| 向量数据库 | Chroma (本地持久化) |
| 前端 | Streamlit |
| 外部 API | 高德地图（天气、IP 定位）、ip-api.com（备用定位） |
| 协议 | Function Calling |

## 项目结构

```
├── README.md
├── .env                          # 环境变量（占位符，需填入真实 Key）
├── .gitignore
├── LICENSE                       # MIT
├── requirements.txt
├── src/
│   ├── app.py                    # Streamlit Web 入口
│   ├── agent/
│   │   ├── react_agent.py        # ReAct Agent 核心类
│   │   └── tools/
│   │       ├── agent_tools.py    # 7 个工具定义
│   │       └── middleware.py     # 3 个中间件钩子
│   ├── rag/
│   │   ├── vector_store.py       # Chroma 向量存储服务
│   │   └── rag_service.py        # RAG 检索 + LLM 摘要
│   ├── model/
│   │   └── factor.py             # 模型工厂（抽象工厂模式）
│   ├── mcp_server/
│   │   └── weather_server.py     # MCP 天气服务
│   ├── utils/
│   │   ├── config_hander.py      # YAML 配置加载
│   │   ├── file_hander.py        # 文件 I/O（MD5、PDF/TXT 加载）
│   │   ├── logger_hander.py      # 日志工厂
│   │   ├── path_tool.py          # 路径工具
│   │   └── prompt_loader.py      # 提示词加载器
│   ├── config/
│   │   ├── agent.yml             # Agent 配置（API 地址等）
│   │   ├── chroma.yml            # 向量库参数
│   │   ├── rag.yml               # 模型名称配置
│   │   └── prompts.yml           # 提示词路径
│   ├── prompts/
│   │   ├── main_prompt.txt       # 主提示词（ReAct 客服）
│   │   ├── rag_summary_prompt.txt# RAG 摘要提示词
│   │   └── report_prompt.txt     # 报告生成提示词
│   ├── data/
│   │   ├── 选购指南.txt
│   │   ├── 故障排除.txt
│   │   ├── 维护保养.txt
│   │   ├── 扫地机器人100问.pdf
│   │   ├── 扫地机器人100问2.txt
│   │   ├── 扫拖一体机器人100问.txt
│   │   └── external/
│   │       └── records.csv       # 模拟用户使用记录
│   ├── tests/                    # 测试用例
│   ├── docker/                   # Docker 部署
│   └── scripts/                  # 辅助脚本
└── docs/                         # 课程报告
```

## 快速开始

### 1. 环境准备

```bash
# Python 3.10+
pip install streamlit langchain langchain-community langchain-chroma langchain-text-splitters \
            dashscope pypdf pyyaml
```

### 2. 配置环境变量

直接编辑 `.env` 文件，填入你的 API Key：

```ini
AMAP_KEY=你的高德地图API Key
DASHSCOPE_API_KEY=你的阿里云DashScope API Key
```

### 3. 构建知识库

```bash
python -m src.rag.vector_store
```

首次运行会自动加载 `data/` 目录下的所有 PDF/TXT 文件，分割后存入 Chroma 向量库。

### 4. 启动服务

```bash
streamlit run src/app.py
```

浏览器访问 `http://localhost:8501` 即可使用。

## 系统架构

```
用户 → Streamlit UI → ReactAgent (LangGraph)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     ┌─────────┐    ┌──────────┐    ┌──────────┐
     │ 7 Tools │    │ Middleware│    │ Qwen3    │
     │         │    │          │    │ -Max     │
     └────┬────┘    └────┬─────┘    └──────────┘
          │              │
    ┌─────┼──────┐       │
    ▼     ▼      ▼       │
  RAG  高德API  CSV      │
(Chroma)(天气 (用户数据)  │
         定位)            │
                         │
    fill_context_for_report() → runtime.context["report"]=True
    report_prompt_switch()    → 动态切换提示词为报告模式
```

**ReAct 循环**: 思考 → 行动（调用工具）→ 观察（获取结果）→ 再思考 → 最终回答

## 工具清单

| 工具 | 功能 | 依赖 |
|------|------|------|
| `rag_summarize` | 从向量库检索专业知识并生成摘要 | Chroma + Qwen |
| `get_weather` | 查询指定城市天气 | 高德天气 API |
| `get_user_location` | IP 定位当前城市 | 高德 / ip-api.com |
| `get_user_id` | 获取模拟用户 ID | 本地随机 |
| `get_current_month` | 获取当前月份 | 本地随机 |
| `fetch_external_data` | 查询用户使用记录 | CSV 文件 |
| `fill_context_for_report` | 触发报告生成模式 | 中间件联动 |

## 中间件

| 中间件 | 类型 | 功能 |
|--------|------|------|
| `monitor_tool` | `@wrap_tool_call` | 记录工具调用日志，监测报告模式触发 |
| `log_before_model` | `@before_model` | 每次 LLM 调用前记录消息数 |
| `report_prompt_switch` | `@dynamic_prompt` | 根据上下文动态切换系统提示词 |

## 学术声明

本项目为 CS599 课程作业，引用了以下开源项目：

- [LangChain](https://github.com/langchain-ai/langchain) — LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent 编排框架
- [Chroma](https://github.com/chroma-core/chroma) — 向量数据库
- [Streamlit](https://github.com/streamlit/streamlit) — Web 前端框架

知识库数据来源于公开的扫地机器人产品文档及使用指南。

## License

MIT
