# Docker项目和容器管理工具 - 开发文档

本文档提供了Docker项目和容器管理工具的架构设计、开发指南和贡献方式。

## 项目架构

该项目采用模块化设计，将镜像管理和容器管理分离，以提供更灵活的功能。

### 核心组件

1. **基础管理器类**
   - `BaseManager`：所有管理器的基类
   - `BaseProjectManager`：项目管理相关的基类
   - `BaseContainerManager`：容器管理相关的基类

2. **项目和镜像管理**
   - `ProjectManager`：管理项目的创建、删除和配置
   - `ImageManager`：管理镜像的构建、标记、推送和压缩
   - `DockerProjectManager`：项目和镜像管理的主类

3. **容器管理**
   - `ContainerManager`：管理容器的创建、启动、停止和重启
   - `BackupManager`：管理容器的备份和恢复
   - `CleanManager`：管理容器的清理
   - `DockerContainerManager`：容器管理的主类

4. **命令行接口**
   - `cli.py`：主命令行接口
   - `project_commands.py`：项目管理命令
   - `image_commands.py`：镜像管理命令
   - `container_commands.py`：容器管理命令
   - `cli_utils.py`：命令行工具函数

### 配置结构

配置文件采用YAML格式，分为项目配置和容器配置两部分：

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

# 其他配置...
```

## 开发指南

### 环境设置

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/docker_manager.git
   cd docker_manager
   ```

2. 创建虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. 安装开发依赖
   ```bash
   pip install -e ".[dev]"
   ```

### 代码风格

本项目遵循PEP 8代码风格指南，并使用以下工具进行代码质量控制：

- `black`：代码格式化
- `flake8`：代码风格检查
- `isort`：导入排序
- `mypy`：类型检查

在提交代码前，请运行以下命令：

```bash
# 格式化代码
black docker_manager

# 检查代码风格
flake8 docker_manager

# 排序导入
isort docker_manager

# 类型检查
mypy docker_manager
```

### 测试

本项目使用`pytest`进行单元测试和集成测试：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_project_manager.py

# 生成测试覆盖率报告
pytest --cov=docker_manager
```

## 架构设计

### 类图

```
BaseManager
├── BaseProjectManager
│   ├── ProjectManager
│   ├── ImageManager
│   └── DockerProjectManager
└── BaseContainerManager
    ├── ContainerManager
    ├── BackupManager
    ├── CleanManager
    └── DockerContainerManager
```

### 命令流程

1. **项目管理命令**
   - 用户输入 -> CLI解析 -> ProjectManager执行 -> 返回结果

2. **镜像管理命令**
   - 用户输入 -> CLI解析 -> DockerProjectManager执行 -> 返回结果

3. **容器管理命令**
   - 用户输入 -> CLI解析 -> DockerContainerManager执行 -> 返回结果

## 贡献指南

我们欢迎所有形式的贡献，包括但不限于：

- 代码贡献
- 文档改进
- Bug报告
- 功能请求

### 贡献流程

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### Pull Request指南

- 确保代码通过所有测试
- 更新文档以反映任何更改
- 遵循现有的代码风格
- 添加测试以覆盖新功能或修复的Bug

## 版本发布

本项目使用语义化版本控制（[SemVer](https://semver.org/)）：

- MAJOR版本：不兼容的API更改
- MINOR版本：向后兼容的功能添加
- PATCH版本：向后兼容的Bug修复

### 发布流程

1. 更新版本号（在`setup.py`和`docker_manager/__init__.py`中）
2. 更新CHANGELOG.md
3. 创建发布分支 (`git checkout -b release/vX.Y.Z`)
4. 提交更改 (`git commit -m 'Release vX.Y.Z'`)
5. 创建标签 (`git tag vX.Y.Z`)
6. 推送到仓库 (`git push origin release/vX.Y.Z --tags`)
7. 创建GitHub Release

## 路线图

### 短期目标

- 完善单元测试
- 添加更多的文档和示例
- 改进错误处理和日志记录

### 中期目标

- 添加Web界面
- 支持更多的Docker功能
- 添加更多的自动化功能

### 长期目标

- 支持多种容器运行时
- 添加集群管理功能
- 添加更多的云服务集成 