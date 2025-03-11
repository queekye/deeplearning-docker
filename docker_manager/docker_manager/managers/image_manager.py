"""镜像管理器类"""

import os
import json
import subprocess
import docker
from typing import Dict, Any, Optional
from pathlib import Path

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import run_command, confirm_action, get_timestamp, create_temp_file


class ImageBuildError(Exception):
    """镜像构建错误"""
    pass

class ImagePushError(Exception):
    """镜像推送错误"""
    pass

class ImageManager(BaseManager):
    """镜像管理器类，用于构建和推送镜像"""
    
    def __init__(self, project_dir: str, image_name: str):
        """
        初始化镜像管理器
        
        Args:
            project_dir: 项目目录路径
            image_name: 镜像名称
        """
        super().__init__()
        self.project_dir = Path(project_dir)
        self.image_name = image_name
        
    def compress_image(self) -> bool:
        """
        通过导出/导入方式压缩镜像
        
        Returns:
            是否成功
        """
        # 检查容器是否存在
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == "running":
                print_colored(f"容器 {self.container_name} 正在运行", "red")
                print_colored(f"请先停止容器：docker_manager -p {self.project_name} stop", "yellow")
                return False
        except docker.errors.NotFound:
            # 容器不存在，可以继续
            pass
        
        # 检查jq是否已安装
        try:
            run_command("which jq", shell=True)
        except subprocess.CalledProcessError:
            print_colored("警告：未检测到jq命令，需要安装jq才能继续", "yellow")
            
            # 尝试安装jq
            try:
                # 检查系统类型
                if os.path.exists("/etc/debian_version"):
                    print_colored("使用apt-get安装jq...", "yellow")
                    run_command("apt-get update && apt-get install -y jq", shell=True)
                elif os.path.exists("/etc/redhat-release"):
                    print_colored("使用yum安装jq...", "yellow")
                    run_command("yum install -y jq", shell=True)
                elif os.path.exists("/etc/alpine-release"):
                    print_colored("使用apk安装jq...", "yellow")
                    run_command("apk add --no-cache jq", shell=True)
                else:
                    print_colored("错误：无法自动安装jq", "red")
                    print_colored("请手动安装jq后再试：", "yellow")
                    print_colored("  - Debian/Ubuntu: sudo apt-get install jq", "yellow")
                    print_colored("  - CentOS/RHEL: sudo yum install jq", "yellow")
                    print_colored("  - Alpine: sudo apk add jq", "yellow")
                    return False
                
                # 再次检查jq是否已安装
                run_command("which jq", shell=True)
                print_colored("jq安装成功，继续执行...", "green")
            except subprocess.CalledProcessError:
                print_colored("jq安装失败，无法继续", "red")
                return False
        
        print_colored("开始压缩镜像...", "yellow")
        print_colored("此过程可能需要较长时间，取决于镜像大小", "yellow")
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        backup_image_name = f"{self.image_name}:backup_{timestamp}"
        
        # 备份当前镜像
        print_colored(f"备份当前镜像为 {backup_image_name}...", "yellow")
        try:
            current_image = self.docker_client.images.get(f"{self.image_name}:latest")
            current_image.tag(backup_image_name)
        except Exception as e:
            logger.error(f"备份镜像失败: {e}")
            return False
        
        # 保存原始镜像的CMD和ENTRYPOINT
        print_colored("保存原始镜像的CMD和ENTRYPOINT...", "yellow")
        try:
            image_info = self.docker_client.images.get(f"{self.image_name}:latest").attrs
            original_cmd = json.dumps(image_info.get('Config', {}).get('Cmd', []))
            original_entrypoint = json.dumps(image_info.get('Config', {}).get('Entrypoint', []))
            original_workdir = image_info.get('Config', {}).get('WorkingDir', '/workspace')
            original_env = json.dumps(image_info.get('Config', {}).get('Env', []))
            
            print_colored(f"原始CMD: {original_cmd}", "yellow")
            print_colored(f"原始ENTRYPOINT: {original_entrypoint}", "yellow")
            print_colored(f"原始WORKDIR: {original_workdir}", "yellow")
        except Exception as e:
            logger.error(f"获取镜像信息失败: {e}")
            return False
        
        # 创建临时容器
        print_colored("创建临时容器...", "yellow")
        container = None
        try:
            container = self.docker_client.containers.create(f"{self.image_name}:latest")
            container_id = container.id
        except Exception as e:
            logger.error(f"创建临时容器失败: {e}")
            return False
        
        # 导出并重新导入容器
        print_colored("导出并重新导入容器（这将压缩镜像并移除历史层）...", "yellow")
        print_colored("请耐心等待，此过程可能需要几分钟到几十分钟...", "yellow")
        
        try:
            # 使用管道直接导出并导入
            export_cmd = f"docker export {container_id} | docker import - {self.image_name}:compressed"
            run_command(export_cmd, shell=True)
        except Exception as e:
            logger.error(f"导出/导入容器失败: {e}")
            # 清理临时容器
            if container:
                try:
                    container.remove(force=True)
                except Exception as cleanup_error:
                    logger.error(f"清理临时容器失败: {cleanup_error}")
            return False
        
        # 删除临时容器
        if container:
            try:
                container.remove(force=True)
            except Exception as e:
                logger.error(f"删除临时容器失败: {e}")
                # 即使删除失败也继续执行
        
        # 恢复CMD和ENTRYPOINT
        print_colored("恢复CMD和ENTRYPOINT...", "yellow")
        
        # 创建临时Dockerfile
        dockerfile_content = f"""FROM {self.image_name}:compressed
WORKDIR {original_workdir}
"""
        
        # 添加ENV
        if original_env != "null" and original_env != "[]":
            print_colored("恢复环境变量...", "yellow")
            # 将JSON格式的环境变量转换为Dockerfile格式
            env_vars = json.loads(original_env)
            for env_var in env_vars:
                dockerfile_content += f"ENV {env_var}\n"
        
        # 添加CMD
        if original_cmd != "null" and original_cmd != "[]":
            print_colored("恢复CMD...", "yellow")
            dockerfile_content += f"CMD {original_cmd}\n"
        else:
            print_colored("设置默认CMD...", "yellow")
            dockerfile_content += 'CMD ["/start_service.sh"]\n'
        
        # 添加ENTRYPOINT
        if original_entrypoint != "null" and original_entrypoint != "[]":
            print_colored("恢复ENTRYPOINT...", "yellow")
            dockerfile_content += f"ENTRYPOINT {original_entrypoint}\n"
        else:
            print_colored("设置默认ENTRYPOINT...", "yellow")
            dockerfile_content += 'ENTRYPOINT ["/bin/bash", "-c"]\n'
        
        # 创建临时Dockerfile
        dockerfile_path = create_temp_file(dockerfile_content)
        
        # 使用临时Dockerfile构建最终镜像
        print_colored("使用临时Dockerfile构建最终镜像...", "yellow")
        try:
            self.docker_client.images.build(
                path=os.path.dirname(dockerfile_path),
                dockerfile=dockerfile_path,
                tag=f"{self.image_name}:compressed_with_metadata"
            )
        except Exception as e:
            logger.error(f"构建最终镜像失败: {e}")
            # 清理中间镜像
            try:
                self.docker_client.images.remove(f"{self.image_name}:compressed")
            except:
                pass
            # 删除临时Dockerfile
            try:
                os.remove(dockerfile_path)
            except:
                pass
            return False
        
        # 删除临时Dockerfile
        try:
            os.remove(dockerfile_path)
        except Exception as e:
            logger.error(f"删除临时Dockerfile失败: {e}")
        
        # 删除中间镜像
        try:
            self.docker_client.images.remove(f"{self.image_name}:compressed")
        except Exception as e:
            logger.error(f"删除中间镜像失败: {e}")
        
        # 显示压缩前后的大小对比
        print_colored("压缩前后的镜像大小对比:", "yellow")
        try:
            original_size = self.docker_client.images.get(f"{self.image_name}:latest").attrs.get('Size', 0)
            compressed_size = self.docker_client.images.get(f"{self.image_name}:compressed_with_metadata").attrs.get('Size', 0)
            
            original_size_gb = original_size / (1024 * 1024 * 1024)
            compressed_size_gb = compressed_size / (1024 * 1024 * 1024)
            
            print_colored(f"原始镜像: {original_size_gb:.2f} GB", "yellow")
            print_colored(f"压缩后的镜像: {compressed_size_gb:.2f} GB", "yellow")
            print_colored(f"节省空间: {original_size_gb - compressed_size_gb:.2f} GB ({(1 - compressed_size / original_size) * 100:.2f}%)", "green")
        except Exception as e:
            logger.error(f"获取镜像大小失败: {e}")
        
        # 询问是否使用压缩后的镜像
        if confirm_action("是否使用压缩后的镜像替换当前镜像？", False):
            print_colored("替换当前镜像...", "yellow")
            try:
                compressed_image = self.docker_client.images.get(f"{self.image_name}:compressed_with_metadata")
                compressed_image.tag(f"{self.image_name}:latest", force=True)
                
                # 删除压缩后的镜像标签
                self.docker_client.images.remove(f"{self.image_name}:compressed_with_metadata")
                
                print_colored("镜像压缩完成！", "green")
                print_colored(f"原镜像已备份为 {backup_image_name}", "green")
                print_colored("CMD和ENTRYPOINT已成功恢复", "green")
                print_colored("您可以使用以下命令启动容器：", "yellow")
                print_colored(f"docker_manager -p {self.project_name} start", "yellow")
            except Exception as e:
                logger.error(f"替换当前镜像失败: {e}")
                print_colored(f"压缩后的镜像仍然可用: {self.image_name}:compressed_with_metadata", "yellow")
                return False
        else:
            print_colored(f"保留压缩后的镜像为 {self.image_name}:compressed_with_metadata", "yellow")
            print_colored("您可以稍后手动使用它", "yellow")
        
        return True 

    def build_image(self, dockerfile: str = 'Dockerfile', build_args: Dict[str, str] = None) -> bool:
        """
        构建Docker镜像
        
        Args:
            dockerfile: Dockerfile路径，相对于项目目录
            build_args: 构建参数
            
        Returns:
            bool: 是否构建成功
        """
        try:
            dockerfile_path = self.project_dir / dockerfile
            if not dockerfile_path.exists():
                raise ImageBuildError(f"Dockerfile不存在: {dockerfile_path}")
            
            print_colored(f"开始构建镜像 {self.image_name}...", "yellow")
            
            # 构建镜像
            try:
                self.docker_client.images.build(
                    path=str(self.project_dir),
                    dockerfile=str(dockerfile_path),
                    tag=self.image_name,
                    buildargs=build_args or {}
                )
                print_colored(f"镜像 {self.image_name} 构建成功", "green")
                return True
            except docker.errors.BuildError as e:
                logger.error(f"构建镜像失败: {e}")
                print_colored(f"构建日志:\n{e.build_log}", "red")
                return False
            
        except Exception as e:
            logger.error(f"构建镜像失败: {e}")
            return False
    
    def push_image(self, registry: str = None, username: str = None, password: str = None) -> bool:
        """
        推送镜像到远程仓库
        
        Args:
            registry: 远程仓库地址
            username: 用户名
            password: 密码
            
        Returns:
            bool: 是否推送成功
        """
        try:
            if registry:
                # 重新标记镜像
                new_tag = f"{registry}/{self.image_name}"
                image = self.docker_client.images.get(self.image_name)
                image.tag(new_tag)
                target_image = new_tag
            else:
                target_image = self.image_name
            
            # 登录仓库
            if username and password:
                try:
                    self.docker_client.login(
                        registry=registry,
                        username=username,
                        password=password
                    )
                except docker.errors.APIError as e:
                    raise ImagePushError(f"登录远程仓库失败: {e}")
            
            print_colored(f"开始推送镜像 {target_image}...", "yellow")
            
            # 推送镜像
            for line in self.docker_client.images.push(
                target_image,
                stream=True,
                decode=True
            ):
                if 'error' in line:
                    raise ImagePushError(line['error'])
                elif 'status' in line:
                    print_colored(line['status'], "yellow")
            
            print_colored(f"镜像 {target_image} 推送成功", "green")
            return True
            
        except Exception as e:
            logger.error(f"推送镜像失败: {e}")
            return False
    
    def tag_image(self, new_tag: str) -> bool:
        """
        为镜像添加新标签
        
        Args:
            new_tag: 新标签名称
            
        Returns:
            bool: 是否添加成功
        """
        try:
            image = self.docker_client.images.get(self.image_name)
            image.tag(new_tag)
            print_colored(f"已为镜像 {self.image_name} 添加标签 {new_tag}", "green")
            return True
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False 