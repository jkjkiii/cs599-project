from langchain_core.documents import Document

from .vector_store import VectorStoreService
from utils.prompt_loader import load_rag_summary_prompt
from langchain_core.prompts import PromptTemplate
from model.factor import chat_model
from langchain_core.output_parsers import StrOutputParser
class RagSummaryService(object):
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_summary_prompt()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()
        
    
    def _init_chain(self):
        chain = self.prompt_template | self.model | StrOutputParser()   
        return chain
    
    def retriever_docs(self, query:str) -> list[Document]:
        return self.retriever.invoke(query)
    
    def rag_summary(self, query:str) -> str:
        docs = self.retriever_docs(query)
        context = ""
        sources = []
        counter = 0
        for doc in docs:
            counter += 1
            source = doc.metadata.get("source", "未知来源")
            source_name = source.replace("\\", "/").split("/")[-1]
            if source_name not in sources:
                sources.append(source_name)
            context += f"【文档{counter} | 来源：{source_name}】：{doc.page_content}\n"

        answer = self.chain.invoke(
            {
                "input": query,
                "context": context
            }
        )

        if sources:
            answer += "\n\n📖 **参考来源**\n"
            for s in sources:
                answer += f"- {s}\n"

        return answer

if __name__ == "__main__":
    rag_summary_service = RagSummaryService()
    query = "小户型适合什么样的机器人"
    summary = rag_summary_service.rag_summary(query)
    print(summary)