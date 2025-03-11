# 基于PyTorch官方镜像
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# 设置工作目录
WORKDIR /workspace

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 更新apt并安装基础工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    openssh-server \
    nano \
    vim \
    screen \
    tmux \
    curl \
    wget \
    ca-certificates \
    apt-transport-https \
    gnupg \
    lsb-release \
    software-properties-common \
    htop \
    unzip \
    zip

# 配置SSH
RUN mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    touch /root/.ssh/known_hosts && \
    chmod 644 /root/.ssh/known_hosts

# 配置SSH服务
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    dpkg-reconfigure openssh-server

# 生成SSH密钥对
RUN ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""

# 配置Git
RUN git config --global core.editor "nano" && \
    git config --global core.autocrlf input

# 配置pip镜像源
RUN mkdir -p /root/.pip && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = pypi.tuna.tsinghua.edu.cn" > /root/.pip/pip.conf

# 配置conda镜像源
RUN conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/ && \
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/ && \
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/ && \
    conda config --set show_channel_urls yes

# 安装Jupyter
RUN pip install jupyter jupyterlab jupyter_contrib_nbextensions jupyter_nbextensions_configurator

# 配置Jupyter
RUN mkdir -p /root/.jupyter && \
    jupyter notebook --generate-config && \
    echo "c.NotebookApp.ip = '0.0.0.0'\nc.NotebookApp.open_browser = False\nc.NotebookApp.port = 8888\nc.NotebookApp.allow_root = True\nc.NotebookApp.notebook_dir = '/workspace'" >> /root/.jupyter/jupyter_notebook_config.py

# 创建MLflow工作目录
RUN mkdir -p /workspace/mlflow/artifacts

# 清理缓存
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 暴露端口
EXPOSE 8888 6006 22

# 复制项目文件
COPY requirements.txt /workspace/requirements.txt

# 安装Python依赖
RUN pip install -r /workspace/requirements.txt

# 复制启动脚本
COPY start_service.sh /workspace/start_service.sh
RUN chmod +x /workspace/start_service.sh

# 设置容器启动命令
CMD ["/workspace/start_service.sh"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8888/ || curl -f http://localhost:6006/ || exit 1 