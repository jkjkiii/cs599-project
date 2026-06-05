from .config_hander import prompts_conf
from .path_tool import *
from .logger_hander import logger

    
def load_system_prompt() -> str:
    prompt_path = get_abs_path(prompts_conf["main_prompt_path"])
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading system prompt from {prompt_path}: {e}")
        return ""
    
def load_rag_summary_prompt() -> str:
    prompt_path = get_abs_path(prompts_conf["rag_summary_prompt_path"])
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading RAG summary prompt from {prompt_path}: {e}")
        return ""

def load_report_prompt() -> str:
    prompt_path = get_abs_path(prompts_conf["report_prompt_path"])
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading report prompt from {prompt_path}: {e}")
        return ""
    
    
if __name__ == "__main__":
    print(load_system_prompt())
    print(load_rag_summary_prompt())
    print(load_report_prompt())