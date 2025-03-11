"""清理管理器类"""

import docker
from typing import Dict, Any, List, Optional

from ..base_container_manager import BaseContainerManager
from ...logger import logger, print_colored


class CleanManager(BaseContainerManager):
    """清理管理器类，用于清理容器内的缓存文件"""
    
    def clean_container(self) -> bool:
        """
        清理容器内的缓存文件
        
        Returns:
            是否成功
        """
        # 检查容器是否存在
        try:
            container = self.get_container()
        except ValueError:
            print_colored(f"容器 {self.container_name} 不存在", "red")
            print_colored(f"请先启动容器：docker_manager container start {self.container_name}", "yellow")
            return False
        
        # 检查容器是否运行
        if container.status != "running":
            print_colored(f"容器 {self.container_name} 未运行", "red")
            print_colored(f"请先启动容器：docker_manager container start {self.container_name}", "yellow")
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