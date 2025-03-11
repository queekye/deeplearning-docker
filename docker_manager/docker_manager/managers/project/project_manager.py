"""项目管理器类"""

import os
import shutil
from typing import List, Dict, Any, Optional

from ..base_project_manager import BaseProjectManager
from ...logger import logger, print_colored
from ...utils import confirm_action
from ...config import (
    load_project_config, list_projects, create_project_config, 
    update_project_config, delete_project_config, get_projects_dir
)


class ProjectManager(BaseProjectManager):
    """项目管理器类，用于管理项目的创建、删除和配置"""
    
    @classmethod
    def list_projects(cls) -> List[str]:
        """
        列出所有已配置的项目
        
        Returns:
            项目名称列表
        """
        return list_projects()
        
    @classmethod
    def create_project(cls, project_name: str, project_dir: str = None) -> 'ProjectManager':
        """
        创建新项目
        
        Args:
            project_name: 项目名称
            project_dir: 项目目录路径，如果为None则使用项目名称作为目录名
            
        Returns:
            ProjectManager实例
        """
        if project_dir is None:
            # 使用项目名称作为目录名
            project_dir = os.path.join(get_projects_dir(), project_name)
        
        # 确保项目目录存在
        os.makedirs(project_dir, exist_ok=True)
        
        # 创建项目配置
        create_project_config(project_name, project_dir)
        
        # 返回管理器实例
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
        # 加载项目配置
        try:
            config = load_project_config(project_name=project_name)
        except FileNotFoundError:
            print_colored(f"项目 {project_name} 不存在", "red")
            return False
        
        # 删除项目文件
        if delete_files and confirm_action(f"确定要删除项目 {project_name} 的所有文件吗？", False):
            project_dir = config['project_dir']
            if os.path.exists(project_dir):
                try:
                    shutil.rmtree(project_dir)
                    print_colored(f"已删除项目目录: {project_dir}", "yellow")
                except Exception as e:
                    logger.error(f"删除项目目录失败: {e}")
        
        # 删除项目配置
        return delete_project_config(project_name)
        
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新项目配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            是否成功
        """
        # 更新配置文件
        success = update_project_config(self.project_name, config_updates)
        
        if success:
            # 重新加载配置
            self.load_project(project_name=self.project_name)
        
        return success 