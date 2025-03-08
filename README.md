# 深度学习开发环境

这是一个基于PyTorch的深度学习开发环境，预装了常用工具和库，并针对中国大陆网络环境进行了优化。

## 优化的Docker构建流程

本项目采用了分层构建的方式，将不常变化的基础环境和经常变化的应用层分开，大大提高了开发和迭代效率：

1. **基础镜像**：包含PyTorch、CUDA、常用工具和服务（SSH、Jupyter、MLflow等）
2. **应用镜像**：包含特定项目的依赖和配置

## 目录结构

```
deeplearning-docker/
├── Dockerfile.base    # 基础镜像定义
├── Dockerfile         # 应用镜像定义
├── start_service.sh   # 服务启动脚本
├── docker-compose.yml # Docker Compose配置
├── requirements.txt   # Python依赖
└── manage_images.sh   # 镜像管理工具（所有操作都通过此工具进行）
```

## 使用方法

本项目提供了一个统一的镜像管理工具`manage_images.sh`，所有操作都通过此工具进行，避免误操作导致容器状态丢失。

### 基本使用流程

```bash
# 赋予脚本执行权限
chmod +x manage_images.sh

# 查看帮助信息
./manage_images.sh help

# 1. 初始化环境（首次使用）
./manage_images.sh init

# 2. 启动容器
./manage_images.sh start

# 3. 保存容器状态并重启（日常使用）
./manage_images.sh save

# 4. 设置定期自动保存
./manage_images.sh setup-cron
```

### 所有可用命令

| 命令            | 说明                                        |
| --------------- | ------------------------------------------- |
| `init`          | 初始化环境（构建基础镜像和应用镜像）        |
| `rebuild-base`  | 重建基础镜像                                |
| `save`          | 保存当前容器状态为新镜像并重启              |
| `clean`         | 清理容器内的缓存文件以减小镜像大小          |
| `compress`      | 通过导出/导入方式深度压缩镜像               |
| `set-cmd`       | 设置镜像的启动命令(CMD)和入口点(ENTRYPOINT) |
| `setup-cron`    | 设置定期自动保存                            |
| `list-backups`  | 列出所有备份镜像                            |
| `clean-backups` | 清理旧的备份镜像                            |
| `restore [TAG]` | 恢复到指定的备份镜像                        |
| `start`         | 启动容器（如果未运行）                      |
| `stop`          | 停止容器                                    |
| `restart`       | 重启容器                                    |
| `logs`          | 查看容器日志                                |
| `push`          | 将当前镜像推送到Docker Hub或指定的registry  |
| `help`          | 显示帮助信息                                |

### Docker Compose 兼容性

镜像管理工具自动检测并支持两种Docker Compose命令形式：
- 新版本的 `docker compose`（无连字符）
- 旧版本的 `docker-compose`（带连字符）

无论您的系统使用哪种命令形式，脚本都能自动适配，无需手动修改。

## 服务访问

容器启动后，可以通过以下地址访问服务：

- **Jupyter Lab**: http://localhost:28888 (需要使用显示的令牌)
- **MLflow**: http://localhost:26006
- **SSH**: `ssh -p 20022 root@localhost`

> **注意**：上述端口是映射到本机的端口。容器内部使用的端口分别是8888(Jupyter)、6006(MLflow)和22(SSH)。容器内部脚本(如start_service.sh)中显示的地址使用的是容器内部端口。

## 容器状态保存与恢复功能

本项目提供了容器状态保存功能，可以将当前容器的完整状态（包括已安装的软件、配置、历史记录等）保存为新镜像，并在重启时使用该镜像。这对于保存开发环境的完整状态（如Cursor历史、插件配置等）非常有用。

### 使用阶段说明

1. **初始设置阶段**：
   - 使用`./manage_images.sh init`构建初始环境
   - 使用`./manage_images.sh start`启动容器
   - 进行初始配置（安装插件、设置偏好等）

2. **日常使用阶段**：
   - 使用`./manage_images.sh save`保存状态并重启
   - 使用`./manage_images.sh setup-cron`设置定期自动保存

> **重要**：一旦进入日常使用阶段（执行过save命令），就不应再使用init命令，否则会覆盖您保存的容器状态。镜像管理工具会在执行可能覆盖容器状态的操作前给出警告。

### 保存容器状态

```bash
# 保存当前容器状态并重启
./manage_images.sh save
```

执行后，脚本会：
1. 询问是否先清理容器内的缓存文件
2. 将当前容器状态保存为新的`deep-learning-env:latest`镜像
3. 将原镜像备份为带时间戳的版本（如`deep-learning-env:backup_20240601_120000`）
4. 使用新镜像重启容器

### 优化镜像大小

随着使用时间的增长，容器内可能会积累大量缓存文件（如Hugging Face模型缓存、pip缓存等），导致保存的镜像越来越大。可以使用以下命令清理这些缓存文件：

```bash
# 清理容器内的缓存文件
./manage_images.sh clean
```

执行后，脚本会：
1. 清理APT缓存、pip缓存、Hugging Face缓存等
2. 清理临时文件和日志文件
3. 显示容器内占用空间较大的文件和目录

建议在保存镜像前先运行此命令，或者在保存时选择清理选项，以减小镜像大小。

#### 深度压缩镜像

如果清理缓存后镜像仍然很大，可以使用深度压缩功能：

```bash
# 停止容器
./manage_images.sh stop

# 深度压缩镜像
./manage_images.sh compress
```

此命令通过Docker的导出/导入机制重建镜像，可以显著减小镜像大小：
1. 移除所有历史层和已删除文件占用的空间
2. 重新构建单层镜像，消除冗余数据
3. 保留原镜像的备份，以防压缩后出现问题
4. 自动保存和恢复CMD、ENTRYPOINT和环境变量等元数据

> **注意**：深度压缩会丢失镜像的历史记录，但不会影响容器的功能。压缩过程可能需要较长时间，取决于镜像大小。脚本会自动检测并安装所需的依赖（如jq）。

#### 手动设置启动命令

如果压缩后的镜像启动命令(CMD)或入口点(ENTRYPOINT)丢失，可以使用以下命令手动设置：

```bash
# 停止容器
./manage_images.sh stop

# 设置启动命令
./manage_images.sh set-cmd
```

此命令提供了一个交互式界面，允许您：
1. 查看当前的CMD、ENTRYPOINT和WORKDIR配置
2. 修改CMD（容器启动命令）
3. 修改ENTRYPOINT（容器入口点）
4. 修改WORKDIR（工作目录）
5. 将所有配置重置为默认值

默认配置为：
- WORKDIR: `/workspace`
- ENTRYPOINT: `["/bin/bash", "-c"]`
- CMD: `["/start_service.sh"]`

每次修改都会自动备份当前镜像，以便在需要时恢复。

### 设置定期自动保存

为了确保您的工作环境定期备份，可以设置定期自动保存：

```bash
# 设置定期自动保存
./manage_images.sh setup-cron
```

按照提示选择执行频率（每天、每周、每月或自定义），脚本会自动设置cron任务。您还可以选择：

1. **自动清理容器**：在保存前自动清理容器内的缓存文件，减小镜像大小
2. **自动推送镜像**：在保存后自动将镜像推送到Docker Hub或自定义Registry

这样，您可以实现完全自动化的备份、清理和分发流程，确保您的开发环境始终保持最佳状态。

### 管理备份镜像

随着时间推移，备份镜像可能会占用大量磁盘空间。可以使用镜像管理工具清理旧的备份镜像：

```bash
# 列出所有备份
./manage_images.sh list-backups

# 清理旧备份（交互式选择）
./manage_images.sh clean-backups

# 恢复到指定备份
./manage_images.sh restore backup_20240601_120000
```

### 镜像推送功能

本项目提供了将镜像推送到Docker Hub或自定义Registry的功能，方便在不同环境之间共享和部署镜像。

```bash
# 推送镜像
./manage_images.sh push
```

执行后，脚本会引导您完成以下步骤：

1. 如果容器正在运行，询问是否先保存当前容器状态
2. 选择推送目标（Docker Hub或自定义Registry）
3. 输入必要的信息（用户名、镜像名称等）
4. 如果选择Docker Hub，可以设置仓库可见性（私有或公开）
5. 自动检测是否已登录目标Registry，如未登录则提示登录
6. 询问是否同时推送基础镜像（deep-learning-base）
7. 询问是否添加额外的标签（如v1.0、stable等）
8. 询问是否保存配置用于自动推送，以及配置文件的保存位置

#### 仓库可见性设置

当推送到Docker Hub时，您可以选择仓库的可见性：
- **私有仓库**：仅您自己和授权用户可以访问（默认选项）
- **公开仓库**：任何人都可以查看和拉取

如果仓库不存在，脚本会引导您在Docker Hub网站上创建仓库并设置可见性。

#### 配置文件位置

推送配置可以保存在两个位置：
1. **项目目录**（`./docker_push_config`）：适合特定项目的配置
2. **用户主目录**（`~/.docker_push_config`）：适合全局配置

脚本会自动检查这两个位置，优先使用项目目录中的配置。

#### 自动推送功能

脚本支持自动推送功能，无需每次手动输入信息和登录。这对于定期备份和推送非常有用。

```bash
# 首次配置自动推送
./manage_images.sh push
# 按提示操作，并在最后选择"是"保存配置

# 之后可以使用自动模式推送
./manage_images.sh push auto
```

#### 与定时任务集成

设置定期自动保存时，可以选择在保存后自动推送镜像：

```bash
# 设置定期自动保存和推送
./manage_images.sh setup-cron
# 按提示设置频率，并选择"是"启用自动推送
```

#### 关于Docker登录凭据

Docker登录凭据（包括访问令牌）保存在`~/.docker/config.json`文件中。一旦登录成功，这些凭据将被保留，无需每次推送时重新登录。

对于自动化场景，您可以：

1. 使用`docker login`命令手动登录一次
2. 使用访问令牌而非密码登录（在Docker Hub网站上生成）
3. 对于CI/CD环境，可以使用环境变量设置凭据

> **注意**：推送前请确保您有足够的权限访问目标Registry，并且镜像名称符合目标Registry的命名规范。

## 开发工作流

### 修改启动脚本

如果您需要修改服务启动脚本，只需编辑`start_service.sh`文件，然后重新构建应用镜像：

```bash
# 编辑启动脚本
nano start_service.sh

# 重新构建应用镜像（不需要重建基础镜像）
./manage_images.sh init

# 重启容器
./manage_images.sh restart
```

### 添加新的Python依赖

如果您需要添加新的Python依赖，只需编辑`requirements.txt`文件，然后重新构建应用镜像：

```bash
# 编辑依赖文件
nano requirements.txt

# 重新构建应用镜像
./manage_images.sh init

# 重启容器
./manage_images.sh restart
```

> **依赖版本说明**：requirements.txt中的大多数依赖使用了>=版本约束，这允许安装最新的兼容版本。如果您需要确保环境的一致性和可重现性，建议将依赖版本固定为特定版本号（例如，将`torch>=2.0.0`改为`torch==2.0.0`）。

### 修改基础环境

如果您需要修改基础环境（如安装新的系统包或更改配置），需要编辑`Dockerfile.base`文件，然后重新构建基础镜像：

```bash
# 编辑基础镜像定义
nano Dockerfile.base

# 重新构建基础镜像
./manage_images.sh rebuild-base
```

## 预装功能

- PyTorch 2.6.0 + CUDA 12.4
- Jupyter Lab
- MLflow
- SSH服务
- 常用开发工具（git、vim、tmux等）
- 中国区镜像源配置（APT、pip、conda）
- 容器状态保存与恢复功能
- 定期自动备份功能
- 统一的镜像生命周期管理工具

> **镜像源说明**：本项目默认配置了清华大学的镜像源，适合中国大陆用户使用。国际用户可以通过修改Dockerfile.base文件中的相关配置，将镜像源改为官方源或其他地区的镜像源。

## 使用MLflow

MLflow服务将在后台运行，可以通过浏览器访问 `http://localhost:26006` 查看实验结果。

在Python代码中使用MLflow：

```python
import mlflow

# 环境变量已经设置好MLFLOW_TRACKING_URI，无需手动指定

# 开始一个实验
mlflow.start_run(run_name="my_experiment")

# 记录参数
mlflow.log_param("learning_rate", 0.01)

# 记录指标
mlflow.log_metric("accuracy", 0.95)

# 保存模型
mlflow.pytorch.log_model(model, "model")

# 结束实验
mlflow.end_run()
```

## 预装Python库

- PyTorch 2.6.0
- Transformers
- Datasets
- MLflow
- 以及其他常用机器学习和数据科学库

## 安全注意事项

在使用本项目时，请注意以下安全风险：

1. **网络安全**：
   - 容器内的服务（Jupyter、MLflow、SSH）默认绑定到0.0.0.0，接受来自任何IP的连接
   - 在公共网络或生产环境中使用时，建议配置防火墙或使用反向代理进行保护
   - 考虑修改服务绑定地址为127.0.0.1，并通过安全的方式暴露服务

2. **SSH安全**：
   - 容器内默认允许root用户通过SSH登录，并使用无密码的SSH密钥
   - 在生产环境中，建议禁用root SSH登录或启用更严格的认证方式
   - 定期更换SSH密钥，并为密钥设置密码保护

3. **数据安全**：
   - 通过卷挂载的数据在容器外部可见，请确保主机安全
   - 敏感数据应当加密存储，避免在容器内存储明文凭证
   - 定期备份重要数据

4. **权限控制**：
   - 容器内服务默认没有设置额外的认证机制
   - 在多用户环境中，建议为Jupyter和MLflow配置认证
   - 考虑使用非root用户运行容器内服务

5. **更新维护**：
   - 定期更新基础镜像和依赖包，以修复已知安全漏洞
   - 关注PyTorch、CUDA和其他关键组件的安全公告

本项目主要用于开发和研究环境，如需在生产环境使用，请进行适当的安全加固。

## 故障排除

### 目录挂载问题

使用Docker Compose时，如果遇到目录挂载错误，请确保已创建相应的目录：

```bash
# 创建数据目录
mkdir -p data notebooks models
```

### 端口冲突问题

如果遇到端口冲突，可以修改docker-compose.yml中的端口映射：

```bash
# 例如，将Jupyter端口从28888改为38888
# 修改docker-compose.yml后重启容器
./manage_images.sh restart
```