"""
RAG 评估脚本 — RAGAS 四大指标
"""
import os
import sys
import warnings
warnings.filterwarnings("ignore")

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

for env_file in [".env", ".env.example"]:
    env_path = os.path.join(PROJECT_ROOT, env_file)
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from rag.rag_service import RagSummaryService

_eval_llm = LangchainLLMWrapper(ChatTongyi(model="qwen-plus"))
_eval_emb = LangchainEmbeddingsWrapper(DashScopeEmbeddings(model="text-embedding-v4"))

test_queries = [
    {
        "question": "小户型适合买什么样的扫地机器人？",
        "ground_truth": "小户型建议选择机身轻薄、激光导航的机型，重点关注沙发底部通过性和边角清洁能力。",
    },
    {
        "question": "扫地机器人故障：无法回充怎么办？",
        "ground_truth": "检查充电座是否通电、周围是否有障碍物、机器人充电触点是否脏污，清理后重试。",
    },
    {
        "question": "扫地机器人日常怎么维护保养？",
        "ground_truth": "定期清理尘盒、滤网、主刷和边刷，检查传感器是否积灰，每3-6个月更换耗材。",
    },
    {
        "question": "家里有宠物，选购扫地机器人要注意什么？",
        "ground_truth": "选择大吸力、毛发防缠绕设计、HEPA滤网的机型，重点关注胶刷和尘盒容量。",
    },
    {
        "question": "如何选购扫地机器人？激光导航和视觉导航哪个好？",
        "ground_truth": "激光导航精度高、黑暗环境可用；视觉导航成本低但光线依赖强。首选激光导航。",
    },
]

print("RAG 评估 — RAGAS 四大指标")
print("-" * 50)

rag = RagSummaryService()
samples = []

for i, item in enumerate(test_queries):
    print(f"[{i+1}/{len(test_queries)}] {item['question']}")
    docs = rag.retriever_docs(item["question"])
    contexts = [d.page_content for d in docs]
    answer = rag.rag_summary(item["question"])
    print(f"  检索: {len(docs)} 篇 | 回答: {answer[:60]}...")
    samples.append({
        "question": item["question"],
        "answer": answer,
        "contexts": contexts,
        "ground_truth": item["ground_truth"],
    })

dataset = Dataset.from_dict({
    "question": [s["question"] for s in samples],
    "answer": [s["answer"] for s in samples],
    "contexts": [s["contexts"] for s in samples],
    "ground_truth": [s["ground_truth"] for s in samples],
})

print("\n评估中...")
result = evaluate(
    dataset,
    metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
    llm=_eval_llm,
    embeddings=_eval_emb,
)

print("\n" + "=" * 50)
print("评估结果（满分 1.0）")
print("=" * 50)
print(result)
print()

for key, label in [
    ("context_precision", "检索精准度"),
    ("context_recall", "检索召回率"),
    ("faithfulness", "回答忠实度"),
    ("answer_relevancy", "回答相关性"),
]:
    try:
        scores = result[key]
        avg = sum(scores) / len(scores) if scores else 0
        flag = "[良好]" if avg > 0.7 else "[一般]" if avg > 0.4 else "[较差]"
        print(f"  {label}: {avg:.4f}  {flag}")
    except KeyError:
        print(f"  {label}: N/A")
