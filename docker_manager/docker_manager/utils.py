"""工具函数模块"""

import os
import subprocess
import shlex
from typing import Tuple, List, Optional, Dict, Any
import datetime
import json
import tempfile

from .logger import logger


def run_command(command: str, shell: bool = False, check: bool = True) -> Tuple[int, str, str]:
    """
    运行shell命令并返回结果
    
    Args:
        command: 要运行的命令
        shell: 是否使用shell执行
        check: 是否检查返回码
        
    Returns:
        (返回码, 标准输出, 标准错误)
    """
    logger.debug(f"执行命令: {command}")
    
    if shell:
        # 使用shell执行命令
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
    else:
        # 不使用shell执行命令
        args = shlex.split(command)
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
    
    # 获取输出
    stdout, stderr = process.communicate()
    return_code = process.returncode
    
    # 检查返回码
    if check and return_code != 0:
        logger.error(f"命令执行失败: {command}")
        logger.error(f"错误输出: {stderr}")
        raise subprocess.CalledProcessError(return_code, command, stdout, stderr)
    
    return return_code, stdout, stderr


def get_timestamp() -> str:
    """
    获取当前时间戳，格式为YYYYMMDD_HHMMSS
    
    Returns:
        格式化的时间戳字符串
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def create_temp_file(content: str) -> str:
    """
    创建临时文件并写入内容
    
    Args:
        content: 要写入的内容
        
    Returns:
        临时文件的路径
    """
    fd, path = tempfile.mkstemp(text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def confirm_action(message: str, default: bool = False) -> bool:
    """
    请求用户确认操作
    
    Args:
        message: 提示消息
        default: 默认选项
        
    Returns:
        用户是否确认
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} ({default_str}): ").strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes') 