"""备份管理器类"""

import time
import docker
from typing import Dict, Any

from .base_manager import BaseManager
from ..logger import logger, print_colored
from ..utils import run_command, confirm_action, get_timestamp


class BackupManager(BaseManager):
    """备份管理器类，用于管理备份的创建、列出、清理和恢复"""
    
    def list_backups(self) -> bool:
        """
        列出所有备份镜像
        
        Returns:
            是否成功
        """
        print_colored("备份镜像列表：", "yellow")
        try:
            images = self.docker_client.images.list(
                name=f"{self.image_name}:backup_*"
            )
            
            if not images:
                print_colored("没有找到备份镜像", "yellow")
                return True
            
            # 打印表头
            print(f"{'镜像标签':<40} {'创建时间':<25} {'大小':<10}")
            print("-" * 75)
            
            # 打印镜像信息
            for image in images:
                # 获取标签
                tag = [t for t in image.tags if t.startswith(f"{self.image_name}:backup_")][0]
                
                # 获取创建时间
                created = image.attrs.get('Created', 'Unknown')
                if created != 'Unknown':
                    # 转换时间格式
                    from datetime import datetime
                    created_dt = datetime.strptime(created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取大小
                size = image.attrs.get('Size', 0)
                size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                
                print(f"{tag:<40} {created:<25} {size_str:<10}")
            
            return True
        except Exception as e:
            logger.error(f"列出备份镜像失败: {e}")
            return False
    
    def clean_backups(self) -> bool:
        """
        清理旧的备份镜像
        
        Returns:
            是否成功
        """
        # 先列出所有备份
        self.list_backups()
        
        print()
        print_colored("清理选项：", "yellow")
        print("1) 保留最新的N个备份")
        print("2) 删除特定的备份")
        print("3) 删除所有备份")
        print("4) 取消操作")
        
        option = input("请选择操作 [1-4]: ").strip()
        
        try:
            if option == "1":
                keep_count = input("保留最新的几个备份？ ").strip()
                try:
                    keep_count = int(keep_count)
                except ValueError:
                    print_colored("错误：请输入有效的数字", "red")
                    return False
                
                # 获取所有备份镜像，按创建时间排序
                images = self.docker_client.images.list(
                    name=f"{self.image_name}:backup_*"
                )
                
                # 按创建时间排序
                images.sort(key=lambda x: x.attrs.get('Created', ''), reverse=True)
                
                if len(images) <= keep_count:
                    print_colored(f"当前备份数量({len(images)})不超过要保留的数量({keep_count})，无需清理", "green")
                    return True
                
                # 删除旧的备份
                for i in range(keep_count, len(images)):
                    tag = [t for t in images[i].tags if t.startswith(f"{self.image_name}:backup_")][0]
                    print_colored(f"删除备份: {tag}", "yellow")
                    self.docker_client.images.remove(tag)
                
            elif option == "2":
                tag = input("请输入要删除的备份标签(例如 backup_20240601_120000): ").strip()
                full_tag = f"{self.image_name}:{tag}"
                
                try:
                    self.docker_client.images.get(full_tag)
                    print_colored(f"删除备份: {full_tag}", "yellow")
                    self.docker_client.images.remove(full_tag)
                except docker.errors.ImageNotFound:
                    print_colored(f"错误：找不到备份 {full_tag}", "red")
                    return False
                
            elif option == "3":
                if not confirm_action("确定要删除所有备份吗？这无法撤销！", False):
                    print_colored("操作已取消", "green")
                    return True
                
                print_colored("删除所有备份...", "yellow")
                images = self.docker_client.images.list(
                    name=f"{self.image_name}:backup_*"
                )
                
                for image in images:
                    tag = [t for t in image.tags if t.startswith(f"{self.image_name}:backup_")][0]
                    print_colored(f"删除备份: {tag}", "yellow")
                    self.docker_client.images.remove(tag)
                
            elif option == "4":
                print_colored("操作已取消", "green")
                return True
                
            else:
                print_colored("无效的选项", "red")
                return False
            
            print_colored("清理完成！", "green")
            return True
            
        except Exception as e:
            logger.error(f"清理备份失败: {e}")
            return False
    
    def restore_backup(self, tag: str = None) -> bool:
        """
        恢复到指定的备份镜像
        
        Args:
            tag: 备份标签，如果为None则提示用户选择
            
        Returns:
            是否成功
        """
        if tag is None:
            # 列出可用的备份镜像
            print_colored("可用的备份镜像：", "yellow")
            self.list_backups()
            
            tag = input("请输入要恢复的备份标签(例如 backup_20240601_120000): ").strip()
        
        full_tag = f"{self.image_name}:{tag}"
        
        # 检查备份是否存在
        try:
            self.docker_client.images.get(full_tag)
        except docker.errors.ImageNotFound:
            print_colored(f"错误：找不到备份 {full_tag}", "red")
            return False
        
        print_colored(f"将从备份 {full_tag} 恢复...", "yellow")
        if not confirm_action("这将覆盖当前的镜像，确定要继续吗？", False):
            print_colored("操作已取消", "green")
            return True
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        current_backup = f"{self.image_name}:pre_restore_{timestamp}"
        
        # 备份当前镜像
        print_colored(f"备份当前镜像为 {current_backup}...", "yellow")
        try:
            current_image = self.docker_client.images.get(f"{self.image_name}:latest")
            current_image.tag(current_backup)
        except Exception as e:
            logger.error(f"备份当前镜像失败: {e}")
            return False
        
        # 恢复备份镜像
        print_colored(f"恢复备份镜像 {full_tag}...", "yellow")
        try:
            backup_image = self.docker_client.images.get(full_tag)
            backup_image.tag(f"{self.image_name}:latest", force=True)
        except Exception as e:
            logger.error(f"恢复备份镜像失败: {e}")
            return False
        
        # 重启容器
        print_colored("重启容器...", "yellow")
        docker_compose_cmd = self.detect_docker_compose_cmd()
        
        try:
            run_command(f"{docker_compose_cmd} down", shell=True)
            run_command(f"{docker_compose_cmd} up -d", shell=True)
        except Exception as e:
            logger.error(f"重启容器失败: {e}")
            return False
        
        # 等待容器启动
        print_colored("等待容器启动...", "yellow")
        time.sleep(5)
        
        # 检查容器状态
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == "running":
                print_colored("容器已成功重启！", "green")
                print_colored(f"已恢复到备份 {full_tag}", "green")
                print_colored(f"之前的镜像已备份为 {current_backup}", "green")
                return True
            else:
                print_colored("容器可能未正常启动，请检查日志：", "yellow")
                run_command(f"{docker_compose_cmd} logs", shell=True)
                return False
        except docker.errors.NotFound:
            print_colored("容器未找到，请检查日志：", "yellow")
            run_command(f"{docker_compose_cmd} logs", shell=True)
            return False 