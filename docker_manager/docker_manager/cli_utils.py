"""CLI工具函数模块"""

import sys
import os
import re
import typer
from threading import Lock
from .logger import logger, print_colored
from .managers.project_manager import ProjectManager as DockerProjectManager
from .managers.container_manager import ContainerManager as DockerContainerManager

class ProjectContext:
    """项目上下文管理类"""
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self._project_name = None
        self._project_lock = Lock()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @property
    def project_name(self):
        """获取当前项目名称"""
        with self._project_lock:
            return self._project_name
    
    @project_name.setter
    def project_name(self, name):
        """设置当前项目名称"""
        if name is not None:
            self._validate_project_name(name)
        with self._project_lock:
            self._project_name = name
    
    @staticmethod
    def _validate_project_name(name):
        """验证项目名称的安全性"""
        if not name:
            raise ValueError("项目名称不能为空")
        
        # 检查项目名称格式
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("项目名称只能包含字母、数字、下划线和连字符")
        
        # 检查路径注入
        if '..' in name or '/' in name or '\\' in name:
            raise ValueError("项目名称包含非法字符")

def set_current_project(project_name):
    """设置当前项目名称"""
    try:
        ProjectContext.get_instance().project_name = project_name
    except ValueError as e:
        print_colored(f"错误：{str(e)}", "red")
        sys.exit(1)

def get_current_project():
    """获取当前项目名称"""
    return ProjectContext.get_instance().project_name

def check_project_specified():
    """检查是否指定了项目名称"""
    ctx = ProjectContext.get_instance()
    if ctx.project_name is None:
        print_colored("错误：未指定项目名称", "red")
        print_colored("请使用 --project 或 -p 选项指定项目名称", "yellow")
        print_colored("例如：docker_manager -p my_project project list", "yellow")
        print_colored("或者先添加项目：docker_manager project add <项目目录>", "yellow")
        sys.exit(1)
    
    try:
        # 检查项目是否存在
        projects = DockerProjectManager.list_projects()
        if ctx.project_name not in projects:
            print_colored(f"错误：项目 '{ctx.project_name}' 不存在", "red")
            print_colored("请使用 docker_manager project list 查看可用项目", "yellow")
            print_colored("或者使用 docker_manager project add <项目目录> 添加新项目", "yellow")
            sys.exit(1)
    except Exception as e:
        print_colored(f"错误：检查项目时发生异常 - {str(e)}", "red")
        logger.error(f"项目检查失败: {str(e)}")
        sys.exit(1)
    
    return True

def get_project_manager():
    """获取当前项目的项目管理器实例"""
    check_project_specified()
    try:
        return DockerProjectManager(project_name=ProjectContext.get_instance().project_name)
    except Exception as e:
        print_colored(f"错误：创建项目管理器失败 - {str(e)}", "red")
        logger.error(f"创建项目管理器失败: {str(e)}")
        sys.exit(1)

def get_container_manager():
    """获取当前项目的容器管理器实例"""
    check_project_specified()
    try:
        return DockerContainerManager(project_name=ProjectContext.get_instance().project_name)
    except Exception as e:
        print_colored(f"错误：创建容器管理器失败 - {str(e)}", "red")
        logger.error(f"创建容器管理器失败: {str(e)}")
        sys.exit(1) 