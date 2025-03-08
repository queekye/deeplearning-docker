# 使用预构建的基础镜像
FROM deep-learning-base:latest

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