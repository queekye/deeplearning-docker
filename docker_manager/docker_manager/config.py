"""配置加载模块"""

import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入 logger 模块，但避免循环导入
# 我们将在 load_config 函数中动态导入 logger 模块


def get_projects_dir() -> str:
    """
    获取项目目录的根目录
    
    Returns:
        项目根目录路径
    """
    # 默认使用 docker_projects 目录
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docker_projects"))


def get_config_dir() -> str:
    """
    获取配置文件目录
    
    Returns:
        配置文件目录路径
    """
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_projects_config_dir() -> str:
    """
    获取项目配置文件目录
    
    Returns:
        项目配置文件目录路径
    """
    config_dir = os.path.join(get_config_dir(), "projects")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_containers_config_dir() -> str:
    """
    获取容器配置文件目录
    
    Returns:
        容器配置文件目录路径
    """
    config_dir = os.path.join(get_config_dir(), "containers")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


# 为了向后兼容，保留原来的load_config函数
def load_config(project_name: str = None, config_path: str = None) -> Dict[str, Any]:
    """
    加载配置文件（向后兼容）
    
    Args:
        project_name: 项目名称，如果提供则从项目配置文件加载
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        配置字典
    """
    from .logger import logger
    logger.warning("load_config函数已弃用，请使用load_project_config或load_container_config")
    return load_project_config(project_name, config_path)


def load_project_config(project_name: str = None, config_path: str = None) -> Dict[str, Any]:
    """
    加载项目配置文件
    
    Args:
        project_name: 项目名称，如果提供则从项目配置文件加载
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        配置字典
    """
    if config_path is None and project_name is not None:
        # 使用项目名称查找配置文件
        config_path = os.path.join(get_projects_config_dir(), f"{project_name}.yaml")
        
        # 向后兼容：如果新路径不存在，尝试旧路径
        if not os.path.exists(config_path):
            old_path = os.path.join(get_config_dir(), f"{project_name}.yaml")
            if os.path.exists(old_path):
                # 迁移配置文件
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                shutil.copy2(old_path, config_path)
    elif config_path is None:
        # 返回空的默认配置
        from .logger import logger
        logger.warning("未指定项目名称或配置文件路径，返回空配置")
        return get_default_project_config()
    
    # 确保配置文件存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"项目配置文件不存在: {config_path}")
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 处理路径中的环境变量
    if 'project_dir' in config:
        config['project_dir'] = os.path.expandvars(config['project_dir'])
    
    if 'compose' in config and 'file_path' in config['compose']:
        # 替换${project_dir}为实际路径
        config['compose']['file_path'] = config['compose']['file_path'].replace(
            "${project_dir}", config['project_dir']
        )
    
    # 确保必要的配置项存在
    ensure_default_project_config(config)
    
    return config


def load_container_config(container_name: str = None, config_path: str = None) -> Dict[str, Any]:
    """
    加载容器配置文件
    
    Args:
        container_name: 容器名称，如果提供则从容器配置文件加载
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        配置字典
    """
    if config_path is None and container_name is not None:
        # 使用容器名称查找配置文件
        config_path = os.path.join(get_containers_config_dir(), f"{container_name}.yaml")
    elif config_path is None:
        # 返回空的默认配置
        from .logger import logger
        logger.warning("未指定容器名称或配置文件路径，返回空配置")
        return get_default_container_config()
    
    # 确保配置文件存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"容器配置文件不存在: {config_path}")
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 确保必要的配置项存在
    ensure_default_container_config(config)
    
    return config


def ensure_default_project_config(config: Dict[str, Any]) -> None:
    """
    确保项目配置中包含所有必要的默认值
    
    Args:
        config: 配置字典
    """
    # 推送配置
    if 'push' not in config:
        config['push'] = {
            'registry': 'docker.io',
            'username': '',
            'repository': '',
            'auto_push': False,
            'push_base_image': False,
            'additional_tags': []
        }


def ensure_default_container_config(config: Dict[str, Any]) -> None:
    """
    确保容器配置中包含所有必要的默认值
    
    Args:
        config: 配置字典
    """
    # 清理配置
    if 'cleanup' not in config:
        config['cleanup'] = {}
    
    # 默认清理目录
    if 'directories' not in config['cleanup']:
        config['cleanup']['directories'] = [
            '/var/cache/apt/',
            '/root/.cache/pip/',
            '/root/.cache/huggingface/',
            '/tmp/*',
            '/var/log/*.log',
            '/var/log/*.gz'
        ]
    
    # 默认保留目录（不清理）
    if 'exclude_directories' not in config['cleanup']:
        config['cleanup']['exclude_directories'] = [
            '/root/.cursor/',
            '/root/.config/cursor/',
            '/etc/ssh/',
            '/root/.ssh/',
            '/workspace/'
        ]
    
    # 定时任务配置
    if 'cron' not in config:
        config['cron'] = {
            'enabled': False,
            'schedule': '0 0 * * *',  # 默认每天午夜执行
            'auto_clean': True,
            'auto_push': False,
            'max_backups': 5
        }
    
    # 备份配置
    if 'backup' not in config:
        config['backup'] = {
            'max_backups': 5,
            'auto_backup': False,
            'backup_schedule': '0 0 * * *'  # 默认每天午夜执行
        }


# 为了向后兼容，保留原来的ensure_default_config函数
def ensure_default_config(config: Dict[str, Any]) -> None:
    """
    确保配置中包含所有必要的默认值（向后兼容）
    
    Args:
        config: 配置字典
    """
    ensure_default_project_config(config)
    ensure_default_container_config(config)


def list_projects() -> List[str]:
    """
    列出所有已配置的项目
    
    Returns:
        项目名称列表
    """
    projects_dir = get_projects_config_dir()
    projects = []
    
    if os.path.exists(projects_dir):
        for file in os.listdir(projects_dir):
            if file.endswith('.yaml'):
                projects.append(file[:-5])  # 移除 .yaml 后缀
    
    # 向后兼容：检查旧目录
    old_dir = get_config_dir()
    if os.path.exists(old_dir):
        for file in os.listdir(old_dir):
            if file.endswith('.yaml') and file[:-5] not in projects:
                projects.append(file[:-5])
    
    return projects


def list_containers() -> List[str]:
    """
    列出所有已配置的容器
    
    Returns:
        容器名称列表
    """
    containers_dir = get_containers_config_dir()
    containers = []
    
    if os.path.exists(containers_dir):
        for file in os.listdir(containers_dir):
            if file.endswith('.yaml'):
                containers.append(file[:-5])  # 移除 .yaml 后缀
    
    return containers


def create_project_config(project_name: str, project_dir: str) -> str:
    """
    创建新项目的配置文件
    
    Args:
        project_name: 项目名称
        project_dir: 项目目录路径
        
    Returns:
        配置文件路径
    """
    config_dir = get_projects_config_dir()
    config_path = os.path.join(config_dir, f"{project_name}.yaml")
    
    # 检查是否已存在
    if os.path.exists(config_path):
        return config_path
    
    # 创建基本配置
    config = {
        'project_name': project_name,
        'project_dir': project_dir,
        'image_name': project_name,
        'push': {
            'registry': 'docker.io',
            'username': '',
            'repository': '',
            'auto_push': False,
            'push_base_image': False,
            'additional_tags': []
        }
    }
    
    # 保存配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    return config_path


def create_container_config(container_name: str, image_name: str, compose_file: str = None) -> str:
    """
    创建新容器的配置文件
    
    Args:
        container_name: 容器名称
        image_name: 镜像名称
        compose_file: Docker Compose文件路径，如果为None则不使用
        
    Returns:
        配置文件路径
    """
    config_dir = get_containers_config_dir()
    config_path = os.path.join(config_dir, f"{container_name}.yaml")
    
    # 检查是否已存在
    if os.path.exists(config_path):
        return config_path
    
    # 创建基本配置
    config = {
        'container_name': container_name,
        'image_name': image_name,
        'cleanup': {
            'directories': [
                '/var/cache/apt/',
                '/root/.cache/pip/',
                '/root/.cache/huggingface/',
                '/tmp/*',
                '/var/log/*.log',
                '/var/log/*.gz'
            ],
            'exclude_directories': [
                '/root/.cursor/',
                '/root/.config/cursor/',
                '/etc/ssh/',
                '/root/.ssh/',
                '/workspace/'
            ]
        },
        'backup': {
            'max_backups': 5,
            'auto_backup': False,
            'backup_schedule': '0 0 * * *'  # 默认每天午夜执行
        },
        'cron': {
            'enabled': False,
            'schedule': '0 0 * * *',  # 默认每天午夜执行
            'auto_clean': True,
            'auto_push': False,
            'max_backups': 5
        }
    }
    
    # 如果提供了compose文件，添加到配置中
    if compose_file:
        config['compose'] = {
            'file_path': compose_file
        }
    
    # 保存配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    return config_path


def update_project_config(project_name: str, config_updates: Dict[str, Any]) -> bool:
    """
    更新项目配置
    
    Args:
        project_name: 项目名称
        config_updates: 要更新的配置项
        
    Returns:
        是否成功
    """
    config_path = os.path.join(get_projects_config_dir(), f"{project_name}.yaml")
    
    # 向后兼容：如果新路径不存在，尝试旧路径
    if not os.path.exists(config_path):
        old_path = os.path.join(get_config_dir(), f"{project_name}.yaml")
        if os.path.exists(old_path):
            # 迁移配置文件
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy2(old_path, config_path)
    
    if not os.path.exists(config_path):
        return False
    
    # 加载现有配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 递归更新配置
    def update_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = update_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    config = update_dict(config, config_updates)
    
    # 保存更新后的配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    return True


def update_container_config(container_name: str, config_updates: Dict[str, Any]) -> bool:
    """
    更新容器配置
    
    Args:
        container_name: 容器名称
        config_updates: 要更新的配置项
        
    Returns:
        是否成功
    """
    config_path = os.path.join(get_containers_config_dir(), f"{container_name}.yaml")
    
    if not os.path.exists(config_path):
        return False
    
    # 加载现有配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 递归更新配置
    def update_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = update_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    config = update_dict(config, config_updates)
    
    # 保存更新后的配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    return True


def delete_project_config(project_name: str) -> bool:
    """
    删除项目配置
    
    Args:
        project_name: 项目名称
        
    Returns:
        是否成功
    """
    config_path = os.path.join(get_projects_config_dir(), f"{project_name}.yaml")
    
    # 向后兼容：如果新路径不存在，尝试旧路径
    if not os.path.exists(config_path):
        old_path = os.path.join(get_config_dir(), f"{project_name}.yaml")
        if os.path.exists(old_path):
            os.remove(old_path)
            return True
        return False
    
    try:
        os.remove(config_path)
        return True
    except Exception:
        return False


def delete_container_config(container_name: str) -> bool:
    """
    删除容器配置
    
    Args:
        container_name: 容器名称
        
    Returns:
        是否成功
    """
    config_path = os.path.join(get_containers_config_dir(), f"{container_name}.yaml")
    
    if not os.path.exists(config_path):
        return False
    
    try:
        os.remove(config_path)
        return True
    except Exception:
        return False


def get_default_project_config() -> Dict[str, Any]:
    """
    获取默认项目配置
    
    Returns:
        默认配置字典
    """
    return {
        'project_name': 'default',
        'project_dir': '',
        'image_name': 'default',
        'push': {
            'registry': 'docker.io',
            'username': '',
            'repository': '',
            'auto_push': False,
            'push_base_image': False,
            'additional_tags': []
        }
    }


def get_default_container_config() -> Dict[str, Any]:
    """
    获取默认容器配置
    
    Returns:
        默认配置字典
    """
    return {
        'container_name': 'default',
        'image_name': 'default:latest',
        'cleanup': {
            'directories': [
                '/var/cache/apt/',
                '/root/.cache/pip/',
                '/root/.cache/huggingface/',
                '/tmp/*',
                '/var/log/*.log',
                '/var/log/*.gz'
            ],
            'exclude_directories': [
                '/root/.cursor/',
                '/root/.config/cursor/',
                '/etc/ssh/',
                '/root/.ssh/',
                '/workspace/'
            ]
        },
        'backup': {
            'max_backups': 5,
            'auto_backup': False,
            'backup_schedule': '0 0 * * *'
        },
        'cron': {
            'enabled': False,
            'schedule': '0 0 * * *',
            'auto_clean': True,
            'auto_push': False,
            'max_backups': 5
        }
    }


# 为了向后兼容，保留原来的get_default_config函数
def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置（向后兼容）
    
    Returns:
        默认配置字典
    """
    project_config = get_default_project_config()
    container_config = get_default_container_config()
    
    # 合并配置
    config = project_config.copy()
    config['container_name'] = container_config['container_name']
    config['cleanup'] = container_config['cleanup']
    config['cron'] = container_config['cron']
    
    return config 