import os
import yaml
from .path_tool import *

def load_rag_config(config_path: str = get_abs_path("src/config/rag.yml"), encoding: str = 'utf-8'):
    with open(config_path, 'r', encoding=encoding) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config

def load_chroma_config(config_path: str = get_abs_path("src/config/chroma.yml"), encoding: str = 'utf-8'):
    with open(config_path, 'r', encoding=encoding) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config

def load_prompts_config(config_path: str = get_abs_path("src/config/prompts.yml"), encoding: str = 'utf-8'):
    with open(config_path, 'r', encoding=encoding) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config

def load_agent_config(config_path: str = get_abs_path("src/config/agent.yml"), encoding: str = 'utf-8'):
    with open(config_path, 'r', encoding=encoding) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    config["AMAP_KEY"] = os.getenv("AMAP_KEY", "")
    return config

rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()
