# -*- coding: utf-8 -*-
"""
日誌系統
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """日誌管理器"""
    
    def __init__(self, name: str = "CCDSystem", log_dir: str = "./logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 建立日誌目錄
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 清除現有 handlers
        self.logger.handlers.clear()
        
        # 控制台 Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 文件 Handler
        log_file = self.log_dir / f"ccd_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str):
        """Debug 訊息"""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """Info 訊息"""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Warning 訊息"""
        self.logger.warning(msg)
    
    def error(self, msg: str, exc_info: bool = False):
        """Error 訊息"""
        self.logger.error(msg, exc_info=exc_info)
    
    def critical(self, msg: str, exc_info: bool = False):
        """Critical 訊息"""
        self.logger.critical(msg, exc_info=exc_info)


# 全域 logger 實例
_global_logger: Optional[Logger] = None


def get_logger(name: str = "CCDSystem") -> Logger:
    """獲取全域 logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name)
    return _global_logger