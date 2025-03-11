#!/bin/bash
GREEN='\033[0;32m'
NC='\033[0m'

# 启动MLflow服务
cd /workspace/mlflow
nohup mlflow server \
    --host 0.0.0.0 \
    --port 6006 \
    --default-artifact-root file:///workspace/mlflow/artifacts > mlflow.log 2>&1 &
echo -e "${GREEN}MLflow服务已在后台启动，端口6006${NC}"

# 启动Jupyter服务
cd /workspace
nohup jupyter lab --allow-root --ip=0.0.0.0 --no-browser > jupyter.log 2>&1 &
echo -e "${GREEN}Jupyter Lab已在后台启动，端口8888${NC}"

# 显示Jupyter访问令牌
sleep 3
TOKEN=$(grep -oP '(?<=token=)[a-zA-Z0-9]+' jupyter.log | head -1)
if [ ! -z "$TOKEN" ]; then
    echo -e "${GREEN}Jupyter访问地址: http://localhost:8888/?token=$TOKEN${NC}"
else
    echo -e "${GREEN}Jupyter已启动，但无法获取令牌。请查看jupyter.log获取访问信息。${NC}"
fi

# 启动SSH服务
service ssh start
echo -e "${GREEN}SSH服务已启动${NC}"

# 保持容器运行
echo -e "${GREEN}所有服务已启动，容器将保持运行${NC}"
echo -e "${GREEN}使用Ctrl+C可以退出日志查看，但容器会继续在后台运行${NC}"
echo -e "${GREEN}===============================${NC}"

# 使用tail命令保持容器运行
tail -f /dev/null 