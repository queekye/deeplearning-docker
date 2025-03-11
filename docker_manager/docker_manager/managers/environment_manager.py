"""环境管理器类"""

from typing import Dict, Any

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import confirm_action


class EnvironmentManager(BaseManager):
    """环境管理器类，用于初始化和重建Docker环境"""
    
    def init_environment(self) -> bool:
        """
        初始化环境（构建Docker镜像）
        
        Returns:
            是否成功
        """
        # 检查是否已进入日常使用阶段
        if self.check_daily_usage_phase():
            print_colored("警告：检测到备份镜像存在！", "red")
            print_colored("您似乎已经进入日常使用阶段，执行初始化将覆盖您保存的容器状态。", "red")
            print_colored("推荐使用 save 命令来保存和重启容器。", "yellow")
            
            if not confirm_action("您确定要继续吗？这将覆盖您的容器状态！", False):
                print_colored("操作已取消。请使用 save 命令来保存和重启容器。", "green")
                return False
        
        print_colored("开始初始化环境...", "yellow")
        
        # 构建镜像
        print_colored("构建Docker镜像...", "yellow")
        try:
            # 使用Docker SDK构建镜像
            build_result = self.docker_client.images.build(
                path=self.project_dir,
                tag=f"{self.image_name}:latest",
                rm=True,  # 构建完成后删除中间容器
            )
            
            # 获取构建的镜像
            image = build_result[0]
            print_colored(f"镜像构建成功: {image.tags[0]}", "green")
            
            # 如果有构建日志，尝试显示
            try:
                for chunk in build_result[1]:
                    if isinstance(chunk, dict):
                        if 'stream' in chunk:
                            line = chunk['stream'].strip()
                            if line:
                                print(line)
                        elif 'error' in chunk:
                            print_colored(f"警告: {chunk['error']}", "yellow")
            except Exception as e:
                # 如果无法迭代构建日志，忽略错误
                logger.debug(f"无法显示构建日志: {e}")
        except Exception as e:
            logger.error(f"构建Docker镜像失败: {e}")
            return False
        
        print_colored("环境初始化完成！", "green")
        print_colored("您可以使用以下命令启动容器：", "yellow")
        print_colored(f"docker_manager -p {self.project_name} start", "yellow")
        
        return True
    
    def rebuild_base(self) -> bool:
        """
        重建Docker镜像
        
        Returns:
            是否成功
        """
        # 检查是否已进入日常使用阶段
        if self.check_daily_usage_phase():
            print_colored("警告：检测到备份镜像存在！", "red")
            print_colored("您似乎已经进入日常使用阶段，重建镜像可能会影响您的环境。", "red")
            
            if not confirm_action("您确定要继续吗？", False):
                print_colored("操作已取消。", "green")
                return False
        
        print_colored("重建Docker镜像...", "yellow")
        try:
            # 使用Docker SDK构建镜像
            build_result = self.docker_client.images.build(
                path=self.project_dir,
                tag=f"{self.image_name}:latest",
                nocache=True,
                rm=True,  # 构建完成后删除中间容器
            )
            
            # 获取构建的镜像
            image = build_result[0]
            print_colored(f"镜像重建成功: {image.tags[0]}", "green")
            
            # 如果有构建日志，尝试显示
            try:
                for chunk in build_result[1]:
                    if isinstance(chunk, dict):
                        if 'stream' in chunk:
                            line = chunk['stream'].strip()
                            if line:
                                print(line)
                        elif 'error' in chunk:
                            print_colored(f"警告: {chunk['error']}", "yellow")
            except Exception as e:
                # 如果无法迭代构建日志，忽略错误
                logger.debug(f"无法显示构建日志: {e}")
        except Exception as e:
            logger.error(f"重建Docker镜像失败: {e}")
            return False
        
        print_colored("Docker镜像重建完成！", "green")
        print_colored("您需要重启容器以应用更改：", "yellow")
        print_colored(f"docker_manager -p {self.project_name} restart", "yellow")
        
        return True
    
    def clean_container(self) -> bool:
        """
        清理容器内的缓存文件
        
        Returns:
            是否成功
        """
        # 检查容器是否存在
        try:
            container = self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            print_colored(f"容器 {self.container_name} 不存在", "red")
            print_colored(f"请先启动容器：docker_manager -p {self.project_name} start", "yellow")
            return False
        
        # 检查容器是否运行
        if container.status != "running":
            print_colored(f"容器 {self.container_name} 未运行", "red")
            print_colored(f"请先启动容器：docker_manager -p {self.project_name} start", "yellow")
            return False
        
        print_colored("正在清理容器内的缓存文件...", "yellow")
        
        # 构建清理脚本
        clean_script = """
        set -e
        echo '将要清理以下内容:'
        """
        
        # 添加要清理的目录
        for directory in self.cleanup_dirs:
            clean_script += f"echo '- {directory}'\n"
        
        clean_script += """
        echo
        
        echo '以下重要数据不会被清理:'
        """
        
        # 添加不清理的目录
        for directory in self.exclude_dirs:
            clean_script += f"echo '- {directory}'\n"
        
        clean_script += """
        echo
        """
        
        # 添加清理命令
        clean_script += """
        echo '清理APT缓存...'
        apt-get clean 2>/dev/null || echo '跳过apt-get clean (可能未安装)'
        
        echo '清理pip缓存...'
        rm -rf /root/.cache/pip 2>/dev/null || echo '跳过清理pip缓存'
        
        echo '清理Hugging Face缓存...'
        rm -rf /root/.cache/huggingface 2>/dev/null || echo '跳过清理Hugging Face缓存'
        
        echo '清理Jupyter缓存...'
        jupyter lab clean 2>/dev/null || echo '跳过jupyter lab clean (可能未安装)'
        jupyter cache clean 2>/dev/null || echo '跳过jupyter cache clean (可能未安装)'
        """
        
        # 添加自定义清理命令
        clean_script += """
        echo '清理系统缓存...'
        """
        
        # 为每个要清理的目录添加清理命令
        for directory in self.cleanup_dirs:
            # 跳过已经处理的特殊目录
            if directory in ['/var/cache/apt/', '/root/.cache/pip/', '/root/.cache/huggingface/']:
                continue
                
            # 检查是否是排除目录的子目录
            skip = False
            for exclude_dir in self.exclude_dirs:
                if directory.startswith(exclude_dir):
                    skip = True
                    break
                    
            if not skip:
                clean_script += f"""
        echo '清理 {directory}...'
        rm -rf {directory} 2>/dev/null || echo '跳过清理 {directory}'
        """
        
        clean_script += """
        echo '清理完成！'
        """
        
        # 执行清理脚本
        try:
            result = container.exec_run(
                cmd=["/bin/bash", "-c", clean_script],
                stdout=True,
                stderr=True
            )
            
            # 打印输出
            output = result.output.decode('utf-8')
            print(output)
            
            if result.exit_code != 0:
                print_colored(f"清理容器失败，退出代码: {result.exit_code}", "red")
                return False
                
            print_colored("容器清理完成！", "green")
            return True
        except Exception as e:
            logger.error(f"清理容器失败: {e}")
            return False 