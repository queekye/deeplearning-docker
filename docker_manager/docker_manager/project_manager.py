"""项目管理主类"""

from typing import List, Dict, Any, Optional

from .managers.project import ProjectManager, ImageManager


class DockerProjectManager:
    """Docker项目管理器，用于管理项目和镜像"""
    
    def __init__(self, project_name: str = None, config: Dict[str, Any] = None):
        """
        初始化Docker项目管理器
        
        Args:
            project_name: 项目名称，如果提供则从项目配置文件加载
            config: 配置字典，如果为None则使用默认配置
        """
        self.project_manager = ProjectManager(project_name=project_name, config=config)
        self.image_manager = ImageManager(project_name=project_name, config=config)
        
        # 从项目管理器获取基本信息
        self.project_name = self.project_manager.project_name
        self.config = self.project_manager.config
        self.project_dir = self.project_manager.project_dir
        self.image_name = self.project_manager.image_name
    
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
    def create_project(cls, project_name: str, project_dir: str = None) -> 'DockerProjectManager':
        """
        创建新项目
        
        Args:
            project_name: 项目名称
            project_dir: 项目目录路径，如果为None则使用项目名称作为目录名
            
        Returns:
            DockerProjectManager实例
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
        return success
    
    # 镜像管理方法
    def build_image(self, nocache: bool = False, build_args: Dict[str, str] = None) -> bool:
        """
        构建Docker镜像
        
        Args:
            nocache: 是否禁用缓存
            build_args: 构建参数
            
        Returns:
            是否成功
        """
        return self.image_manager.build_image(nocache, build_args)
    
    def tag_image(self, source_tag: str = "latest", target_tag: str = None) -> bool:
        """
        为镜像添加标签
        
        Args:
            source_tag: 源标签
            target_tag: 目标标签，如果为None则使用时间戳
            
        Returns:
            是否成功
        """
        return self.image_manager.tag_image(source_tag, target_tag)
    
    def push_image(self, tag: str = "latest") -> bool:
        """
        推送镜像到远程仓库
        
        Args:
            tag: 镜像标签
            
        Returns:
            是否成功
        """
        return self.image_manager.push_image(tag)
    
    def list_images(self) -> List[Dict[str, Any]]:
        """
        列出项目的所有镜像
        
        Returns:
            镜像列表，每个镜像包含标签、创建时间和大小信息
        """
        return self.image_manager.list_images()
    
    def delete_image(self, tag: str, force: bool = False) -> bool:
        """
        删除镜像
        
        Args:
            tag: 镜像标签
            force: 是否强制删除
            
        Returns:
            是否成功
        """
        return self.image_manager.delete_image(tag, force)
    
    def compress_image(self, tag: str = "latest") -> bool:
        """
        通过导出/导入方式压缩镜像
        
        Args:
            tag: 镜像标签
            
        Returns:
            是否成功
        """
        return self.image_manager.compress_image(tag) 