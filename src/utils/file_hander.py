import os, hashlib
from .logger_hander import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, UnstructuredFileLoader, PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader

def get_file_md5_hex(file_path: str) -> str:
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    if not os.path.isfile(file_path):
        logger.error(f"Not a file: {file_path}")
        return None
    md5_obj = hashlib.md5()
    chunk_size = 4096
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5_obj.update(chunk)
        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error occurred while calculating MD5 for {file_path}: {e}")
        return None
    
    
def listdir_with_allowed_types(dir_path: str, allowed_types: tuple[str]):
    if not os.path.exists(dir_path):
        logger.error(f"Directory not found: {dir_path}")
        return []
    if not os.path.isdir(dir_path):
        logger.error(f"Not a directory: {dir_path}")
        return []
    try:
        files = []
        for item in os.listdir(dir_path):
            if item.endswith(allowed_types):
                files.append(os.path.join(dir_path, item))
        return tuple(files)
    except Exception as e:
        logger.error(f"Error occurred while listing directory {dir_path}: {e}")
        return []
    
def pdf_loader(file_path:str,password:str=None) -> list[Document]:
    try:
        loader = PyPDFLoader(file_path, password=password)
        return loader.load()
    except Exception as e:
        logger.error(f"Error loading PDF file {file_path}: {e}")
        return []
    
def txt_loader(file_path:str) -> list[Document]:
    try:
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()
    except Exception as e:
        logger.error(f"Error loading TXT file {file_path}: {e}")
        return []