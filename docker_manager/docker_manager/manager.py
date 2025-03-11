"""Docker镜像管理类"""

from typing import Optional, List, Dict, Any, Tuple

from .managers import (
    ProjectManager,
    EnvironmentManager,
    ContainerManager,
    BackupManager,
    ImageManager
)


class DockerImageManager:
    """Docker镜像管理类，用于管理多个项目的Docker镜像和容器
    
    该类提供了以下功能：
    1. 项目管理：添加、删除、配置项目
    2. 环境初始化：构建Docker镜像
    3. 容器管理：启动、停止、重启容器
    4. 镜像管理：保存容器状态、清理缓存、压缩镜像
    5. 备份管理：创建、列出、清理、恢复备份
    
    每个项目都有独立的配置，包括项目目录、镜像名称、容器名称等。
    """
    
    def __init__(self, project_name: str = None, config: Dict[str, Any] = None):
        """
        初始化Docker镜像管理器
        
        Args:
            project_name: 项目名称，如果提供则从项目配置文件加载
            config: 配置字典，如果为None则使用默认配置
        """
        # 初始化各个管理器
        self.project_manager = ProjectManager(project_name=project_name, config=config)
        self.environment_manager = EnvironmentManager(project_name=project_name, config=config)
        self.container_manager = ContainerManager(project_name=project_name, config=config)
        self.backup_manager = BackupManager(project_name=project_name, config=config)
        self.image_manager = ImageManager(project_name=project_name, config=config)
        
        # 从项目管理器获取基本信息
        self.project_name = self.project_manager.project_name
        self.config = self.project_manager.config
        self.project_dir = self.project_manager.project_dir
        self.image_name = self.project_manager.image_name
        self.container_name = self.project_manager.container_name
    
    # 项目管理方法
    @classmethod
    def list_projects(cls) -> List[str]:
        """
        列出所有已配置的项目
        
        Returns:
            项目名称列表
        """
        return ProjectManager.list_projects()
        
    @classmethod
    def create_project(cls, project_name: str, project_dir: str = None) -> 'DockerImageManager':
        """
        创建新项目
        
        Args:
            project_name: 项目名称
            project_dir: 项目目录路径，如果为None则使用项目名称作为目录名
            
        Returns:
            DockerImageManager实例
        """
        project_manager = ProjectManager.create_project(project_name, project_dir)
        return cls(project_name=project_name)
        
    @classmethod
    def delete_project(cls, project_name: str, delete_files: bool = False) -> bool:
        """
        删除项目
        
        Args:
            project_name: 项目名称
            delete_files: 是否同时删除项目文件
            
        Returns:
            是否成功
        """
        return ProjectManager.delete_project(project_name, delete_files)
        
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新项目配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            是否成功
        """
        success = self.project_manager.update_config(config_updates)
        if success:
            # 更新本地属性
            self.config = self.project_manager.config
            self.project_dir = self.project_manager.project_dir
            self.image_name = self.project_manager.image_name
            self.container_name = self.project_manager.container_name
        return success
    
    # 环境管理方法
    def detect_docker_compose_cmd(self) -> str:
        """
        检测Docker Compose命令
        
        Returns:
            Docker Compose命令
        """
        return self.environment_manager.detect_docker_compose_cmd()
    
    def check_daily_usage_phase(self) -> bool:
        """
        检查是否已进入日常使用阶段
        
        Returns:
            是否已进入日常使用阶段
        """
        return self.environment_manager.check_daily_usage_phase()
    
    def init_environment(self) -> bool:
        """
        初始化环境（构建Docker镜像）
        
        Returns:
            是否成功
        """
        return self.environment_manager.init_environment()
    
    def rebuild_base(self) -> bool:
        """
        重建Docker镜像
        
        Returns:
            是否成功
        """
        return self.environment_manager.rebuild_base()
    
    def clean_container(self) -> bool:
        """
        清理容器内的缓存文件
        
        Returns:
            是否成功
        """
        return self.environment_manager.clean_container()
    
    # 容器管理方法
    def save_container(self) -> bool:
        """
        保存容器状态并重启
        
        Returns:
            是否成功
        """
        return self.container_manager.save_container()
    
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
    
    # 备份管理方法
    def list_backups(self) -> bool:
        """
        列出所有备份镜像
        
        Returns:
            是否成功
        """
        return self.backup_manager.list_backups()
    
    def clean_backups(self) -> bool:
        """
        清理旧的备份镜像
        
        Returns:
            是否成功
        """
        return self.backup_manager.clean_backups()
    
    def restore_backup(self, tag: str = None) -> bool:
        """
        恢复到指定的备份镜像
        
        Args:
            tag: 备份标签，如果为None则提示用户选择
            
        Returns:
            是否成功
        """
        return self.backup_manager.restore_backup(tag)
    
    # 镜像管理方法
    def compress_image(self) -> bool:
        """
        通过导出/导入方式压缩镜像
        
        Returns:
            是否成功
        """
        return self.image_manager.compress_image() 