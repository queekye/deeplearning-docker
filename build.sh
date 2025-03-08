#!/bin/bash
set -e

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始构建Docker镜像...${NC}"

# 构建基础镜像（如果不存在或强制重建）
if [ "$1" == "--rebuild-base" ] || [ ! "$(docker images -q deep-learning-base:latest 2> /dev/null)" ]; then
    echo -e "${YELLOW}构建基础镜像...${NC}"
    docker build -t deep-learning-base:latest -f Dockerfile.base .
else
    echo -e "${YELLOW}使用现有基础镜像...${NC}"
fi

# 构建应用镜像
echo -e "${YELLOW}构建应用镜像...${NC}"
docker build -t deep-learning-env:latest .

echo -e "${GREEN}镜像构建完成！${NC}"
echo -e "${GREEN}运行容器: docker run -it -p 28888:8888 -p 26006:6006 -p 20022:22 --gpus all deep-learning-env:latest${NC}" 