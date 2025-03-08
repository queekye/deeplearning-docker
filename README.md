# 深度学习开发环境

这是一个基于PyTorch的深度学习开发环境，预装了常用工具和库，并针对中国大陆网络环境进行了优化。

## 优化的Docker构建流程

本项目采用了分层构建的方式，将不常变化的基础环境和经常变化的应用层分开，大大提高了开发和迭代效率：

1. **基础镜像**：包含PyTorch、CUDA、常用工具和服务（SSH、Jupyter、MLflow等）
2. **应用镜像**：包含特定项目的依赖和配置

## 目录结构

```
dockerfile/
├── Dockerfile.base    # 基础镜像定义
├── Dockerfile         # 应用镜像定义
├── start_service.sh   # 服务启动脚本
├── build.sh           # 构建脚本
├── docker-compose.yml # Docker Compose配置
└── requirements.txt   # Python依赖
```

## 使用方法

### 方法一：使用构建脚本（推荐）

```bash
# 进入dockerfile目录
cd dockerfile

# 赋予脚本执行权限
chmod +x build.sh

# 构建镜像（首次构建会同时构建基础镜像）
./build.sh

# 如果需要重建基础镜像
./build.sh --rebuild-base
```

### 方法二：使用Docker Compose

```bash
# 进入dockerfile目录
cd dockerfile

# 启动容器
docker-compose up -d

# 查看容器日志
docker-compose logs -f
```

### 方法三：手动构建和运行

```bash
# 构建基础镜像
docker build -t deep-learning-base:latest -f Dockerfile.base .

# 构建应用镜像
docker build -t deep-learning-env:latest .

# 运行容器
docker run -it -p 28888:8888 -p 26006:6006 -p 20022:22 --gpus all deep-learning-env:latest
```

## 服务访问

容器启动后，可以通过以下地址访问服务：

- **Jupyter Lab**: http://localhost:28888 (需要使用显示的令牌)
- **MLflow**: http://localhost:26006
- **SSH**: `ssh -p 20022 root@localhost`

> **注意**：上述端口是映射到本机的端口。容器内部使用的端口分别是8888(Jupyter)、6006(MLflow)和22(SSH)。容器内部脚本(如start_service.sh)中显示的地址使用的是容器内部端口。

## 开发工作流

### 修改启动脚本

如果您需要修改服务启动脚本，只需编辑`start_service.sh`文件，然后重新构建应用镜像：

```bash
# 编辑启动脚本
nano start_service.sh

# 重新构建应用镜像（不需要重建基础镜像）
docker build -t deep-learning-env:latest .

# 重启容器
docker-compose restart
```

### 添加新的Python依赖

如果您需要添加新的Python依赖，只需编辑`requirements.txt`文件，然后重新构建应用镜像：

```bash
# 编辑依赖文件
nano requirements.txt

# 重新构建应用镜像
docker build -t deep-learning-env:latest .

# 重启容器
docker-compose restart
```

> **依赖版本说明**：requirements.txt中的大多数依赖使用了>=版本约束，这允许安装最新的兼容版本。如果您需要确保环境的一致性和可重现性，建议将依赖版本固定为特定版本号（例如，将`torch>=2.0.0`改为`torch==2.0.0`）。

### 修改基础环境

如果您需要修改基础环境（如安装新的系统包或更改配置），需要编辑`Dockerfile.base`文件，然后重新构建基础镜像：

```bash
# 编辑基础镜像定义
nano Dockerfile.base

# 重新构建基础镜像
./build.sh --rebuild-base
```

## 预装功能

- PyTorch 2.6.0 + CUDA 12.4
- Jupyter Lab
- MLflow
- SSH服务
- 常用开发工具（git、vim、tmux等）
- 中国区镜像源配置（APT、pip、conda）

> **镜像源说明**：本项目默认配置了清华大学的镜像源，适合中国大陆用户使用。国际用户可以通过修改Dockerfile.base文件中的相关配置，将镜像源改为官方源或其他地区的镜像源。

## 主要特性

- 基于PyTorch 2.6.0，支持CUDA 12.4和cuDNN 9
- 预装Jupyter Notebook和JupyterLab
- 配置了清华大学镜像源（APT、pip、conda）
- 包含常用开发工具（git、vim、tmux等）
- 集成MLflow用于实验跟踪和模型管理

## 使用方法

### 构建镜像

```bash
docker build -t deep-learning-env .
```

### 运行容器

```bash
docker run -it --gpus all -p 28888:8888 -p 26006:6006 -p 20022:22 deep-learning-env
```

容器启动后，Jupyter Lab和MLflow服务会自动启动，并显示Jupyter的访问令牌。您可以直接通过以下地址访问服务：

- Jupyter Lab: http://localhost:28888 (需要使用显示的令牌)
- MLflow: http://localhost:26006

> **注意**：start_service.sh脚本中显示的访问地址使用的是容器内部端口(8888和6006)，而不是映射到主机的端口。请使用上述映射后的端口访问服务。

### 手动启动服务

如果需要手动启动服务，可以使用以下命令：

```bash
# 启动所有服务（包括MLflow和Jupyter）
start_service

# 只启动Jupyter
start_jupyter
```

### 配置 Git 全局信息，你可以根据实际情况修改

```bash
git config --global user.name "User Name"

git config --global user.email "Email"
```

### 使用MLflow

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

## 预克隆的仓库

- Flash Attention: https://github.com/Dao-AILab/flash-attention.git
- LLaMA-Factory: https://github.com/hiyouga/LLaMA-Factory.git

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

如果遇到端口冲突，可以修改docker-compose.yml或docker run命令中的端口映射：

```bash
# 例如，将Jupyter端口从28888改为38888
docker run -it --gpus all -p 38888:8888 -p 26006:6006 -p 20022:22 deep-learning-env:latest
```