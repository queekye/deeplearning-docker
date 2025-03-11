"""容器管理主类"""

from typing import List, Dict, Any, Optional

from .managers.container import ContainerManager, BackupManager, CleanManager


class DockerContainerManager:
    """Docker容器管理器，用于管理容器、备份和清理"""
    
    def __init__(self, container_name: str = None, config: Dict[str, Any] = None):
        """
        初始化Docker容器管理器
        
        Args:
            container_name: 容器名称，如果提供则从容器配置文件加载
            config: 配置字典，如果为None则使用默认配置
        """
        self.container_manager = ContainerManager(container_name=container_name, config=config)
        self.backup_manager = BackupManager(container_name=container_name, config=config)
        self.clean_manager = CleanManager(container_name=container_name, config=config)
        
        # 从容器管理器获取基本信息
        self.container_name = self.container_manager.container_name
        self.config = self.container_manager.config
        self.image_name = self.container_manager.image_name
    
    # 容器管理方法
    @classmethod
    def list_containers(cls) -> List[str]:
        """
        列出所有已配置的容器
        
        Returns:
            容器名称列表
        """
        return ContainerManager.list_containers()
    
    @classmethod
    def create_container(cls, container_name: str, image_name: str, compose_file: str = None) -> 'DockerContainerManager':
        """
        创建新容器配置
        
        Args:
            container_name: 容器名称
            image_name: 镜像名称
            compose_file: Docker Compose文件路径，如果为None则不使用
            
        Returns:
            DockerContainerManager实例
        """
        container_manager = ContainerManager.create_container(container_name, image_name, compose_file)
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
        return ContainerManager.delete_container(container_name, delete_container)
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新容器配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            是否成功
        """
        success = self.container_manager.update_config(config_updates)
        if success:
            # 更新本地属性
            self.config = self.container_manager.config
            self.image_name = self.container_manager.image_name
        return success
    
    def start_container(self) -> bool:
        """
        启动容器
        
        Returns:
            是否成功
        """
        return self.container_manager.start_container()
    
    def stop_container(self) -> bool:
        """
        停止容器
        
        Returns:
            是否成功
        """
        return self.container_manager.stop_container()
    
    def restart_container(self) -> bool:
        """
        重启容器
        
        Returns:
            是否成功
        """
        return self.container_manager.restart_container()
    
    def view_logs(self) -> bool:
        """
        查看容器日志
        
        Returns:
            是否成功
        """
        return self.container_manager.view_logs()
    
    def save_container(self) -> bool:
        """
        保存容器状态为新镜像
        
        Returns:
            是否成功
        """
        return self.container_manager.save_container()
    
    # 备份管理方法
    def list_backups(self) -> bool:
        """
        列出所有备份镜像
        
        Returns:
            是否成功
        """
        return self.backup_manager.list_backups()
    
    def create_backup(self) -> bool:
        """
        创建备份
        
        Returns:
            是否成功
        """
        return self.backup_manager.create_backup()
    
    def restore_backup(self, backup_index: int = None) -> bool:
        """
        恢复到指定的备份镜像
        
        Args:
            backup_index: 备份序号，如果为None则提示用户选择
            
        Returns:
            是否成功
        """
        return self.backup_manager.restore_backup(backup_index)
    
    def clean_backups(self) -> bool:
        """
        清理旧的备份镜像
        
        Returns:
            是否成功
        """
        return self.backup_manager.clean_backups()
    
    # 清理管理方法
    def clean_container(self) -> bool:
        """
        清理容器内的缓存文件
        
        Returns:
            是否成功
        """
        return self.clean_manager.clean_container() 