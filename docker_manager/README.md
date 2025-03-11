# Docker项目和容器管理工具

一个用于管理Docker深度学习环境的Python工具，支持项目、镜像和容器的完整生命周期管理。

## 功能特点

- 简单易用的命令行接口
- 智能默认值和自动推断
- 交互式配置
- 自动化任务调度与管理
- 集中式常量配置
- 灵活的错误处理
- 常用定时方案快速选择

## 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/docker_manager.git
cd docker_manager
pip install -e .
```

## 快速开始

```bash
# 在当前目录创建项目（目录名作为项目名）
dm init

# 或指定项目目录和名称
dm init /path/to/project -n my_project

# 强制初始化（即使缺少必需文件）
dm init -f
```

## 命令参考

### 基础命令

```bash
# 创建项目（默认使用当前目录）
dm init [目录] [-n 名称] [-f 强制]

# 构建镜像（默认使用当前目录的Dockerfile）
dm build [-f Dockerfile文件] [-p 推送] [--build-arg KEY=VALUE]

# 启动容器（默认使用docker-compose.yml）
dm up [-f compose文件]

# 停止容器
dm down

# 保存容器状态
dm save [-t 标签] [-c 清理]

# 推送镜像到远程仓库
dm push [-r 仓库地址] [-u 用户名] [-p 密码] [-t 标签]
```

### 配置命令

```bash
# 交互式配置（支持tab补全）
dm config

# 快速设置常用配置
dm config registry docker.io
dm config username myname
```

### 定时任务管理

```bash
# 交互式配置定时任务（支持常用定时方案选择）
dm schedule

# 快速设置备份任务
dm schedule backup "0 0 * * *"

# 快速设置清理任务
dm schedule cleanup "0 0 * * *"

# 列出所有定时任务
dm schedule list

# 删除定时任务（交互式选择）
dm schedule remove

# 删除指定类型的定时任务
dm schedule remove backup
```

### 高级命令

```bash
# 构建并推送镜像
dm build -p

# 清理并保存容器
dm save -c

# 推送镜像到指定仓库
dm push -r registry.example.com -u username -p password

# 推送镜像并使用配置文件中的认证信息
dm push

# 查看状态
dm status

# 查看日志
dm logs [-f 持续显示]

# 清理旧镜像
dm cleanup [-d 天数] [-n 保留数量] [--dry-run]
```

## 配置文件

配置文件位于项目目录下的 `config.json`，可以通过 `dm config` 交互式配置：

```json
{
  "project": {
    "name": "my_project",
    "directory": "/path/to/project"
  },
  "image": {
    "name": "my-project-image",
    "dockerfile": "Dockerfile",
    "registry": {
      "url": "docker.io",
      "username": "username",
      "password": ""
    }
  },
  "container": {
    "name": "my-project-container",
    "compose_file": "docker-compose.yml",
    "cleanup": {
      "paths": ["/tmp/*", "/var/cache/*"]
    },
    "backup": {
      "schedule": "0 0 * * *",
      "cleanup": false,
      "auto_push": false
    }
  },
  "schedule": {
    "backup": {
      "cron": "0 0 * * *",
      "job_id": "unique_job_id",
      "cleanup": false,
      "auto_push": false
    },
    "cleanup": {
      "cron": "0 0 * * 0",
      "job_id": "unique_job_id",
      "paths": ["/tmp/*", "/var/cache/*"]
    }
  }
}
```

## 敏感信息管理

为了避免在配置文件中明文存储敏感信息（如Docker仓库密码），工具支持使用环境变量来管理这些信息：

### 使用环境变量存储密码

1. **通用环境变量**：设置 `DOCKER_PASSWORD` 环境变量
   ```bash
   export DOCKER_PASSWORD="your_password"
   ```

2. **用户特定环境变量**：如果有多个用户，可以设置用户特定的环境变量
   ```bash
   # 假设用户名为 username
   export DOCKER_PASSWORD_USERNAME="your_password"
   ```

3. **持久化环境变量**：将环境变量添加到 `~/.bashrc` 或 `~/.profile` 文件中
   ```bash
   echo 'export DOCKER_PASSWORD="your_password"' >> ~/.bashrc
   source ~/.bashrc
   ```

### 自动推送备份镜像

当启用自动推送备份镜像功能时，系统会按以下顺序查找认证信息：

1. 首先检查用户特定的环境变量（如 `DOCKER_PASSWORD_USERNAME`）
2. 然后检查通用环境变量 `DOCKER_PASSWORD`
3. 最后检查配置文件中的密码字段

为了安全起见，建议：
- 在配置文件中保留空的密码字段 `"password": ""`
- 使用环境变量存储实际密码
- 对于自动化任务，确保环境变量在任务执行时可用

### 手动登录替代方案

如果不想设置环境变量，也可以使用 Docker CLI 手动登录：

```bash
docker login -u username
# 系统会提示输入密码
```

登录后的凭证会存储在 Docker 的配置文件中，工具会自动使用这些凭证。

## 定时任务管理

工具提供了强大的定时任务管理功能，支持以下特性：

### 常用定时方案

交互式配置定时任务时，可以选择以下常用定时方案：

- **每天（午夜12点）**：`0 0 * * *`
- **每天（上午8点）**：`0 8 * * *`
- **每周（周日午夜）**：`0 0 * * 0`
- **每月（1号午夜）**：`0 0 1 * *`
- **每小时（整点）**：`0 * * * *`
- **自定义**：手动输入Cron表达式

### 任务类型

支持以下类型的定时任务：

- **备份任务**：定期将容器保存为镜像
  - 可选择是否在备份前清理容器
  - 可选择是否自动推送备份镜像

- **清理任务**：定期清理容器内的缓存文件
  - 可自定义清理路径

### 任务管理

- **列出任务**：`dm schedule list` 查看所有已配置的定时任务
- **删除任务**：`dm schedule remove` 交互式选择要删除的任务
- **修改任务**：删除旧任务后重新配置

## 智能默认值

工具使用集中式常量配置管理所有默认值，位于 `constants.py` 文件中：

- **项目名称**：使用目录名
- **Dockerfile**：自动查找项目目录下的 Dockerfile
- **Compose文件**：自动查找项目目录下的 docker-compose.yml
- **镜像名称**：使用项目名称
- **容器名称**：使用项目名称
- **注册表URL**：默认为 docker.io
- **清理路径**：默认为 `/tmp/*` 和 `/var/cache/*`

## 自定义默认值

如果需要修改默认值，可以通过以下方式：

1. **修改常量文件**：编辑 `constants.py` 文件中的相关配置
2. **环境变量**：使用环境变量覆盖默认配置
3. **配置文件**：在项目的 `config.json` 中设置自定义值

### 常量配置示例

```python
# 文件相关
DEFAULT_FILES = {
    'dockerfile': 'Dockerfile',
    'compose_file': 'docker-compose.yml',
    'config_file': 'config.json'
}

# 项目默认配置
DEFAULT_PROJECT_CONFIG = {
    'project': {
        'name': None,  # 将使用目录名
        'directory': None  # 将使用当前目录
    },
    'image': {
        'name': None,  # 将使用项目名
        'dockerfile': DEFAULT_FILES['dockerfile'],
        'registry': {
            'url': 'docker.io',
            'username': '',
            'password': ''
        }
    },
    # ... 更多配置 ...
}
```

## 必需文件检查

工具会在初始化项目时检查以下必需文件：

- **Dockerfile**：用于构建镜像
- **docker-compose.yml**：用于管理容器

如果这些文件不存在，工具会提供以下选项：

1. 创建这些文件后再初始化
2. 使用 `--force` 参数强制初始化

## 最佳实践

1. **项目组织**
   - 将相关文件放在同一目录下
   - 使用有意义的项目名称
   - 保持配置文件的整洁

2. **工作流程**
   - 使用 `dm init` 创建新项目
   - 使用 `dm config` 配置项目
   - 使用 `dm build` 构建镜像
   - 使用 `dm up` 启动容器
   - 使用 `dm save` 保存状态

3. **自动化**
   - 使用 `dm schedule` 配置定时备份和清理任务
   - 选择合适的定时方案或自定义Cron表达式
   - 使用 `dm schedule list` 定期检查任务状态
   - 使用环境变量管理敏感信息

4. **错误处理**
   - 使用 `--force` 参数处理特殊情况
   - 查看错误消息了解详细信息
   - 使用 `dm status` 检查当前状态

## 常见问题

1. **命令不生效**
   - 确保在正确的项目目录下
   - 检查配置文件是否正确
   - 使用 `dm status` 查看当前状态

2. **配置问题**
   - 使用 `dm config` 交互式配置
   - 检查配置文件格式
   - 使用环境变量覆盖敏感配置

3. **定时任务**
   - 使用 `dm schedule` 交互式配置，选择常用定时方案
   - 使用 `dm schedule list` 检查任务是否正确配置
   - 如需修改任务，先使用 `dm schedule remove` 删除旧任务
   - 确保系统时间正确

4. **缺少必需文件**
   - 创建必需的 Dockerfile 和 docker-compose.yml
   - 使用 `-f` 参数强制初始化
   - 检查文件路径是否正确

5. **构建参数问题**
   - 使用正确的格式：`--build-arg KEY=VALUE`
   - 多个参数需要多次使用 `--build-arg`
   - 检查参数是否被 Dockerfile 正确使用

6. **推送镜像失败**
   - 使用 `dm config` 配置正确的仓库信息（URL、用户名、密码）
   - 确保已登录到镜像仓库：`dm push -u 用户名 -p 密码`
   - 检查是否有推送权限
   - 对于私有仓库，确保仓库已创建
   - 如果遇到"access denied"错误，检查认证信息是否正确
   - 使用 `-f` 参数强制推送，跳过状态检查

## 开发者指南

### 添加新命令

1. 在 `cli.py` 中使用 `@app.command()` 装饰器添加新命令
2. 使用 `typer.Option` 和 `typer.Argument` 定义参数
3. 实现命令逻辑并使用 `logger` 输出结果

### 修改默认值

1. 编辑 `constants.py` 文件中的相关配置
2. 确保修改后的值与现有代码兼容
3. 更新文档以反映新的默认值

## 许可证

MIT 