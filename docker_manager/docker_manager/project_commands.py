"""项目管理命令模块"""

import os
import sys
import typer
from typing import Optional, List
from pathlib import Path

from .managers.project_manager import ProjectManager
from .logger import logger, print_colored
from .config import get_projects_dir, load_config
from .cli_utils import get_current_project

# 创建项目管理子命令
project_app = typer.Typer(
    name="project",
    help="项目管理命令",
    add_completion=False
)


@project_app.command("list")
def list_projects():
    """列出所有已配置的项目"""
    projects = DockerProjectManager.list_projects()
    
    if not projects:
        print_colored("没有找到已配置的项目", "yellow")
        print_colored("使用 'docker_manager project add <项目目录>' 添加项目", "yellow")
        return
    
    print_colored("已配置的项目：", "green")
    for project in projects:
        try:
            config = load_config(project_name=project)
            project_dir = config.get('project_dir', '未知')
            image_name = config.get('image_name', '未知')
            print(f"  - {project}")
            print(f"    目录: {project_dir}")
            print(f"    镜像: {image_name}")
        except Exception:
            print(f"  - {project} (配置加载失败)")
    
    print()
    print_colored("使用方法:", "cyan")
    print_colored("  docker_manager -p <项目名称> <命令>", "cyan")
    print_colored("例如:", "cyan")
    print_colored("  docker_manager -p my_project init", "cyan")


@project_app.command("add")
def add_project(
    project_dir: str = typer.Argument(..., help="项目目录路径"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="项目名称，默认使用目录名"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="交互式配置项目")
):
    """添加新项目"""
    # 确保项目目录存在
    project_dir = os.path.abspath(project_dir)
    if not os.path.exists(project_dir):
        print_colored(f"错误：项目目录不存在: {project_dir}", "red")
        print_colored("请先创建项目目录", "yellow")
        sys.exit(1)
    
    # 如果未指定名称，使用目录名
    if name is None:
        name = os.path.basename(project_dir)
    
    # 检查项目名称是否已存在
    projects = DockerProjectManager.list_projects()
    if name in projects:
        print_colored(f"错误：项目 {name} 已存在", "red")
        print_colored("请使用其他名称或删除现有项目", "yellow")
        sys.exit(1)
    
    # 检查项目目录是否包含必要的文件
    docker_compose_file = os.path.join(project_dir, "docker-compose.yml")
    dockerfile = os.path.join(project_dir, "Dockerfile")
    
    if not os.path.exists(docker_compose_file):
        print_colored(f"警告：未找到 docker-compose.yml 文件: {docker_compose_file}", "yellow")
        if not typer.confirm("是否继续？"):
            sys.exit(1)
    
    if not os.path.exists(dockerfile):
        print_colored(f"警告：未找到 Dockerfile 文件: {dockerfile}", "yellow")
        if not typer.confirm("是否继续？"):
            sys.exit(1)
    
    # 创建项目
    try:
        manager = DockerProjectManager.create_project(name, project_dir)
        print_colored(f"项目 {name} 已成功添加", "green")
        print_colored(f"项目目录: {project_dir}", "green")
        
        # 交互式配置
        if interactive:
            configure_project_interactive(name)
        else:
            print_colored("您可以使用以下命令初始化环境：", "yellow")
            print_colored(f"docker_manager -p {name} init", "yellow")
    except Exception as e:
        logger.error(f"添加项目失败: {e}")
        sys.exit(1)


def configure_project_interactive(project_name: str):
    """交互式配置项目"""
    print_colored(f"\n开始交互式配置项目 {project_name}...", "green")
    
    # 加载项目管理器
    manager = DockerProjectManager(project_name=project_name)
    
    # 配置更新字典
    config_updates = {}
    
    # 配置镜像和容器名称
    print_colored("\n配置镜像和容器名称", "blue")
    image_name = typer.prompt(f"镜像名称 (默认: {manager.image_name})", default=manager.image_name)
    container_name = typer.prompt(f"容器名称 (默认: {manager.container_name})", default=manager.container_name)
    
    if image_name != manager.image_name:
        config_updates['image_name'] = image_name
    
    if container_name != manager.container_name:
        config_updates['container_name'] = container_name
    
    # 配置清理目录
    print_colored("\n配置清理目录", "blue")
    print_colored("当前要清理的目录:", "yellow")
    for directory in manager.cleanup_dirs:
        print(f"  - {directory}")
    
    if typer.confirm("是否修改要清理的目录？"):
        cleanup_dirs = []
        print_colored("输入要清理的目录，每行一个，输入空行结束:", "yellow")
        while True:
            directory = input("> ").strip()
            if not directory:
                break
            cleanup_dirs.append(directory)
        
        if cleanup_dirs:
            if 'cleanup' not in config_updates:
                config_updates['cleanup'] = {}
            config_updates['cleanup']['directories'] = cleanup_dirs
    
    # 配置排除目录
    print_colored("\n配置不清理的目录", "blue")
    print_colored("当前不清理的目录:", "yellow")
    for directory in manager.exclude_dirs:
        print(f"  - {directory}")
    
    if typer.confirm("是否修改不清理的目录？"):
        exclude_dirs = []
        print_colored("输入不清理的目录，每行一个，输入空行结束:", "yellow")
        while True:
            directory = input("> ").strip()
            if not directory:
                break
            exclude_dirs.append(directory)
        
        if exclude_dirs:
            if 'cleanup' not in config_updates:
                config_updates['cleanup'] = {}
            config_updates['cleanup']['exclude_directories'] = exclude_dirs
    
    # 配置定时任务
    print_colored("\n配置定时任务", "blue")
    enable_cron = typer.confirm("是否启用定时任务？", default=manager.cron_config['enabled'])
    
    if enable_cron:
        cron_schedule = typer.prompt(
            "定时任务计划 (cron格式，例如 '0 0 * * *' 表示每天午夜)",
            default=manager.cron_config['schedule']
        )
        auto_clean = typer.confirm("是否在定时任务中自动清理容器？", default=manager.cron_config['auto_clean'])
        auto_push = typer.confirm("是否在定时任务中自动推送镜像？", default=manager.cron_config['auto_push'])
        max_backups = typer.prompt(
            "最大备份数量",
            default=manager.cron_config['max_backups'],
            type=int
        )
        
        if 'cron' not in config_updates:
            config_updates['cron'] = {}
        
        config_updates['cron']['enabled'] = enable_cron
        config_updates['cron']['schedule'] = cron_schedule
        config_updates['cron']['auto_clean'] = auto_clean
        config_updates['cron']['auto_push'] = auto_push
        config_updates['cron']['max_backups'] = max_backups
    elif not manager.cron_config['enabled']:
        # 如果原来就是禁用的，不需要更新
        pass
    else:
        # 禁用定时任务
        if 'cron' not in config_updates:
            config_updates['cron'] = {}
        config_updates['cron']['enabled'] = False
    
    # 配置镜像推送
    if enable_cron and auto_push:
        print_colored("\n配置镜像推送", "blue")
        registry = typer.prompt("镜像仓库地址", default=manager.push_config['registry'])
        username = typer.prompt("用户名", default=manager.push_config['username'])
        repository = typer.prompt("仓库名称", default=manager.push_config['repository'] or image_name)
        push_base_image = typer.confirm("是否同时推送基础镜像？", default=manager.push_config['push_base_image'])
        
        if 'push' not in config_updates:
            config_updates['push'] = {}
        
        config_updates['push']['registry'] = registry
        config_updates['push']['username'] = username
        config_updates['push']['repository'] = repository
        config_updates['push']['auto_push'] = True
        config_updates['push']['push_base_image'] = push_base_image
    
    # 更新配置
    if config_updates:
        success = manager.update_config(config_updates)
        
        if success:
            print_colored(f"\n项目 {project_name} 的配置已更新", "green")
        else:
            print_colored(f"\n更新项目 {project_name} 的配置失败", "red")
            sys.exit(1)
    else:
        print_colored("\n没有配置更改", "yellow")
    
    # 询问是否初始化环境
    if typer.confirm("\n是否立即初始化环境？"):
        manager.init_environment()
    else:
        print_colored("\n您可以使用以下命令初始化环境：", "yellow")
        print_colored(f"docker_manager -p {project_name} init", "yellow")


@project_app.command("remove")
def remove_project(
    name: str = typer.Argument(..., help="要删除的项目名称"),
    delete_files: bool = typer.Option(False, "--delete-files", "-d", help="同时删除项目文件")
):
    """删除项目"""
    # 检查项目是否存在
    projects = DockerProjectManager.list_projects()
    if name not in projects:
        print_colored(f"错误：项目 {name} 不存在", "red")
        sys.exit(1)
    
    # 确认删除
    if not typer.confirm(f"确定要删除项目 {name} 吗？"):
        print_colored("操作已取消", "green")
        return
    
    # 删除项目
    try:
        success = DockerProjectManager.delete_project(name, delete_files)
        if success:
            print_colored(f"项目 {name} 已成功删除", "green")
        else:
            print_colored(f"删除项目 {name} 失败", "red")
            sys.exit(1)
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        sys.exit(1)


@project_app.command("config")
def configure_project(
    name: str = typer.Argument(..., help="要配置的项目名称"),
    cleanup_dirs: Optional[List[str]] = typer.Option(None, "--cleanup-dir", help="要清理的目录"),
    exclude_dirs: Optional[List[str]] = typer.Option(None, "--exclude-dir", help="不清理的目录"),
    cron_schedule: Optional[str] = typer.Option(None, "--cron-schedule", help="定时任务计划"),
    max_backups: Optional[int] = typer.Option(None, "--max-backups", help="最大备份数量"),
    auto_clean: Optional[bool] = typer.Option(None, "--auto-clean/--no-auto-clean", help="是否自动清理"),
    auto_push: Optional[bool] = typer.Option(None, "--auto-push/--no-auto-push", help="是否自动推送")
):
    """配置项目"""
    # 检查项目是否存在
    projects = DockerProjectManager.list_projects()
    if name not in projects:
        print_colored(f"错误：项目 {name} 不存在", "red")
        sys.exit(1)
    
    # 创建配置更新字典
    config_updates = {}
    
    # 更新清理目录
    if cleanup_dirs is not None:
        if 'cleanup' not in config_updates:
            config_updates['cleanup'] = {}
        config_updates['cleanup']['directories'] = cleanup_dirs
    
    # 更新排除目录
    if exclude_dirs is not None:
        if 'cleanup' not in config_updates:
            config_updates['cleanup'] = {}
        config_updates['cleanup']['exclude_directories'] = exclude_dirs
    
    # 更新定时任务配置
    if cron_schedule is not None or max_backups is not None or auto_clean is not None or auto_push is not None:
        if 'cron' not in config_updates:
            config_updates['cron'] = {}
        
        if cron_schedule is not None:
            config_updates['cron']['schedule'] = cron_schedule
        
        if max_backups is not None:
            config_updates['cron']['max_backups'] = max_backups
        
        if auto_clean is not None:
            config_updates['cron']['auto_clean'] = auto_clean
        
        if auto_push is not None:
            config_updates['cron']['auto_push'] = auto_push
    
    # 如果没有更新，显示当前配置
    if not config_updates:
        manager = DockerProjectManager(project_name=name)
        print_colored(f"项目 {name} 的当前配置：", "green")
        print(f"项目目录: {manager.project_dir}")
        print(f"镜像名称: {manager.image_name}")
        print(f"容器名称: {manager.container_name}")
        print(f"Docker Compose 文件: {manager.compose_file}")
        
        print("\n清理配置:")
        print("要清理的目录:")
        for directory in manager.cleanup_dirs:
            print(f"  - {directory}")
        
        print("\n不清理的目录:")
        for directory in manager.exclude_dirs:
            print(f"  - {directory}")
        
        print("\n定时任务配置:")
        print(f"启用: {manager.cron_config['enabled']}")
        print(f"计划: {manager.cron_config['schedule']}")
        print(f"自动清理: {manager.cron_config['auto_clean']}")
        print(f"自动推送: {manager.cron_config['auto_push']}")
        print(f"最大备份数量: {manager.cron_config['max_backups']}")
        
        print("\n使用以下命令修改配置:")
        print(f"  docker_manager project config {name} --cleanup-dir <目录> --exclude-dir <目录> --cron-schedule <计划> --max-backups <数量> --auto-clean/--no-auto-clean --auto-push/--no-auto-push")
        
        return
    
    # 更新配置
    try:
        manager = DockerProjectManager(project_name=name)
        success = manager.update_config(config_updates)
        
        if success:
            print_colored(f"项目 {name} 的配置已更新", "green")
        else:
            print_colored(f"更新项目 {name} 的配置失败", "red")
            sys.exit(1)
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        sys.exit(1) 