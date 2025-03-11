"""命令行接口主模块"""

import typer
import sys
from typing import Optional

from .logger import print_colored
from .cli_utils import set_current_project
from .project_commands import project_app
from .container_commands import container_app
from .image_commands import image_app
from .managers.project_manager import DockerProjectManager
from .managers.container_manager import DockerContainerManager

# 创建Typer应用
app = typer.Typer(
    name="docker_manager",
    help="Docker项目和容器管理工具",
    add_completion=False
)

# 添加子命令组
app.add_typer(project_app, name="project")
app.add_typer(container_app, name="container")
app.add_typer(image_app, name="image")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="指定要操作的项目名称")
):
    """Docker项目和容器管理工具，用于管理多个深度学习环境的Docker项目、镜像和容器"""
    set_current_project(project)
    
    # 如果没有子命令且没有指定项目，显示帮助信息
    if ctx.invoked_subcommand is None:
        projects = DockerProjectManager.list_projects()
        
        if not projects:
            print_colored("欢迎使用Docker项目和容器管理工具！", "green")
            print_colored("您还没有添加任何项目。", "yellow")
            print_colored("请先添加一个项目：", "yellow")
            print_colored("  docker_manager project add <项目目录>", "cyan")
            print()
            print_colored("查看帮助：", "yellow")
            print_colored("  docker_manager --help", "cyan")
        else:
            print_colored("欢迎使用Docker项目和容器管理工具！", "green")
            print_colored("您有以下项目：", "yellow")
            for project in projects:
                print(f"  - {project}")
            print()
            print_colored("使用子命令：", "yellow")
            print_colored("  docker_manager project <命令>", "cyan")
            print_colored("  docker_manager container <命令>", "cyan")
            print_colored("  docker_manager image <命令>", "cyan")
            print()
            print_colored("查看帮助：", "yellow")
            print_colored("  docker_manager --help", "cyan")


# 容器操作命令
@app.command("init")
def init_cmd():
    """初始化环境（构建Docker镜像）"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerProjectManager(project_name=project_name)
    success = manager.init_environment()
    if not success:
        sys.exit(1)


@app.command("start")
def start_cmd():
    """启动容器"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.start_container()
    if not success:
        sys.exit(1)


@app.command("stop")
def stop_cmd():
    """停止容器"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.stop_container()
    if not success:
        sys.exit(1)


@app.command("restart")
def restart_cmd():
    """重启容器"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.restart_container()
    if not success:
        sys.exit(1)


@app.command("logs")
def logs_cmd():
    """查看容器日志"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.view_logs()
    if not success:
        sys.exit(1)


@app.command("clean")
def clean_cmd():
    """清理容器内的缓存文件以减小镜像大小"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.clean_container()
    if not success:
        sys.exit(1)


# 镜像操作命令
@app.command("rebuild")
def rebuild_cmd():
    """重建Docker镜像"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerProjectManager(project_name=project_name)
    success = manager.rebuild_image()
    if not success:
        sys.exit(1)


@app.command("save")
def save_cmd():
    """保存当前容器状态为新镜像并重启"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.save_container()
    if not success:
        sys.exit(1)


@app.command("compress")
def compress_cmd():
    """压缩Docker镜像以减小大小"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerProjectManager(project_name=project_name)
    success = manager.compress_image()
    if not success:
        sys.exit(1)


@app.command("list-backups")
def list_backups_cmd():
    """列出所有备份镜像"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.list_backups()
    if not success:
        sys.exit(1)


@app.command("clean-backups")
def clean_backups_cmd():
    """清理旧的备份镜像"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.clean_backups()
    if not success:
        sys.exit(1)


@app.command("restore")
def restore_cmd(tag: Optional[str] = typer.Argument(None, help="要恢复的备份标签，例如 backup_20240601_120000")):
    """恢复到指定的备份镜像"""
    from .cli_utils import get_current_project, check_project_specified
    check_project_specified()
    project_name = get_current_project()
    manager = DockerContainerManager(project_name=project_name)
    success = manager.restore_backup(tag)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    app() 