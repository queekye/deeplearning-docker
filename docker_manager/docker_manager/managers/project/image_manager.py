"""镜像管理器类"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional

from ..base_project_manager import BaseProjectManager
from ...logger import logger, print_colored
from ...utils import run_command, confirm_action, get_timestamp, create_temp_file


class ImageManager(BaseProjectManager):
    """镜像管理器类，用于管理镜像的构建、推送和压缩"""
    
    def build_image(self, nocache: bool = False, build_args: Dict[str, str] = None) -> bool:
        """
        构建Docker镜像
        
        Args:
            nocache: 是否禁用缓存
            build_args: 构建参数
            
        Returns:
            是否成功
        """
        if not self.project_dir or not os.path.exists(self.project_dir):
            print_colored(f"项目目录 {self.project_dir} 不存在", "red")
            return False
        
        print_colored(f"构建镜像 {self.image_name}...", "yellow")
        
        try:
            # 准备构建参数
            build_kwargs = {
                'path': self.project_dir,
                'tag': f"{self.image_name}:latest",
                'rm': True,  # 构建完成后删除中间容器
                'nocache': nocache
            }
            
            # 添加构建参数
            if build_args:
                build_kwargs['buildargs'] = build_args
            
            # 使用Docker SDK构建镜像
            build_result = self.docker_client.images.build(**build_kwargs)
            
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
                
            return True
        except Exception as e:
            logger.error(f"构建镜像失败: {e}")
            return False
    
    def tag_image(self, source_tag: str = "latest", target_tag: str = None) -> bool:
        """
        为镜像添加标签
        
        Args:
            source_tag: 源标签
            target_tag: 目标标签，如果为None则使用时间戳
            
        Returns:
            是否成功
        """
        if target_tag is None:
            # 使用时间戳作为标签
            target_tag = f"v{get_timestamp()}"
        
        source_image = f"{self.image_name}:{source_tag}"
        target_image = f"{self.image_name}:{target_tag}"
        
        print_colored(f"为镜像 {source_image} 添加标签 {target_image}...", "yellow")
        
        try:
            # 获取源镜像
            image = self.docker_client.images.get(source_image)
            
            # 添加标签
            image.tag(self.image_name, target_tag)
            
            print_colored(f"标签添加成功: {target_image}", "green")
            return True
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    def push_image(self, tag: str = "latest") -> bool:
        """
        推送镜像到远程仓库
        
        Args:
            tag: 镜像标签
            
        Returns:
            是否成功
        """
        # 检查推送配置
        if not self.push_config.get('registry') or not self.push_config.get('username'):
            print_colored("推送配置不完整，请先配置推送信息", "red")
            return False
        
        registry = self.push_config['registry']
        username = self.push_config['username']
        repository = self.push_config.get('repository') or self.image_name
        
        # 构建完整的镜像名称
        full_image_name = f"{registry}/{username}/{repository}:{tag}"
        
        print_colored(f"推送镜像 {self.image_name}:{tag} 到 {full_image_name}...", "yellow")
        
        try:
            # 获取源镜像
            image = self.docker_client.images.get(f"{self.image_name}:{tag}")
            
            # 添加远程标签
            image.tag(f"{registry}/{username}/{repository}", tag)
            
            # 推送镜像
            for line in self.docker_client.images.push(
                f"{registry}/{username}/{repository}", 
                tag=tag, 
                stream=True, 
                decode=True
            ):
                if 'status' in line:
                    print(f"{line['status']} {line.get('progress', '')}")
                elif 'error' in line:
                    print_colored(f"错误: {line['error']}", "red")
                    return False
            
            print_colored(f"镜像推送成功: {full_image_name}", "green")
            return True
        except Exception as e:
            logger.error(f"推送镜像失败: {e}")
            return False
    
    def list_images(self) -> List[Dict[str, Any]]:
        """
        列出项目的所有镜像
        
        Returns:
            镜像列表，每个镜像包含标签、创建时间和大小信息
        """
        images_info = []
        
        try:
            # 获取所有镜像
            images = self.docker_client.images.list(name=self.image_name)
            
            for image in images:
                # 过滤出属于当前项目的标签
                tags = [tag for tag in image.tags if tag.startswith(f"{self.image_name}:")]
                
                if not tags:
                    continue
                
                # 获取创建时间
                created = image.attrs.get('Created', 'Unknown')
                if created != 'Unknown':
                    # 转换时间格式
                    from datetime import datetime
                    created_dt = datetime.strptime(created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取大小
                size = image.attrs.get('Size', 0)
                size_gb = size / (1024 * 1024 * 1024)
                
                # 添加到结果列表
                images_info.append({
                    'id': image.id,
                    'tags': tags,
                    'created': created,
                    'size': size,
                    'size_str': f"{size_gb:.2f} GB"
                })
            
            return images_info
        except Exception as e:
            logger.error(f"列出镜像失败: {e}")
            return []
    
    def delete_image(self, tag: str, force: bool = False) -> bool:
        """
        删除镜像
        
        Args:
            tag: 镜像标签
            force: 是否强制删除
            
        Returns:
            是否成功
        """
        image_name = f"{self.image_name}:{tag}"
        
        print_colored(f"删除镜像 {image_name}...", "yellow")
        
        try:
            self.docker_client.images.remove(image_name, force=force)
            print_colored(f"镜像已删除: {image_name}", "green")
            return True
        except Exception as e:
            logger.error(f"删除镜像失败: {e}")
            return False
    
    def compress_image(self, tag: str = "latest") -> bool:
        """
        通过导出/导入方式压缩镜像
        
        Args:
            tag: 镜像标签
            
        Returns:
            是否成功
        """
        image_name = f"{self.image_name}:{tag}"
        
        print_colored(f"压缩镜像 {image_name}...", "yellow")
        print_colored("此过程可能需要较长时间，取决于镜像大小", "yellow")
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        backup_tag = f"backup_{timestamp}"
        
        # 备份当前镜像
        print_colored(f"备份当前镜像为 {self.image_name}:{backup_tag}...", "yellow")
        try:
            current_image = self.docker_client.images.get(image_name)
            current_image.tag(self.image_name, backup_tag)
        except Exception as e:
            logger.error(f"备份镜像失败: {e}")
            return False
        
        # 保存原始镜像的CMD和ENTRYPOINT
        print_colored("保存原始镜像的CMD和ENTRYPOINT...", "yellow")
        try:
            image_info = self.docker_client.images.get(image_name).attrs
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
            container = self.docker_client.containers.create(image_name)
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
            original_size = self.docker_client.images.get(image_name).attrs.get('Size', 0)
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
                compressed_image.tag(self.image_name, tag, force=True)
                
                # 删除压缩后的镜像标签
                self.docker_client.images.remove(f"{self.image_name}:compressed_with_metadata")
                
                print_colored("镜像压缩完成！", "green")
                print_colored(f"原镜像已备份为 {self.image_name}:{backup_tag}", "green")
                print_colored("CMD和ENTRYPOINT已成功恢复", "green")
                return True
            except Exception as e:
                logger.error(f"替换当前镜像失败: {e}")
                print_colored(f"压缩后的镜像仍然可用: {self.image_name}:compressed_with_metadata", "yellow")
                return False
        else:
            print_colored(f"保留压缩后的镜像为 {self.image_name}:compressed_with_metadata", "yellow")
            print_colored("您可以稍后手动使用它", "yellow")
            return True 