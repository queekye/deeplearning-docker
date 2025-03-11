"""容器操作相关命令模块"""

import sys
import typer
from typing import Optional

from .cli_utils import get_container_manager

# 创建容器操作命令组
container_app = typer.Typer(
    name="container",
    help="容器操作命令",
    add_completion=False
)


@container_app.command("init")
def init_environment():
    """初始化环境（构建Docker镜像）"""
    manager = get_container_manager()
    success = manager.init_environment()
    if not success:
        sys.exit(1)


@container_app.command("start")
def start_container():
    """启动容器"""
    manager = get_container_manager()
    success = manager.start_container()
    if not success:
        sys.exit(1)


@container_app.command("stop")
def stop_container():
    """停止容器"""
    manager = get_container_manager()
    success = manager.stop_container()
    if not success:
        sys.exit(1)


@container_app.command("restart")
def restart_container():
    """重启容器"""
    manager = get_container_manager()
    success = manager.restart_container()
    if not success:
        sys.exit(1)


@container_app.command("logs")
def view_logs():
    """查看容器日志"""
    manager = get_container_manager()
    success = manager.view_logs()
    if not success:
        sys.exit(1)


@container_app.command("clean")
def clean_container():
    """清理容器内的缓存文件以减小镜像大小"""
    manager = get_container_manager()
    success = manager.clean_container()
    if not success:
        sys.exit(1)


@container_app.command("save")
def save_container():
    """保存当前容器状态为新镜像并重启"""
    manager = get_container_manager()
    success = manager.save_container()
    if not success:
        sys.exit(1)


@container_app.command("backup")
def backup_container():
    """备份当前容器状态"""
    manager = get_container_manager()
    success = manager.backup_container()
    if not success:
        sys.exit(1)


@container_app.command("restore")
def restore_container(tag: Optional[str] = typer.Argument(None, help="要恢复的备份标签，例如 backup_20240601_120000")):
    """恢复到指定的备份镜像"""
    manager = get_container_manager()
    success = manager.restore_backup(tag)
    if not success:
        sys.exit(1)


@container_app.command("list-backups")
def list_backups():
    """列出所有备份镜像"""
    manager = get_container_manager()
    success = manager.list_backups()
    if not success:
        sys.exit(1)


@container_app.command("clean-backups")
def clean_backups():
    """清理旧的备份镜像"""
    manager = get_container_manager()
    success = manager.clean_backups()
    if not success:
        sys.exit(1) 