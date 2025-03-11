"""项目管理器类"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base_manager import BaseManager
from .image_manager import ImageManager
from .container_manager import ContainerManager
from ..logger import logger, print_colored
from ..utils import confirm_action

class ProjectConfigError(Exception):
    """项目配置错误"""
    pass

class ProjectOperationError(Exception):
    """项目操作错误"""
    pass

class ProjectManager(BaseManager):
    """项目管理器类，用于管理项目配置和资源"""
    
    REQUIRED_CONFIG_FIELDS = {
        'project': {
            'name': str,
            'directory': str
        },
        'image': {
            'name': str,
            'dockerfile': str,
            'registry': {
                'url': str,
                'username': str,
                'password': str
            }
        },
        'container': {
            'name': str,
            'compose_file': str,
            'cleanup': {
                'paths': list
            },
            'backup': {
                'schedule': str,
                'cleanup': bool,
                'auto_push': bool
            }
        }
    }
    
    def __init__(self, project_name: str):
        """
        初始化项目管理器
        
        Args:
            project_name: 项目名称
        """
        super().__init__()
        self.project_name = project_name
        self.project_dir = None
        self.config = {}
        self.image_manager = None
        self.container_manager = None
        
    def create_project(self, project_dir: str) -> bool:
        """
        创建新项目
        
        Args:
            project_dir: 项目目录路径
            
        Returns:
            bool: 是否创建成功
        """
        try:
            # 验证目录
            project_dir = os.path.abspath(project_dir)
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # 初始化配置
            self.project_dir = project_dir
            self.config = {
                'project': {
                    'name': self.project_name,
                    'directory': project_dir
                },
                'image': {
                    'name': f"{self.project_name}:latest",
                    'dockerfile': 'Dockerfile',
                    'registry': {
                        'url': 'docker.io',
                        'username': '',
                        'password': ''
                    }
                },
                'container': {
                    'name': self.project_name,
                    'compose_file': 'docker-compose.yml',
                    'cleanup': {
                        'paths': ['/tmp/*', '/var/cache/*']
                    },
                    'backup': {
                        'schedule': '',
                        'cleanup': False,
                        'auto_push': False
                    }
                }
            }
            
            # 保存配置
            self._save_config()
            
            # 初始化管理器
            self._init_managers()
            
            print_colored(f"项目 '{self.project_name}' 创建成功", "green")
            return True
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            return False
    
    def load_project(self) -> bool:
        """
        加载项目配置
        
        Returns:
            bool: 是否加载成功
        """
        try:
            config_file = os.path.join(self.project_dir, 'config.json')
            if not os.path.exists(config_file):
                raise ProjectConfigError(f"项目配置文件不存在: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self._validate_config()
            self._init_managers()
            
            return True
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            return False
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新项目配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 更新配置
            for section, values in config_updates.items():
                if section in self.config:
                    self.config[section].update(values)
            
            # 验证新配置
            self._validate_config()
            
            # 保存配置
            self._save_config()
            
            # 重新初始化管理器
            self._init_managers()
            
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def cleanup_resources(self) -> bool:
        """
        清理项目资源
        
        Returns:
            bool: 是否清理成功
        """
        try:
            if self.container_manager:
                self.container_manager.cleanup_container()
            return True
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
            return False
    
    def _validate_config(self):
        """验证配置的完整性和正确性"""
        try:
            self._validate_config_structure(self.config, self.REQUIRED_CONFIG_FIELDS)
            self._validate_paths()
        except Exception as e:
            raise ProjectConfigError(f"配置验证失败: {str(e)}")
    
    def _validate_config_structure(self, config: Dict, required: Dict):
        """递归验证配置结构"""
        for key, value_type in required.items():
            if key not in config:
                raise ProjectConfigError(f"缺少必需的配置项: {key}")
            
            if isinstance(value_type, dict):
                if not isinstance(config[key], dict):
                    raise ProjectConfigError(f"配置项类型错误: {key} 应为字典")
                self._validate_config_structure(config[key], value_type)
            elif not isinstance(config[key], value_type):
                raise ProjectConfigError(f"配置项类型错误: {key} 应为 {value_type.__name__}")
    
    def _validate_paths(self):
        """验证配置中的路径"""
        project_dir = Path(self.config['project']['directory'])
        if not project_dir.exists():
            raise ProjectConfigError(f"项目目录不存在: {project_dir}")
        
        dockerfile = project_dir / self.config['image']['dockerfile']
        if not dockerfile.exists():
            raise ProjectConfigError(f"Dockerfile不存在: {dockerfile}")
        
        compose_file = project_dir / self.config['container']['compose_file']
        if not compose_file.exists():
            raise ProjectConfigError(f"Docker Compose文件不存在: {compose_file}")
    
    def _save_config(self):
        """保存配置到文件"""
        config_file = os.path.join(self.project_dir, 'config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_managers(self):
        """初始化镜像和容器管理器"""
        image_config = self.config['image']
        container_config = self.config['container']
        
        self.image_manager = ImageManager(
            project_dir=self.project_dir,
            image_name=image_config['name']
        )
        
        self.container_manager = ContainerManager(
            project_dir=self.project_dir,
            container_name=container_config['name']
        ) 