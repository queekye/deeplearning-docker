# Docker项目和容器管理工具

一个用于管理多个Docker项目、镜像和容器的Python工具，特别适用于深度学习环境。

## 功能特点

- 管理多个Docker项目
- 构建和重建Docker镜像
- 管理容器的启动、停止和重启
- 保存容器状态并重启
- 清理容器内的缓存文件以减小镜像大小
- 备份和恢复容器
- 推送镜像到远程仓库
- 压缩镜像以减小大小
- 查看容器日志

## 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/docker_manager.git
cd docker_manager
pip install -e .
```

## 使用方法

### 项目管理

在使用其他功能前，必须先添加一个项目：

```bash
# 列出所有项目
docker_manager project list

# 添加新项目
docker_manager project add /path/to/project_directory --name my_project

# 交互式配置项目
docker_manager project add /path/to/project_directory -i

# 配置项目参数
docker_manager project config my_project --cleanup-dir cache --exclude-dir data --max-backups 5

# 删除项目
docker_manager project remove my_project
```

### 镜像管理

```bash
# 构建Docker镜像
docker_manager -p my_project image build

# 重建Docker镜像
docker_manager -p my_project image rebuild

# 推送Docker镜像到远程仓库
docker_manager -p my_project image push

# 压缩Docker镜像以减小大小
docker_manager -p my_project image compress

# 列出所有项目镜像
docker_manager -p my_project image list
```

### 容器管理

```bash
# 初始化环境（构建Docker镜像并创建容器）
docker_manager -p my_project container init

# 启动容器
docker_manager -p my_project container start

# 停止容器
docker_manager -p my_project container stop

# 重启容器
docker_manager -p my_project container restart

# 查看容器日志
docker_manager -p my_project container logs

# 清理容器内的缓存文件
docker_manager -p my_project container clean

# 保存当前容器状态为新镜像并重启
docker_manager -p my_project container save

# 备份当前容器状态
docker_manager -p my_project container backup

# 恢复到指定的备份镜像
docker_manager -p my_project container restore backup_20240601_120000

# 列出所有备份镜像
docker_manager -p my_project container list-backups

# 清理旧的备份镜像
docker_manager -p my_project container clean-backups
```

## 项目配置

每个项目都有独立的配置文件，可以通过交互式配置或命令行参数进行设置：

```yaml
# 项目配置
project:
  name: "my_project"
  directory: "/path/to/project_directory"

# 镜像配置
image:
  name: "my-project-image"
  tag: "latest"
  registry: "docker.io"
  username: "username"
  repository: "my-project"

# 容器配置
container:
  name: "my-project-container"
  ports:
    - "8888:8888"
  volumes:
    - "/host/path:/container/path"
  environment:
    - "VARIABLE=value"

# Docker Compose配置
compose:
  file_path: "${project.directory}/docker-compose.yml"

# 清理配置
cleanup:
  directories:
    - "cache"
    - "tmp"
  exclude_directories:
    - "data"
    - "models"

# 备份配置
backups:
  max_count: 5
  directory: "${project.directory}/backups"

# 定时任务配置
cron:
  enabled: true
  schedule: "0 0 * * *"
  auto_clean: true
  auto_push: false
  max_backups: 5

# 推送配置
push:
  registry: "docker.io"
  username: "username"
  repository: "my-project"
  auto_push: false
  push_base_image: false
```

## 使用阶段说明

1. **项目设置阶段**：使用`docker_manager project add`添加项目
2. **镜像构建阶段**：使用`docker_manager -p my_project image build`构建镜像
3. **容器初始化阶段**：使用`docker_manager -p my_project container init`初始化容器
4. **日常使用阶段**：使用`docker_manager -p my_project container save`保存状态并重启

> **重要**：一旦进入日常使用阶段（执行过save命令），就不应再使用init命令，否则会覆盖您保存的容器状态。容器管理工具会在执行可能覆盖容器状态的操作前给出警告。

## 许可证

MIT 