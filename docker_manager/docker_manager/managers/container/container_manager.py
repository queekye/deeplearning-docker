"""容器管理器类"""

import os
import time
import docker
from typing import List, Dict, Any, Optional

from ..base_container_manager import BaseContainerManager
from ...logger import logger, print_colored
from ...utils import run_command, confirm_action, get_timestamp
from ...config import (
    load_container_config, list_containers, create_container_config, 
    update_container_config, delete_container_config
)


class ContainerManager(BaseContainerManager):
    """容器管理器类，用于管理容器的创建、启动、停止和重启"""
    
    @classmethod
    def list_containers(cls) -> List[str]:
        """
        列出所有已配置的容器
        
        Returns:
            容器名称列表
        """
        return list_containers()
    
    @classmethod
    def create_container(cls, container_name: str, image_name: str, compose_file: str = None) -> 'ContainerManager':
        """
        创建新容器配置
        
        Args:
            container_name: 容器名称
            image_name: 镜像名称
            compose_file: Docker Compose文件路径，如果为None则不使用
            
        Returns:
            ContainerManager实例
        """
        # 创建容器配置
        create_container_config(container_name, image_name, compose_file)
        
        # 返回管理器实例
        return cls(container_name=container_name)
    
    @classmethod
    def delete_container(cls, container_name: str, delete_container: bool = False) -> bool:
        """
        删除容器配置
        
        Args:
            container_name: 容器名称
            delete_container: 是否同时删除Docker容器
            
        Returns:
            是否成功
        """
        # 加载容器配置
        try:
            config = load_container_config(container_name=container_name)
        except FileNotFoundError:
            print_colored(f"容器 {container_name} 不存在", "red")
            return False
        
        # 删除Docker容器
        if delete_container:
            try:
                docker_client = docker.from_env()
                try:
                    container = docker_client.containers.get(container_name)
                    if confirm_action(f"确定要删除容器 {container_name} 吗？", False):
                        container.remove(force=True)
                        print_colored(f"已删除容器: {container_name}", "yellow")
                except docker.errors.NotFound:
                    print_colored(f"容器 {container_name} 不存在，只删除配置", "yellow")
            except Exception as e:
                logger.error(f"删除容器失败: {e}")
        
        # 删除容器配置
        return delete_container_config(container_name)
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新容器配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            是否成功
        """
        # 更新配置文件
        success = update_container_config(self.container_name, config_updates)
        
        if success:
            # 重新加载配置
            self.load_container(container_name=self.container_name)
        
        return success
    
    def start_container(self) -> bool:
        """
        启动容器
        
        Returns:
            是否成功
        """
        # 检查容器是否已经在运行
        try:
            container = self.get_container()
            if container.status == "running":
                print_colored("容器已经在运行中", "yellow")
                return True
        except ValueError:
            # 容器不存在，尝试使用Docker Compose启动
            pass
        
        # 检查是否有Docker Compose配置
        if 'compose' in self.config and 'file_path' in self.config['compose']:
            compose_file = self.config['compose']['file_path']
            if os.path.exists(compose_file):
                print_colored(f"使用Docker Compose启动容器...", "yellow")
                docker_compose_cmd = self.detect_docker_compose_cmd(compose_file)
                
                try:
                    run_command(f"{docker_compose_cmd} up -d", shell=True)
                except Exception as e:
                    logger.error(f"启动容器失败: {e}")
                    return False
                
                # 等待容器启动
                print_colored("等待容器启动...", "yellow")
                time.sleep(5)
                
                # 检查容器状态
                try:
                    container = self.get_container()
                    if container.status == "running":
                        print_colored("容器已成功启动！", "green")
                        return True
                    else:
                        print_colored("容器启动失败，请检查日志", "red")
                        run_command(f"{docker_compose_cmd} logs", shell=True)
                        return False
                except ValueError:
                    print_colored("容器启动失败，请检查日志", "red")
                    run_command(f"{docker_compose_cmd} logs", shell=True)
                    return False
        else:
            # 使用Docker SDK启动容器
            print_colored(f"使用Docker SDK启动容器...", "yellow")
            try:
                # 检查镜像是否存在
                try:
                    self.docker_client.images.get(self.image_name)
                except docker.errors.ImageNotFound:
                    print_colored(f"镜像 {self.image_name} 不存在，请先构建或拉取镜像", "red")
                    return False
                
                # 创建并启动容器
                container = self.docker_client.containers.run(
                    self.image_name,
                    name=self.container_name,
                    detach=True
                )
                
                print_colored(f"容器已成功启动: {container.name}", "green")
                return True
            except Exception as e:
                logger.error(f"启动容器失败: {e}")
                return False
    
    def stop_container(self) -> bool:
        """
        停止容器
        
        Returns:
            是否成功
        """
        # 检查容器是否在运行
        try:
            container = self.get_container()
            if container.status != "running":
                print_colored("容器未在运行", "yellow")
                return True
        except ValueError:
            print_colored("容器未在运行", "yellow")
            return True
        
        # 检查是否有Docker Compose配置
        if 'compose' in self.config and 'file_path' in self.config['compose']:
            compose_file = self.config['compose']['file_path']
            if os.path.exists(compose_file):
                print_colored(f"使用Docker Compose停止容器...", "yellow")
                docker_compose_cmd = self.detect_docker_compose_cmd(compose_file)
                
                try:
                    run_command(f"{docker_compose_cmd} down", shell=True)
                    print_colored("容器已停止", "green")
                    return True
                except Exception as e:
                    logger.error(f"停止容器失败: {e}")
                    return False
        else:
            # 使用Docker SDK停止容器
            print_colored(f"停止容器 {self.container_name}...", "yellow")
            try:
                container = self.get_container()
                container.stop()
                print_colored("容器已停止", "green")
                return True
            except Exception as e:
                logger.error(f"停止容器失败: {e}")
                return False
    
    def restart_container(self) -> bool:
        """
        重启容器
        
        Returns:
            是否成功
        """
        # 检查是否有Docker Compose配置
        if 'compose' in self.config and 'file_path' in self.config['compose']:
            compose_file = self.config['compose']['file_path']
            if os.path.exists(compose_file):
                print_colored(f"使用Docker Compose重启容器...", "yellow")
                docker_compose_cmd = self.detect_docker_compose_cmd(compose_file)
                
                try:
                    run_command(f"{docker_compose_cmd} down", shell=True)
                    run_command(f"{docker_compose_cmd} up -d", shell=True)
                except Exception as e:
                    logger.error(f"重启容器失败: {e}")
                    return False
                
                # 等待容器启动
                print_colored("等待容器启动...", "yellow")
                time.sleep(5)
                
                # 检查容器状态
                try:
                    container = self.get_container()
                    if container.status == "running":
                        print_colored("容器已成功重启！", "green")
                        return True
                    else:
                        print_colored("容器启动失败，请检查日志", "red")
                        run_command(f"{docker_compose_cmd} logs", shell=True)
                        return False
                except ValueError:
                    print_colored("容器启动失败，请检查日志", "red")
                    run_command(f"{docker_compose_cmd} logs", shell=True)
                    return False
        else:
            # 使用Docker SDK重启容器
            print_colored(f"重启容器 {self.container_name}...", "yellow")
            try:
                container = self.get_container()
                container.restart()
                print_colored("容器已成功重启！", "green")
                return True
            except Exception as e:
                logger.error(f"重启容器失败: {e}")
                return False
    
    def view_logs(self) -> bool:
        """
        查看容器日志
        
        Returns:
            是否成功
        """
        # 检查是否有Docker Compose配置
        if 'compose' in self.config and 'file_path' in self.config['compose']:
            compose_file = self.config['compose']['file_path']
            if os.path.exists(compose_file):
                print_colored(f"使用Docker Compose查看日志...", "yellow")
                docker_compose_cmd = self.detect_docker_compose_cmd(compose_file)
                
                try:
                    run_command(f"{docker_compose_cmd} logs", shell=True)
                    return True
                except Exception as e:
                    logger.error(f"查看日志失败: {e}")
                    return False
        else:
            # 使用Docker SDK查看日志
            print_colored(f"查看容器 {self.container_name} 的日志...", "yellow")
            try:
                container = self.get_container()
                logs = container.logs().decode('utf-8')
                print(logs)
                return True
            except Exception as e:
                logger.error(f"查看日志失败: {e}")
                return False
    
    def save_container(self) -> bool:
        """
        保存容器状态为新镜像
        
        Returns:
            是否成功
        """
        # 检查容器是否存在
        try:
            container = self.get_container()
        except ValueError:
            print_colored(f"容器 {self.container_name} 不存在", "red")
            print_colored(f"请先启动容器：docker_manager container start {self.container_name}", "yellow")
            return False
        
        # 检查容器是否运行
        if container.status != "running":
            print_colored(f"容器 {self.container_name} 未运行", "red")
            print_colored(f"请先启动容器：docker_manager container start {self.container_name}", "yellow")
            return False
        
        # 询问是否先清理容器
        if confirm_action("是否先清理容器内的缓存文件以减小镜像大小？", False):
            from .clean_manager import CleanManager
            clean_manager = CleanManager(container_name=self.container_name)
            clean_manager.clean_container()
        
        print_colored("正在保存当前容器状态为新镜像...", "yellow")
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        image_base_name = self.image_name.split(':')[0]  # 移除标签部分
        new_image_name = f"{image_base_name}:latest"
        backup_image_name = f"{image_base_name}:backup_{timestamp}"
        
        # 将当前镜像标记为备份
        print_colored(f"备份当前镜像为 {backup_image_name}...", "yellow")
        try:
            current_image = self.docker_client.images.get(new_image_name)
            current_image.tag(backup_image_name)
        except Exception as e:
            logger.error(f"备份当前镜像失败: {e}")
            return False
        
        # 提交当前容器为新镜像
        print_colored("提交当前容器为新镜像...", "yellow")
        try:
            container.commit(repository=image_base_name, tag="latest")
        except Exception as e:
            logger.error(f"提交容器失败: {e}")
            return False
        
        # 重启容器
        print_colored("重启容器...", "yellow")
        if not self.restart_container():
            return False
        
        print_colored("容器状态已成功保存为新镜像！", "green")
        print_colored(f"新镜像已保存为 {new_image_name}", "green")
        print_colored(f"旧镜像已备份为 {backup_image_name}", "green")
        
        return True 