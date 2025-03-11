"""镜像操作相关命令模块"""

import sys
import typer
from typing import Optional

from .cli_utils import get_project_manager

# 创建镜像操作命令组
image_app = typer.Typer(
    name="image",
    help="镜像操作命令",
    add_completion=False
)


@image_app.command("build")
def build_image():
    """构建Docker镜像"""
    manager = get_project_manager()
    success = manager.build_image()
    if not success:
        sys.exit(1)


@image_app.command("rebuild")
def rebuild_image():
    """重建Docker镜像"""
    manager = get_project_manager()
    success = manager.rebuild_image()
    if not success:
        sys.exit(1)


@image_app.command("push")
def push_image():
    """推送Docker镜像到远程仓库"""
    manager = get_project_manager()
    success = manager.push_image()
    if not success:
        sys.exit(1)


@image_app.command("compress")
def compress_image():
    """压缩Docker镜像以减小大小"""
    manager = get_project_manager()
    success = manager.compress_image()
    if not success:
        sys.exit(1)


@image_app.command("list")
def list_images():
    """列出所有项目镜像"""
    manager = get_project_manager()
    success = manager.list_images()
    if not success:
        sys.exit(1) 