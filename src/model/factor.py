from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from utils.config_hander import rag_conf


class BaseModelFactor(ABC):
    @abstractmethod
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactor(BaseModelFactor):
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatTongyi(model=rag_conf["chat_model_name"])

class EmbeddingsFactor(BaseModelFactor):
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])
    
    
    
chat_model = ChatModelFactor().generate()
embedding_model = EmbeddingsFactor().generate()