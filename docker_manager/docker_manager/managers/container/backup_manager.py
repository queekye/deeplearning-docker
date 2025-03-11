"""备份管理器类"""

import time
import docker
from typing import Dict, Any, List, Optional

from ..base_container_manager import BaseContainerManager
from ...logger import logger, print_colored
from ...utils import run_command, confirm_action, get_timestamp


class BackupManager(BaseContainerManager):
    """备份管理器类，用于管理容器的备份和恢复"""
    
    def list_backups(self) -> bool:
        """
        列出所有备份镜像
        
        Returns:
            是否成功
        """
        print_colored("备份镜像列表：", "yellow")
        
        backups = super().list_backups()
        
        if not backups:
            print_colored("没有找到备份镜像", "yellow")
            return True
        
        # 打印表头
        print(f"{'镜像标签':<40} {'创建时间':<25} {'大小':<10}")
        print("-" * 75)
        
        # 打印镜像信息
        for backup in backups:
            print(f"{backup['tag']:<40} {backup['created']:<25} {backup['size_str']:<10}")
        
        return True
    
    def clean_backups(self) -> bool:
        """
        清理旧的备份镜像
        
        Returns:
            是否成功
        """
        # 先列出所有备份
        backups = super().list_backups()
        
        if not backups:
            print_colored("没有找到备份镜像", "yellow")
            return True
        
        # 打印备份列表
        print_colored("备份镜像列表：", "yellow")
        print(f"{'序号':<5} {'镜像标签':<40} {'创建时间':<25} {'大小':<10}")
        print("-" * 80)
        
        for i, backup in enumerate(backups):
            print(f"{i+1:<5} {backup['tag']:<40} {backup['created']:<25} {backup['size_str']:<10}")
        
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
                
                if len(backups) <= keep_count:
                    print_colored(f"当前备份数量({len(backups)})不超过要保留的数量({keep_count})，无需清理", "green")
                    return True
                
                # 删除旧的备份
                for i in range(keep_count, len(backups)):
                    tag = backups[i]['tag']
                    print_colored(f"删除备份: {tag}", "yellow")
                    try:
                        self.docker_client.images.remove(tag)
                    except Exception as e:
                        logger.error(f"删除备份失败: {e}")
                
            elif option == "2":
                backup_index = input("请输入要删除的备份序号: ").strip()
                try:
                    backup_index = int(backup_index) - 1
                    if backup_index < 0 or backup_index >= len(backups):
                        print_colored("错误：无效的备份序号", "red")
                        return False
                    
                    tag = backups[backup_index]['tag']
                    print_colored(f"删除备份: {tag}", "yellow")
                    self.docker_client.images.remove(tag)
                except ValueError:
                    print_colored("错误：请输入有效的数字", "red")
                    return False
                except Exception as e:
                    logger.error(f"删除备份失败: {e}")
                    return False
                
            elif option == "3":
                if not confirm_action("确定要删除所有备份吗？这无法撤销！", False):
                    print_colored("操作已取消", "green")
                    return True
                
                print_colored("删除所有备份...", "yellow")
                for backup in backups:
                    tag = backup['tag']
                    print_colored(f"删除备份: {tag}", "yellow")
                    try:
                        self.docker_client.images.remove(tag)
                    except Exception as e:
                        logger.error(f"删除备份失败: {e}")
                
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
    
    def create_backup(self) -> bool:
        """
        创建备份
        
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
        
        # 询问是否先清理容器
        if confirm_action("是否先清理容器内的缓存文件以减小备份大小？", False):
            from .clean_manager import CleanManager
            clean_manager = CleanManager(container_name=self.container_name)
            clean_manager.clean_container()
        
        print_colored("正在创建备份...", "yellow")
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        image_base_name = self.image_name.split(':')[0]  # 移除标签部分
        backup_tag = f"backup_{timestamp}"
        backup_image_name = f"{image_base_name}:{backup_tag}"
        
        # 提交当前容器为备份镜像
        print_colored(f"提交当前容器为备份镜像 {backup_image_name}...", "yellow")
        try:
            container.commit(repository=image_base_name, tag=backup_tag)
            print_colored(f"备份创建成功: {backup_image_name}", "green")
            return True
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False
    
    def restore_backup(self, backup_index: int = None) -> bool:
        """
        恢复到指定的备份镜像
        
        Args:
            backup_index: 备份序号，如果为None则提示用户选择
            
        Returns:
            是否成功
        """
        # 列出可用的备份镜像
        backups = super().list_backups()
        
        if not backups:
            print_colored("没有找到备份镜像", "red")
            return False
        
        # 打印备份列表
        print_colored("可用的备份镜像：", "yellow")
        print(f"{'序号':<5} {'镜像标签':<40} {'创建时间':<25} {'大小':<10}")
        print("-" * 80)
        
        for i, backup in enumerate(backups):
            print(f"{i+1:<5} {backup['tag']:<40} {backup['created']:<25} {backup['size_str']:<10}")
        
        # 如果未指定备份序号，提示用户选择
        if backup_index is None:
            backup_index = input("请输入要恢复的备份序号: ").strip()
            try:
                backup_index = int(backup_index) - 1
            except ValueError:
                print_colored("错误：请输入有效的数字", "red")
                return False
        else:
            backup_index -= 1  # 转换为0-based索引
        
        # 检查备份序号是否有效
        if backup_index < 0 or backup_index >= len(backups):
            print_colored("错误：无效的备份序号", "red")
            return False
        
        # 获取备份标签
        backup_tag = backups[backup_index]['tag']
        
        print_colored(f"将从备份 {backup_tag} 恢复...", "yellow")
        if not confirm_action("这将覆盖当前的镜像，确定要继续吗？", False):
            print_colored("操作已取消", "green")
            return True
        
        # 获取当前时间作为标签
        timestamp = get_timestamp()
        image_base_name = self.image_name.split(':')[0]  # 移除标签部分
        current_backup = f"{image_base_name}:pre_restore_{timestamp}"
        
        # 备份当前镜像
        print_colored(f"备份当前镜像为 {current_backup}...", "yellow")
        try:
            current_image = self.docker_client.images.get(f"{image_base_name}:latest")
            current_image.tag(current_backup)
        except Exception as e:
            logger.error(f"备份当前镜像失败: {e}")
            return False
        
        # 恢复备份镜像
        print_colored(f"恢复备份镜像 {backup_tag}...", "yellow")
        try:
            backup_image = self.docker_client.images.get(backup_tag)
            backup_image.tag(f"{image_base_name}:latest", force=True)
        except Exception as e:
            logger.error(f"恢复备份镜像失败: {e}")
            return False
        
        # 重启容器
        print_colored("重启容器...", "yellow")
        from .container_manager import ContainerManager
        container_manager = ContainerManager(container_name=self.container_name)
        if not container_manager.restart_container():
            return False
        
        print_colored("备份恢复成功！", "green")
        print_colored(f"已恢复到备份 {backup_tag}", "green")
        print_colored(f"之前的镜像已备份为 {current_backup}", "green")
        
        return True 