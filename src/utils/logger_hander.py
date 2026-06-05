import logging
import os
from .path_tool import *
from datetime import datetime

LOG_ROOT = get_abs_path("logs")
os.makedirs(LOG_ROOT, exist_ok=True)

DEFAULT_LOG_FORMAT = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")

def get_logger(name: str = "agent", console_level: int = logging.INFO, file_level: int = logging.DEBUG, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置logger的最低级别为DEBUG，确保所有日志都能被处理

    if logger.handlers:
        return logger  # 如果logger已经有处理器了，就直接返回，避免重复添加处理器
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    
    logger.addHandler(console_handler)
    
    if not log_file :
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # 创建文件处理器 
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    
    logger.addHandler(file_handler)
    
    return logger


logger = get_logger()  # 获取默认logger实例