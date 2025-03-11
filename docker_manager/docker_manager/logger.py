"""日志和彩色输出模块"""

import logging
import sys
import os
from typing import Dict, Any, Optional
from rich.console import Console
from rich.theme import Theme

# 创建Rich控制台
custom_theme = Theme({
    "info": "green",
    "warning": "yellow",
    "error": "red",
    "debug": "blue"
})
console = Console(theme=custom_theme)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建日志记录器
logger = logging.getLogger('docker_manager')


def print_colored(message: str, color: str = 'no_color') -> None:
    """
    打印彩色文本
    
    Args:
        message: 要打印的消息
        color: 颜色名称
    """
    # 将颜色名称映射到Rich样式
    style_map = {
        'green': 'info',
        'yellow': 'warning',
        'red': 'error',
        'blue': 'debug',
        'no_color': None
    }
    
    style = style_map.get(color, None)
    console.print(message, style=style)


def load_colors_from_config(config: Dict[str, Any]) -> None:
    """
    从配置中加载颜色设置
    
    Args:
        config: 配置字典
    """
    # 使用Rich时不需要加载颜色配置
    pass


class RichHandler(logging.Handler):
    """Rich日志处理器"""
    
    def emit(self, record):
        """输出日志记录"""
        message = self.format(record)
        
        # 根据日志级别选择样式
        if record.levelno >= logging.ERROR:
            console.print(message, style="error")
        elif record.levelno >= logging.WARNING:
            console.print(message, style="warning")
        elif record.levelno >= logging.INFO:
            console.print(message, style="info")
        else:
            console.print(message, style="debug")


def setup_logger(name: str = "docker_manager", level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        日志记录器
    """
    # 创建日志器
    logger = logging.getLogger(name)
    
    # 如果已经有处理器，说明已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(level)
    
    # 创建Rich处理器
    rich_handler = RichHandler()
    rich_handler.setLevel(level)
    
    # 设置格式
    formatter = logging.Formatter("%(levelname)-8s %(message)s")
    rich_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(rich_handler)
    
    return logger 