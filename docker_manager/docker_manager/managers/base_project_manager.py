"""项目管理基类"""

import os
import subprocess
from typing import Dict, Any, Optional

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import run_command


class BaseProjectManager(BaseManager):
    """项目管理基类，包含项目和镜像管理的共享功能"""
    
    def __init__(self, project_name: str = None, config: Dict[str, Any] = None):
        """
        初始化项目管理器
        
        Args:
            project_name: 项目名称，如果提供则从项目配置文件加载
            config: 配置字典，如果为None则使用默认配置
        """
        super().__init__()
        
        self.project_name = None
        self.config = {}
        self.project_dir = None
        self.image_name = None
        
        # 如果提供了项目名称或配置，加载项目信息
        if project_name or config:
            self.load_project(project_name, config)
    
    def load_project(self, project_name: str = None, config: Dict[str, Any] = None):
        """
        加载项目配置
        
        Args:
            project_name: 项目名称，如果提供则从项目配置文件加载
            config: 配置字典，如果为None则使用默认配置
            
        Raises:
            ValueError: 如果项目不存在或配置无效
        """
        from ..config import load_project_config
        
        if project_name is None and config is None:
            raise ValueError("必须指定项目名称或提供配置")
            
        if project_name is not None and not config:
            try:
                self.config = load_project_config(project_name)
                self.project_name = project_name
            except FileNotFoundError:
                raise ValueError(f"项目 '{project_name}' 不存在，请先添加项目")
        else:
            self.config = config or {}
            self.project_name = self.config.get('project_name', 'default')
            
        # 检查配置是否有效
        if not self.config.get('project_dir'):
            raise ValueError(f"项目 '{self.project_name}' 的配置无效，缺少项目目录")
            
        self.project_dir = self.config['project_dir']
        self.image_name = self.config['image_name']
        
        # 推送配置
        self.push_config = self.config.get('push', {})
        
    def detect_docker_compose_cmd(self, compose_file: str) -> str:
        """
        检测Docker Compose命令
        
        Args:
            compose_file: Docker Compose文件路径
            
        Returns:
            Docker Compose命令
            
        Raises:
            RuntimeError: 如果未找到Docker Compose命令
        """
        # 检查是否支持新版命令格式
        try:
            run_command("docker compose version", shell=True)
            return f"docker compose -f {compose_file}"
        except subprocess.CalledProcessError:
            # 检查是否支持旧版命令格式
            try:
                run_command("docker-compose version", shell=True)
                return f"docker-compose -f {compose_file}"
            except subprocess.CalledProcessError:
                logger.error("未找到Docker Compose命令。请确保已安装Docker Compose。")
                raise RuntimeError("未找到Docker Compose命令") 