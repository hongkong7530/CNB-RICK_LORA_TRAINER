import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from ..config import config

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    
    # 检查是否已经有处理器，如果有则不再添加
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # 使用TimedRotatingFileHandler按周分割日志文件
    log_file = os.path.join(config.LOGS_DIR, 'application.log')
    # 创建按周轮换的日志处理器
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='W0',  # 每周一轮换
        interval=1,  # 每1周
        backupCount=12  # 保留12周的日志
    )
    file_handler.setLevel(logging.INFO)
    # 设置后缀名格式为 application.log.YYYY-MM-DD
    file_handler.suffix = "%Y-%m-%d"
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器 - 添加模块名称以便于区分不同模块的日志
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 