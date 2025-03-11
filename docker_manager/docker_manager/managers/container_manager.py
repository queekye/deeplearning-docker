"""容器管理器类"""

import os
import time
import docker
import schedule
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from docker.errors import APIError, NotFound
from requests.exceptions import RequestException

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import run_command, confirm_action, get_timestamp

class ContainerError(Exception):
    """容器操作错误"""
    pass

class ContainerManager(BaseManager):
    """容器管理器类，用于管理容器的生命周期和维护"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    STARTUP_TIMEOUT = 30
    
    def __init__(self, project_dir: str, container_name: str):
        """
        初始化容器管理器
        
        Args:
            project_dir: 项目目录路径
            container_name: 容器名称
        """
        super().__init__()
        self.project_dir = Path(project_dir)
        self.container_name = container_name
        self.compose_file = None
        self._check_docker_connection()
        
    def _check_docker_connection(self):
        """检查Docker守护进程连接"""
        try:
            self.docker_client.ping()
        except (APIError, RequestException) as e:
            raise ContainerError(f"无法连接到Docker守护进程: {str(e)}")
    
    def _wait_for_container_status(self, expected_status: str, timeout: int = None) -> Tuple[bool, Optional[str]]:
        """等待容器达到预期状态"""
        if timeout is None:
            timeout = self.STARTUP_TIMEOUT
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container = self.docker_client.containers.get(self.container_name)
                if container.status == expected_status:
                    return True, None
                elif container.status in ["exited", "dead"]:
                    logs = container.logs(tail=50).decode('utf-8')
                    return False, f"容器异常退出，状态: {container.status}\n最后50行日志:\n{logs}"
            except NotFound:
                if expected_status == "removed":
                    return True, None
                return False, "容器不存在"
            except Exception as e:
                return False, f"检查容器状态失败: {str(e)}"
            time.sleep(1)
        
        return False, f"等待容器状态 {expected_status} 超时"
    
    def start_container(self, compose_file: str = 'docker-compose.yml') -> bool:
        """
        启动容器
        
        Args:
            compose_file: Docker Compose文件路径，相对于项目目录
            
        Returns:
            bool: 是否启动成功
        """
        try:
            self.compose_file = self.project_dir / compose_file
            if not self.compose_file.exists():
                raise ContainerError(f"Docker Compose文件不存在: {self.compose_file}")
            
            # 检查容器是否已经在运行
            try:
                container = self.docker_client.containers.get(self.container_name)
                if container.status == "running":
                    print_colored("容器已经在运行中", "yellow")
                    return True
            except NotFound:
                pass
            
            print_colored("启动容器...", "yellow")
            run_command(f"docker compose -f {self.compose_file} up -d", shell=True)
            
            success, error = self._wait_for_container_status("running")
            if not success:
                raise ContainerError(error)
            
            print_colored("容器启动成功", "green")
            return True
            
        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            return False
    
    def stop_container(self) -> bool:
        """
        停止容器
        
        Returns:
            bool: 是否停止成功
        """
        try:
            if not self.compose_file:
                raise ContainerError("未指定Docker Compose文件")
            
            print_colored("停止容器...", "yellow")
            run_command(f"docker compose -f {self.compose_file} down", shell=True)
            
            success, error = self._wait_for_container_status("removed")
            if not success:
                raise ContainerError(error)
            
            print_colored("容器已停止", "green")
            return True
            
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return False
    
    def save_as_image(self, image_name: str, cleanup: bool = False) -> bool:
        """
        将容器保存为镜像
        
        Args:
            image_name: 新镜像名称
            cleanup: 是否在保存前清理容器
            
        Returns:
            bool: 是否保存成功
        """
        try:
            container = self.docker_client.containers.get(self.container_name)
            
            if cleanup:
                print_colored("清理容器...", "yellow")
                if not self.cleanup_container():
                    print_colored("清理容器失败，继续保存", "yellow")
            
            print_colored(f"将容器保存为镜像 {image_name}...", "yellow")
            container.commit(repository=image_name.split(':')[0],
                           tag=image_name.split(':')[1] if ':' in image_name else 'latest')
            
            print_colored(f"容器已保存为镜像 {image_name}", "green")
            return True
            
        except Exception as e:
            logger.error(f"保存容器为镜像失败: {e}")
            return False
    
    def cleanup_container(self, paths: List[str] = None) -> bool:
        """
        清理容器内的缓存文件
        
        Args:
            paths: 要清理的路径列表，如果为None则使用默认路径
            
        Returns:
            bool: 是否清理成功
        """
        try:
            container = self.docker_client.containers.get(self.container_name)
            
            if not paths:
                paths = ['/tmp/*', '/var/cache/*']
            
            print_colored("清理容器缓存...", "yellow")
            for path in paths:
                try:
                    container.exec_run(f"rm -rf {path}")
                except Exception as e:
                    logger.error(f"清理路径 {path} 失败: {e}")
            
            print_colored("容器缓存清理完成", "green")
            return True
            
        except Exception as e:
            logger.error(f"清理容器失败: {e}")
            return False
    
    def schedule_backup(self, cron_expr: str, image_name: str = None,
                       cleanup: bool = False, auto_push: bool = False) -> bool:
        """
        设置定时备份任务
        
        Args:
            cron_expr: cron表达式
            image_name: 备份镜像名称，如果为None则使用容器名称加时间戳
            cleanup: 是否在备份前清理容器
            auto_push: 是否自动推送备份镜像
            
        Returns:
            bool: 是否设置成功
        """
        try:
            def backup_job():
                if not image_name:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{self.container_name}_backup_{timestamp}"
                else:
                    backup_name = image_name
                
                if self.save_as_image(backup_name, cleanup=cleanup):
                    if auto_push:
                        # 这里需要实现推送逻辑
                        pass
            
            # 解析cron表达式并设置定时任务
            schedule.every().day.at(cron_expr).do(backup_job)
            
            print_colored(f"已设置定时备份任务: {cron_expr}", "green")
            return True
            
        except Exception as e:
            logger.error(f"设置定时备份任务失败: {e}")
            return False 