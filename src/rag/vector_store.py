import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_chroma import Chroma
from utils.config_hander import chroma_conf
from utils.path_tool import *
from model.factor import chat_model, embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.file_hander import pdf_loader,txt_loader,listdir_with_allowed_types,get_file_md5_hex
from utils.logger_hander import logger
class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
            embedding_function=embedding_model,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
        )
        
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})
    
    
    def load_document(self):
        
        def check_md5_hex(md5_for_check:str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False
            
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    if line.strip() == md5_for_check:
                        return True
                    
                return False
            
            
        def save_md5_hex(md5_hex:str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_hex + "\n")
                
                
        def get_filr_documents(file_path:str):
            if file_path.endswith(".pdf"):
                return pdf_loader(file_path)
            elif file_path.endswith(".txt"):
                return txt_loader(file_path)
            else:
                return []
            
        allowed_files_path = listdir_with_allowed_types(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )
        
        for file_path in allowed_files_path:
            md5_hex = get_file_md5_hex(file_path)
            if not md5_hex:
                continue
            
            if check_md5_hex(md5_hex):
                logger.info(f"File {file_path} has already been processed, skipping.")
                continue
            
            documents = get_filr_documents(file_path)
            if not documents:#判断文件是否加载成功
                logger.warning(f"No documents loaded from file {file_path}, skipping.")
                continue
            split_documents = self.text_splitter.split_documents(documents)
            if not split_documents:#切分操作是否产出了有效结果
                logger.warning(f"No documents obtained after splitting for file {file_path}, skipping.")
                continue
            self.vector_store.add_documents(split_documents)
            save_md5_hex(md5_hex)
            logger.info(f"File {file_path} processed and added to vector store successfully.")
            
            
            
if __name__ == "__main__":
    vector_store_service = VectorStoreService()
    vector_store_service.load_document()
    retriver = vector_store_service.get_retriever()
    res = retriver.invoke("迷路")
    for r in res:
        print(r.page_content)
        print("===")