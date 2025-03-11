"""容器管理基类"""

import os
import subprocess
import time
import docker
from typing import Dict, Any, Optional, List

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import run_command


class BaseContainerManager(BaseManager):
    """容器管理基类，包含容器管理的共享功能"""
    
    def __init__(self, container_name: str = None, config: Dict[str, Any] = None):
        """
        初始化容器管理器
        
        Args:
            container_name: 容器名称，如果提供则从容器配置文件加载
            config: 配置字典，如果为None则使用默认配置
        """
        super().__init__()
        
        self.container_name = None
        self.config = {}
        self.image_name = None
        
        # 清理配置
        self.cleanup_dirs = []
        self.exclude_dirs = []
        
        # 备份配置
        self.backup_config = {}
        
        # 如果提供了容器名称或配置，加载容器信息
        if container_name or config:
            self.load_container(container_name, config)
    
    def load_container(self, container_name: str = None, config: Dict[str, Any] = None):
        """
        加载容器配置
        
        Args:
            container_name: 容器名称，如果提供则从容器配置文件加载
            config: 配置字典，如果为None则使用默认配置
            
        Raises:
            ValueError: 如果容器不存在或配置无效
        """
        from ..config import load_container_config
        
        if container_name is None and config is None:
            raise ValueError("必须指定容器名称或提供配置")
            
        if container_name is not None and not config:
            try:
                self.config = load_container_config(container_name)
                self.container_name = container_name
            except FileNotFoundError:
                raise ValueError(f"容器 '{container_name}' 不存在，请先添加容器")
        else:
            self.config = config or {}
            self.container_name = self.config.get('container_name', 'default')
            
        # 检查配置是否有效
        if not self.config.get('image_name'):
            raise ValueError(f"容器 '{self.container_name}' 的配置无效，缺少镜像名称")
            
        self.image_name = self.config['image_name']
        
        # 清理配置
        cleanup_config = self.config.get('cleanup', {})
        self.cleanup_dirs = cleanup_config.get('directories', [])
        self.exclude_dirs = cleanup_config.get('exclude_directories', [])
        
        # 备份配置
        self.backup_config = self.config.get('backup', {})
        
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
    
    def get_container(self) -> docker.models.containers.Container:
        """
        获取容器对象
        
        Returns:
            容器对象
            
        Raises:
            ValueError: 如果容器不存在
        """
        try:
            return self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            raise ValueError(f"容器 '{self.container_name}' 不存在")
    
    def check_container_running(self) -> bool:
        """
        检查容器是否正在运行
        
        Returns:
            是否正在运行
        """
        try:
            container = self.get_container()
            return container.status == "running"
        except ValueError:
            return False
    
    def list_backups(self, image_name: str = None) -> List[Dict[str, Any]]:
        """
        列出指定镜像的所有备份
        
        Args:
            image_name: 镜像名称，如果为None则使用当前容器的镜像
            
        Returns:
            备份列表，每个备份包含标签、创建时间和大小信息
        """
        if image_name is None:
            image_name = self.image_name.split(':')[0]  # 移除标签部分
            
        backups = []
        try:
            images = self.docker_client.images.list(
                name=f"{image_name}:backup_*"
            )
            
            for image in images:
                # 获取标签
                tag = [t for t in image.tags if t.startswith(f"{image_name}:backup_")][0]
                
                # 获取创建时间
                created = image.attrs.get('Created', 'Unknown')
                if created != 'Unknown':
                    # 转换时间格式
                    from datetime import datetime
                    created_dt = datetime.strptime(created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取大小
                size = image.attrs.get('Size', 0)
                size_gb = size / (1024 * 1024 * 1024)
                
                backups.append({
                    'tag': tag,
                    'created': created,
                    'size': size,
                    'size_str': f"{size_gb:.2f} GB"
                })
                
            # 按创建时间排序，最新的在前面
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
        except Exception as e:
            logger.error(f"列出备份镜像失败: {e}")
            return [] 