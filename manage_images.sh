#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测Docker Compose命令
detect_docker_compose_cmd() {
    # 检查是否支持新版命令格式
    if docker compose version &>/dev/null; then
        echo "docker compose"
    # 检查是否支持旧版命令格式
    elif docker-compose version &>/dev/null; then
        echo "docker-compose"
    else
        echo -e "${RED}错误：未找到Docker Compose命令。请确保已安装Docker Compose。${NC}"
        exit 1
    fi
}

# 获取Docker Compose命令
DOCKER_COMPOSE_CMD=$(detect_docker_compose_cmd)

# 显示帮助信息
show_help() {
    echo -e "${BLUE}深度学习环境镜像管理工具${NC}"
    echo
    echo -e "用法: $0 [选项]"
    echo
    echo -e "选项:"
    echo -e "  ${GREEN}init${NC}             初始化环境（构建基础镜像和应用镜像）"
    echo -e "  ${GREEN}rebuild-base${NC}     重建基础镜像"
    echo -e "  ${GREEN}save${NC}             保存当前容器状态为新镜像并重启"
    echo -e "  ${GREEN}clean${NC}            清理容器内的缓存文件以减小镜像大小"
    echo -e "  ${GREEN}compress${NC}         通过导出/导入方式压缩镜像"
    echo -e "  ${GREEN}set-cmd${NC}          设置镜像的启动命令(CMD)"
    echo -e "  ${GREEN}setup-cron${NC}       设置定期自动保存"
    echo -e "  ${GREEN}list-backups${NC}     列出所有备份镜像"
    echo -e "  ${GREEN}clean-backups${NC}    清理旧的备份镜像"
    echo -e "  ${GREEN}restore${NC} [TAG]    恢复到指定的备份镜像"
    echo -e "  ${GREEN}start${NC}            启动容器（如果未运行）"
    echo -e "  ${GREEN}stop${NC}             停止容器"
    echo -e "  ${GREEN}restart${NC}          重启容器"
    echo -e "  ${GREEN}logs${NC}             查看容器日志"
    echo -e "  ${GREEN}push${NC}             将当前镜像推送到Docker Hub或指定的registry"
    echo -e "  ${GREEN}help${NC}             显示此帮助信息"
    echo
    echo -e "${YELLOW}使用阶段说明:${NC}"
    echo -e "1. 初始设置阶段: 使用 ${GREEN}init${NC} 命令构建初始环境"
    echo -e "2. 日常使用阶段: 使用 ${GREEN}save${NC} 命令保存容器状态"
    echo
    echo -e "${RED}注意:${NC} 一旦进入日常使用阶段（执行过save命令），就不应再使用init命令，"
    echo -e "      否则会覆盖您保存的容器状态。"
    echo
    echo -e "${YELLOW}当前使用的Docker Compose命令: ${DOCKER_COMPOSE_CMD}${NC}"
}

# 检查是否已进入日常使用阶段
check_daily_usage_phase() {
    if docker images "deep-learning-env:backup_*" --format "{{.Repository}}:{{.Tag}}" | grep -q "deep-learning-env:backup_"; then
        return 0  # 已进入日常使用阶段
    else
        return 1  # 尚未进入日常使用阶段
    fi
}

# 初始化环境
init_environment() {
    if check_daily_usage_phase; then
        echo -e "${RED}警告：检测到备份镜像存在！${NC}"
        echo -e "${RED}您似乎已经进入日常使用阶段，执行初始化将覆盖您保存的容器状态。${NC}"
        echo -e "${YELLOW}推荐使用 $0 save 来保存和重启容器。${NC}"
        
        read -p "您确定要继续吗？这将覆盖您的容器状态！(y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo -e "${GREEN}操作已取消。请使用 $0 save 来保存和重启容器。${NC}"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}开始初始化环境...${NC}"
    
    # 检查基础镜像是否存在
    if ! docker images deep-learning-base:latest | grep -q deep-learning-base; then
        echo -e "${YELLOW}构建基础镜像...${NC}"
        docker build -t deep-learning-base:latest -f Dockerfile.base .
    else
        echo -e "${GREEN}使用现有的基础镜像${NC}"
    fi
    
    # 构建应用镜像
    echo -e "${YELLOW}构建应用镜像...${NC}"
    docker build -t deep-learning-env:latest .
    
    echo -e "${GREEN}环境初始化完成！${NC}"
    echo -e "${YELLOW}您可以使用以下命令启动容器：${NC}"
    echo -e "$0 start"
    
    return 0
}

# 重建基础镜像
rebuild_base() {
    if check_daily_usage_phase; then
        echo -e "${RED}警告：检测到备份镜像存在！${NC}"
        echo -e "${RED}您似乎已经进入日常使用阶段，重建基础镜像可能会影响您的环境。${NC}"
        
        read -p "您确定要继续吗？(y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo -e "${GREEN}操作已取消。${NC}"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}重建基础镜像...${NC}"
    docker build -t deep-learning-base:latest -f Dockerfile.base .
    
    echo -e "${YELLOW}重建应用镜像...${NC}"
    docker build -t deep-learning-env:latest .
    
    echo -e "${GREEN}基础镜像重建完成！${NC}"
    echo -e "${YELLOW}您需要重启容器以应用更改：${NC}"
    echo -e "$0 restart"
    
    return 0
}

# 清理容器内的缓存文件
clean_container() {
    # 检查容器是否在运行
    if ! docker ps | grep -q "deep-learning-env"; then
        echo -e "${RED}错误：容器 deep-learning-env 未运行！${NC}"
        echo -e "${YELLOW}请先启动容器：$0 start${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}正在清理容器内的缓存文件...${NC}"
    
    # 执行清理命令
    docker exec deep-learning-env bash -c "
        set -e
        echo '${YELLOW}将要清理以下内容:${NC}'
        echo '- APT缓存 (/var/cache/apt/)'
        echo '- pip缓存 (/root/.cache/pip/)'
        echo '- Hugging Face缓存 (/root/.cache/huggingface/)'
        echo '- Jupyter缓存 (不影响配置和扩展)'
        echo '- 临时文件 (/tmp/*)'
        echo '- 日志文件 (/var/log/*.log, /var/log/*.gz)'
        echo '- bash历史 (/root/.bash_history)'
        echo
        
        echo '${GREEN}以下重要数据不会被清理:${NC}'
        echo '- Cursor配置和历史 (/root/.cursor/, /root/.config/cursor/)'
        echo '- SSH配置和密钥 (/etc/ssh/, /root/.ssh/)'
        echo '- 服务器配置文件 (Jupyter, MLflow等)'
        echo '- 工作目录数据 (/workspace/)'
        echo '- 用户安装的软件和插件'
        echo
        
        echo '清理APT缓存...'
        apt-get clean
        
        echo '清理pip缓存...'
        rm -rf /root/.cache/pip
        
        echo '清理Hugging Face缓存...'
        rm -rf /root/.cache/huggingface
        
        echo '清理Jupyter缓存...'
        jupyter lab clean
        jupyter cache clean 2>/dev/null || echo '跳过jupyter cache clean (可能未安装)'
        
        echo '清理系统缓存...'
        # 保留重要的临时文件
        find /tmp -type f -not -path '*/ssh*' -not -path '*/systemd*' -delete
        find /tmp -type d -empty -delete
        
        echo '清理日志文件...'
        find /var/log -type f -name '*.log' -delete
        find /var/log -type f -name '*.gz' -delete
        
        echo '清理bash历史...'
        rm -f /root/.bash_history
        
        echo '查找大文件(>100MB)...'
        find / -type f -size +100M -not -path '*/proc/*' -not -path '*/sys/*' -not -path '*/dev/*' -not -path '*/workspace/*' 2>/dev/null | sort -k2 | while read file; do
            echo \"\$file: \$(du -h \"\$file\" | cut -f1)\"
        done
        
        echo '分析磁盘使用情况...'
        du -h --max-depth=1 /root | sort -hr | head -10
        du -h --max-depth=1 /workspace | sort -hr | head -10
        du -h --max-depth=1 / | sort -hr | head -10
    "
    
    echo -e "${GREEN}容器内缓存文件清理完成！${NC}"
    echo -e "${YELLOW}您可以使用以下命令保存容器状态：${NC}"
    echo -e "$0 save"
    
    return 0
}

# 保存容器状态并重启
save_container() {
    # 检查容器是否在运行
    if ! docker ps | grep -q "deep-learning-env"; then
        echo -e "${RED}错误：容器 deep-learning-env 未运行！${NC}"
        echo -e "${YELLOW}请先启动容器：$0 start${NC}"
        return 1
    fi
    
    # 询问是否先清理容器
    read -p "是否先清理容器内的缓存文件以减小镜像大小？(y/N): " clean_first
    if [[ "$clean_first" == "y" || "$clean_first" == "Y" ]]; then
        clean_container
    fi
    
    echo -e "${YELLOW}正在保存当前容器状态为新镜像...${NC}"
    
    # 获取当前时间作为标签
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    NEW_IMAGE_NAME="deep-learning-env:latest"
    BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
    
    # 将当前镜像标记为备份
    echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
    docker tag ${NEW_IMAGE_NAME} ${BACKUP_IMAGE_NAME}
    
    # 提交当前容器为新镜像
    echo -e "${YELLOW}提交当前容器为新镜像...${NC}"
    docker commit deep-learning-env ${NEW_IMAGE_NAME}
    
    # 使用docker-compose重启容器
    echo -e "${YELLOW}重启容器...${NC}"
    ${DOCKER_COMPOSE_CMD} down
    ${DOCKER_COMPOSE_CMD} up -d
    
    # 等待容器启动
    echo -e "${YELLOW}等待容器启动...${NC}"
    sleep 5
    
    # 检查容器状态
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${GREEN}容器已成功重启！${NC}"
        echo -e "${GREEN}新镜像已保存为 ${NEW_IMAGE_NAME}${NC}"
        echo -e "${GREEN}旧镜像已备份为 ${BACKUP_IMAGE_NAME}${NC}"
    else
        echo -e "${YELLOW}容器可能未正常启动，请检查日志：${NC}"
        ${DOCKER_COMPOSE_CMD} logs
    fi
    
    return 0
}

# 推送镜像到Docker Hub或指定的registry
push_image() {
    # 检查是否有参数传入（用于自动推送模式）
    local auto_mode=false
    local auto_target=""
    local auto_username=""
    local auto_registry=""
    local auto_image_name="deep-learning-env"
    local auto_push_base=false
    local auto_tag=""
    local skip_save_check=false
    local auto_private=true  # 默认为私有仓库
    
    # 解析参数
    for arg in "$@"; do
        if [ "$arg" == "auto" ]; then
            auto_mode=true
        elif [ "$arg" == "skip_save_check" ]; then
            skip_save_check=true
        fi
    done
    
    if [ "$auto_mode" = true ]; then
        # 读取配置文件
        local config_file=""
        
        # 首先检查项目目录下的配置文件
        if [ -f "./docker_push_config" ]; then
            config_file="./docker_push_config"
        # 然后检查用户主目录下的配置文件
        elif [ -f "${HOME}/.docker_push_config" ]; then
            config_file="${HOME}/.docker_push_config"
        fi
        
        if [ ! -z "$config_file" ]; then
            source "$config_file"
            echo -e "${YELLOW}已读取自动推送配置: $config_file${NC}"
        else
            echo -e "${RED}错误：未找到自动推送配置文件${NC}"
            echo -e "${YELLOW}请先运行 $0 push 并设置自动推送配置${NC}"
            return 1
        fi
    fi
    
    # 检查容器是否在运行（非自动模式且未跳过检查时）
    if [ "$auto_mode" = false ] && [ "$skip_save_check" = false ] && docker ps | grep -q "deep-learning-env"; then
        echo -e "${YELLOW}检测到容器正在运行${NC}"
        read -p "是否先保存当前容器状态？(y/N): " save_first
        if [[ "$save_first" == "y" || "$save_first" == "Y" ]]; then
            save_container
        fi
    fi
    
    if [ "$auto_mode" = false ]; then
        echo -e "${YELLOW}准备推送镜像...${NC}"
        
        # 询问推送目标
        echo -e "${YELLOW}请选择推送目标：${NC}"
        echo "1) Docker Hub"
        echo "2) 自定义Registry"
        read -p "请选择 [1-2]: " registry_option
        
        case $registry_option in
            1)
                read -p "请输入Docker Hub用户名: " username
                read -p "请输入镜像名称 (默认: deep-learning-env): " image_name
                image_name=${image_name:-deep-learning-env}
                
                # 询问仓库可见性
                echo -e "${YELLOW}请选择仓库可见性：${NC}"
                echo "1) 私有 (Private) - 仅自己和授权用户可访问"
                echo "2) 公开 (Public) - 任何人都可以访问"
                read -p "请选择 [1-2]: " visibility_option
                
                local is_private=true
                case $visibility_option in
                    1)
                        is_private=true
                        echo -e "${YELLOW}已选择私有仓库${NC}"
                        ;;
                    2)
                        is_private=false
                        echo -e "${YELLOW}已选择公开仓库${NC}"
                        ;;
                    *)
                        echo -e "${RED}无效的选项，将使用默认值（私有仓库）${NC}"
                        is_private=true
                        ;;
                esac
                
                # 检查仓库是否存在
                echo -e "${YELLOW}检查仓库是否存在...${NC}"
                if curl -s -f -L -X GET "https://hub.docker.com/v2/repositories/${username}/${image_name}" > /dev/null; then
                    echo -e "${GREEN}仓库已存在: ${username}/${image_name}${NC}"
                else
                    echo -e "${YELLOW}仓库不存在，需要创建${NC}"
                    
                    # 检查是否已登录Docker Hub
                    if ! docker info 2>/dev/null | grep -q "Username"; then
                        echo -e "${YELLOW}您尚未登录Docker Hub${NC}"
                        echo -e "${YELLOW}请先登录Docker Hub${NC}"
                        docker login
                        
                        # 检查登录是否成功
                        if [ $? -ne 0 ]; then
                            echo -e "${RED}登录失败，推送操作已取消${NC}"
                            return 1
                        fi
                    fi
                    
                    # 创建仓库
                    echo -e "${YELLOW}正在创建${is_private:+私有}${is_private:+:+公开}仓库: ${username}/${image_name}${NC}"
                    
                    # 提示用户在Docker Hub网站上创建仓库
                    echo -e "${YELLOW}请在Docker Hub网站上创建仓库:${NC}"
                    echo -e "1. 访问 https://hub.docker.com/repositories"
                    echo -e "2. 点击 'Create Repository'"
                    echo -e "3. 输入仓库名称: ${image_name}"
                    echo -e "4. 选择可见性: ${is_private:+Private}${is_private:+:+Public}"
                    echo -e "5. 点击 'Create'"
                    
                    read -p "仓库创建完成后按回车继续..." _
                fi
                
                # 检查是否已登录Docker Hub
                if ! docker info 2>/dev/null | grep -q "Username"; then
                    # 检查是否存在Docker配置文件
                    if [ ! -f "${HOME}/.docker/config.json" ] || ! grep -q "auth" "${HOME}/.docker/config.json"; then
                        echo -e "${YELLOW}您尚未登录Docker Hub${NC}"
                        read -p "是否现在登录？(y/N): " need_login
                        
                        if [[ "$need_login" == "y" || "$need_login" == "Y" ]]; then
                            echo -e "${YELLOW}请登录Docker Hub...${NC}"
                            docker login
                            
                            # 检查登录是否成功
                            if [ $? -ne 0 ]; then
                                echo -e "${RED}登录失败，推送操作已取消${NC}"
                                return 1
                            fi
                        else
                            echo -e "${RED}未登录Docker Hub，推送可能会失败${NC}"
                        fi
                    else
                        echo -e "${GREEN}检测到Docker Hub凭据已存在${NC}"
                    fi
                else
                    echo -e "${GREEN}已登录Docker Hub${NC}"
                fi
                
                # 构建目标镜像名称
                target_image="${username}/${image_name}:latest"
                
                # 设置自动推送目标
                auto_target="dockerhub"
                auto_username="${username}"
                auto_image_name="${image_name}"
                auto_private="${is_private}"
                ;;
            2)
                read -p "请输入Registry地址 (例如: registry.example.com): " registry
                read -p "请输入镜像名称 (默认: deep-learning-env): " image_name
                image_name=${image_name:-deep-learning-env}
                
                # 检查是否已登录该Registry
                if ! docker info 2>/dev/null | grep -q "${registry}" || ! grep -q "${registry}" "${HOME}/.docker/config.json" 2>/dev/null; then
                    echo -e "${YELLOW}您可能尚未登录${registry}${NC}"
                    read -p "是否现在登录？(y/N): " need_login
                    
                    if [[ "$need_login" == "y" || "$need_login" == "Y" ]]; then
                        echo -e "${YELLOW}请登录Registry...${NC}"
                        docker login ${registry}
                        
                        # 检查登录是否成功
                        if [ $? -ne 0 ]; then
                            echo -e "${RED}登录失败，推送操作已取消${NC}"
                            return 1
                        fi
                    else
                        echo -e "${RED}未登录Registry，推送可能会失败${NC}"
                    fi
                else
                    echo -e "${GREEN}已登录${registry}${NC}"
                fi
                
                # 构建目标镜像名称
                target_image="${registry}/${image_name}:latest"
                
                # 设置自动推送目标
                auto_target="registry"
                auto_registry="${registry}"
                auto_image_name="${image_name}"
                ;;
            *)
                echo -e "${RED}无效的选项${NC}"
                return 1
                ;;
        esac
        
        # 询问是否要推送基础镜像
        read -p "是否同时推送基础镜像 (deep-learning-base)？(y/N): " push_base
        if [[ "$push_base" == "y" || "$push_base" == "Y" ]]; then
            auto_push_base=true
        fi
        
        # 询问是否要添加额外的标签
        read -p "是否添加额外的标签？(y/N): " add_tag
        if [[ "$add_tag" == "y" || "$add_tag" == "Y" ]]; then
            read -p "请输入标签 (例如: v1.0, stable): " extra_tag
            auto_tag="${extra_tag}"
            
            # 从target_image中提取基本名称（不含:latest）
            base_target_image=${target_image%:latest}
            
            # 为当前镜像添加额外标签
            echo -e "${YELLOW}为当前镜像添加标签: ${base_target_image}:${extra_tag}${NC}"
            docker tag deep-learning-env:latest ${base_target_image}:${extra_tag}
            
            # 如果需要推送基础镜像，也为其添加额外标签
            if [[ "$push_base" == "y" || "$push_base" == "Y" ]]; then
                base_image_name=${base_target_image/deep-learning-env/deep-learning-base}
                echo -e "${YELLOW}为基础镜像添加标签: ${base_image_name}:${extra_tag}${NC}"
                docker tag deep-learning-base:latest ${base_image_name}:${extra_tag}
            fi
        fi
        
        # 询问是否保存配置用于自动推送
        read -p "是否保存此配置用于自动推送？(y/N): " save_config
        if [[ "$save_config" == "y" || "$save_config" == "Y" ]]; then
            # 询问保存位置
            echo -e "${YELLOW}请选择配置文件保存位置：${NC}"
            echo "1) 项目目录 (./docker_push_config)"
            echo "2) 用户主目录 (${HOME}/.docker_push_config)"
            read -p "请选择 [1-2]: " config_location
            
            local config_file=""
            case $config_location in
                1)
                    config_file="./docker_push_config"
                    ;;
                2)
                    config_file="${HOME}/.docker_push_config"
                    ;;
                *)
                    echo -e "${RED}无效的选项，将使用默认位置 (项目目录)${NC}"
                    config_file="./docker_push_config"
                    ;;
            esac
            
            # 创建配置文件
            cat > "${config_file}" << EOF
# Docker推送自动配置
# 由manage_images.sh生成于$(date)
auto_target="${auto_target}"
auto_username="${auto_username}"
auto_registry="${auto_registry}"
auto_image_name="${auto_image_name}"
auto_push_base=${auto_push_base}
auto_tag="${auto_tag}"
auto_private=${auto_private}
EOF
            chmod 600 "${config_file}"
            echo -e "${GREEN}已保存推送配置到 ${config_file}${NC}"
        fi
    else
        # 自动模式，使用配置文件中的设置
        if [ "${auto_target}" == "dockerhub" ]; then
            target_image="${auto_username}/${auto_image_name}:latest"
            echo -e "${YELLOW}自动模式：推送到Docker Hub (${target_image})${NC}"
            echo -e "${YELLOW}仓库类型: ${auto_private:+私有}${auto_private:+:+公开}${NC}"
        elif [ "${auto_target}" == "registry" ]; then
            target_image="${auto_registry}/${auto_image_name}:latest"
            echo -e "${YELLOW}自动模式：推送到自定义Registry (${target_image})${NC}"
        else
            echo -e "${RED}错误：无效的自动推送目标${NC}"
            return 1
        fi
        
        # 如果有额外标签
        if [ ! -z "${auto_tag}" ]; then
            base_target_image=${target_image%:latest}
            echo -e "${YELLOW}为当前镜像添加标签: ${base_target_image}:${auto_tag}${NC}"
            docker tag deep-learning-env:latest ${base_target_image}:${auto_tag}
            
            if [ "${auto_push_base}" = true ]; then
                base_image_name=${base_target_image/deep-learning-env/deep-learning-base}
                echo -e "${YELLOW}为基础镜像添加标签: ${base_image_name}:${auto_tag}${NC}"
                docker tag deep-learning-base:latest ${base_image_name}:${auto_tag}
            fi
        fi
    fi
    
    # 为当前镜像添加目标标签
    echo -e "${YELLOW}为当前镜像添加标签: ${target_image}${NC}"
    docker tag deep-learning-env:latest ${target_image}
    
    # 推送当前镜像
    echo -e "${YELLOW}推送镜像: ${target_image}${NC}"
    docker push ${target_image}
    push_result=$?
    
    if [ $push_result -ne 0 ]; then
        echo -e "${RED}推送失败！请检查网络连接和登录状态${NC}"
        if [ "$auto_mode" = true ]; then
            echo "推送失败：${target_image}" >> "${HOME}/docker_push_errors.log"
        fi
        return 1
    fi
    
    # 如果添加了额外标签，也推送它
    if [ ! -z "${auto_tag}" ] || [[ "$add_tag" == "y" || "$add_tag" == "Y" ]]; then
        extra_tag=${auto_tag:-$extra_tag}
        base_target_image=${target_image%:latest}
        echo -e "${YELLOW}推送镜像: ${base_target_image}:${extra_tag}${NC}"
        docker push ${base_target_image}:${extra_tag}
        if [ $? -ne 0 ]; then
            echo -e "${RED}推送标签镜像失败！${NC}"
            return 1
        fi
    fi
    
    # 如果需要推送基础镜像
    if [ "${auto_push_base}" = true ] || [[ "$push_base" == "y" || "$push_base" == "Y" ]]; then
        # 构建基础镜像的目标名称
        base_target_image=${target_image/deep-learning-env/deep-learning-base}
        
        # 为基础镜像添加目标标签
        echo -e "${YELLOW}为基础镜像添加标签: ${base_target_image}${NC}"
        docker tag deep-learning-base:latest ${base_target_image}
        
        # 推送基础镜像
        echo -e "${YELLOW}推送基础镜像: ${base_target_image}${NC}"
        docker push ${base_target_image}
        if [ $? -ne 0 ]; then
            echo -e "${RED}推送基础镜像失败！${NC}"
            return 1
        fi
        
        # 如果添加了额外标签，也推送它
        if [ ! -z "${auto_tag}" ] || [[ "$add_tag" == "y" || "$add_tag" == "Y" ]]; then
            extra_tag=${auto_tag:-$extra_tag}
            base_image_name=${base_target_image%:latest}
            echo -e "${YELLOW}推送基础镜像: ${base_image_name}:${extra_tag}${NC}"
            docker push ${base_image_name}:${extra_tag}
            if [ $? -ne 0 ]; then
                echo -e "${RED}推送基础镜像标签失败！${NC}"
                return 1
            fi
        fi
    fi
    
    echo -e "${GREEN}镜像推送完成！${NC}"
    return 0
}

# 通过导出/导入方式压缩镜像
compress_image() {
    # 检查容器是否在运行
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${RED}错误：容器正在运行！${NC}"
        echo -e "${YELLOW}请先停止容器：$0 stop${NC}"
        return 1
    fi
    
    # 检查jq是否已安装
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}警告：未检测到jq命令，需要安装jq才能继续${NC}"
        
        # 检查是否有sudo权限
        local has_sudo=false
        if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
            has_sudo=true
        fi
        
        if [ "$has_sudo" = true ]; then
            echo -e "${YELLOW}检测到您有sudo权限，将尝试安装jq...${NC}"
            if command -v apt-get &> /dev/null; then
                echo -e "${YELLOW}使用apt-get安装jq...${NC}"
                sudo apt-get update && sudo apt-get install -y jq
            elif command -v yum &> /dev/null; then
                echo -e "${YELLOW}使用yum安装jq...${NC}"
                sudo yum install -y jq
            elif command -v apk &> /dev/null; then
                echo -e "${YELLOW}使用apk安装jq...${NC}"
                sudo apk add --no-cache jq
            else
                echo -e "${RED}错误：无法自动安装jq${NC}"
                echo -e "${YELLOW}请手动安装jq后再试：${NC}"
                echo -e "  - Debian/Ubuntu: sudo apt-get install jq"
                echo -e "  - CentOS/RHEL: sudo yum install jq"
                echo -e "  - Alpine: sudo apk add jq"
                return 1
            fi
        else
            echo -e "${RED}您没有sudo权限，无法自动安装jq${NC}"
            echo -e "${YELLOW}请联系系统管理员安装jq，或使用以下命令手动安装：${NC}"
            echo -e "  - Debian/Ubuntu: sudo apt-get install jq"
            echo -e "  - CentOS/RHEL: sudo yum install jq"
            echo -e "  - Alpine: sudo apk add jq"
            return 1
        fi
        
        # 再次检查jq是否已安装
        if ! command -v jq &> /dev/null; then
            echo -e "${RED}jq安装失败，无法继续${NC}"
            return 1
        else
            echo -e "${GREEN}jq安装成功，继续执行...${NC}"
        fi
    fi
    
    echo -e "${YELLOW}开始压缩镜像...${NC}"
    echo -e "${YELLOW}此过程可能需要较长时间，取决于镜像大小${NC}"
    
    # 获取当前时间作为标签
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
    
    # 备份当前镜像
    echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
    docker tag deep-learning-env:latest ${BACKUP_IMAGE_NAME}
    if [ $? -ne 0 ]; then
        echo -e "${RED}备份镜像失败！${NC}"
        return 1
    fi
    
    # 保存原始镜像的CMD和ENTRYPOINT
    echo -e "${YELLOW}保存原始镜像的CMD和ENTRYPOINT...${NC}"
    ORIGINAL_CMD=$(docker inspect --format='{{json .Config.Cmd}}' deep-learning-env:latest)
    ORIGINAL_ENTRYPOINT=$(docker inspect --format='{{json .Config.Entrypoint}}' deep-learning-env:latest)
    ORIGINAL_WORKDIR=$(docker inspect --format='{{.Config.WorkingDir}}' deep-learning-env:latest)
    ORIGINAL_ENV=$(docker inspect --format='{{json .Config.Env}}' deep-learning-env:latest)
    
    echo -e "${YELLOW}原始CMD: ${ORIGINAL_CMD}${NC}"
    echo -e "${YELLOW}原始ENTRYPOINT: ${ORIGINAL_ENTRYPOINT}${NC}"
    echo -e "${YELLOW}原始WORKDIR: ${ORIGINAL_WORKDIR}${NC}"
    
    # 创建临时容器
    echo -e "${YELLOW}创建临时容器...${NC}"
    CONTAINER_ID=$(docker create deep-learning-env:latest)
    if [ $? -ne 0 ]; then
        echo -e "${RED}创建临时容器失败！${NC}"
        return 1
    fi
    
    # 导出并重新导入容器（这会压缩镜像并移除历史层）
    echo -e "${YELLOW}导出并重新导入容器（这将压缩镜像并移除历史层）...${NC}"
    echo -e "${YELLOW}请耐心等待，此过程可能需要几分钟到几十分钟...${NC}"
    
    # 使用管道直接导出并导入，避免创建大型临时文件
    docker export ${CONTAINER_ID} | docker import - deep-learning-env:compressed
    if [ $? -ne 0 ]; then
        echo -e "${RED}导出/导入容器失败！${NC}"
        # 清理临时容器
        docker rm ${CONTAINER_ID} &>/dev/null
        return 1
    fi
    
    # 删除临时容器
    docker rm ${CONTAINER_ID}
    
    # 恢复CMD和ENTRYPOINT
    echo -e "${YELLOW}恢复CMD和ENTRYPOINT...${NC}"
    
    # 创建临时Dockerfile
    TEMP_DOCKERFILE=$(mktemp)
    if [ $? -ne 0 ]; then
        echo -e "${RED}创建临时Dockerfile失败！${NC}"
        # 清理中间镜像
        docker rmi deep-learning-env:compressed &>/dev/null
        return 1
    fi
    
    cat > "${TEMP_DOCKERFILE}" << EOF
FROM deep-learning-env:compressed
WORKDIR ${ORIGINAL_WORKDIR:-/workspace}
EOF
    
    # 添加ENV
    if [ "${ORIGINAL_ENV}" != "null" ] && [ "${ORIGINAL_ENV}" != "[]" ]; then
        echo -e "${YELLOW}恢复环境变量...${NC}"
        # 将JSON格式的环境变量转换为Dockerfile格式
        echo "${ORIGINAL_ENV}" | jq -r '.[]' 2>/dev/null | while read -r env_var; do
            echo "ENV ${env_var}" >> "${TEMP_DOCKERFILE}"
        done
    fi
    
    # 添加CMD
    if [ "${ORIGINAL_CMD}" != "null" ] && [ "${ORIGINAL_CMD}" != "[]" ]; then
        echo -e "${YELLOW}恢复CMD...${NC}"
        echo "CMD ${ORIGINAL_CMD}" >> "${TEMP_DOCKERFILE}"
    else
        echo -e "${YELLOW}设置默认CMD...${NC}"
        echo 'CMD ["/start_service.sh"]' >> "${TEMP_DOCKERFILE}"
    fi
    
    # 添加ENTRYPOINT
    if [ "${ORIGINAL_ENTRYPOINT}" != "null" ] && [ "${ORIGINAL_ENTRYPOINT}" != "[]" ]; then
        echo -e "${YELLOW}恢复ENTRYPOINT...${NC}"
        echo "ENTRYPOINT ${ORIGINAL_ENTRYPOINT}" >> "${TEMP_DOCKERFILE}"
    else
        echo -e "${YELLOW}设置默认ENTRYPOINT...${NC}"
        echo 'ENTRYPOINT ["/bin/bash", "-c"]' >> "${TEMP_DOCKERFILE}"
    fi
    
    # 使用临时Dockerfile构建最终镜像
    echo -e "${YELLOW}使用临时Dockerfile构建最终镜像...${NC}"
    docker build -t deep-learning-env:compressed_with_metadata -f "${TEMP_DOCKERFILE}" .
    build_result=$?
    
    # 删除临时Dockerfile
    rm "${TEMP_DOCKERFILE}"
    
    # 检查构建结果
    if [ $build_result -ne 0 ]; then
        echo -e "${RED}构建最终镜像失败！${NC}"
        # 清理中间镜像
        docker rmi deep-learning-env:compressed &>/dev/null
        return 1
    fi
    
    # 删除中间镜像
    docker rmi deep-learning-env:compressed
    
    # 显示压缩前后的大小对比
    echo -e "${YELLOW}压缩前后的镜像大小对比:${NC}"
    echo -e "原始镜像:"
    docker images deep-learning-env:latest --format "{{.Size}}"
    echo -e "压缩后的镜像:"
    docker images deep-learning-env:compressed_with_metadata --format "{{.Size}}"
    
    # 询问是否使用压缩后的镜像
    read -p "是否使用压缩后的镜像替换当前镜像？(y/N): " use_compressed
    if [[ "$use_compressed" == "y" || "$use_compressed" == "Y" ]]; then
        echo -e "${YELLOW}替换当前镜像...${NC}"
        docker tag deep-learning-env:compressed_with_metadata deep-learning-env:latest
        if [ $? -ne 0 ]; then
            echo -e "${RED}替换当前镜像失败！${NC}"
            echo -e "${YELLOW}压缩后的镜像仍然可用: deep-learning-env:compressed_with_metadata${NC}"
            return 1
        fi
        
        docker rmi deep-learning-env:compressed_with_metadata
        
        echo -e "${GREEN}镜像压缩完成！${NC}"
        echo -e "${GREEN}原镜像已备份为 ${BACKUP_IMAGE_NAME}${NC}"
        echo -e "${GREEN}CMD和ENTRYPOINT已成功恢复${NC}"
        echo -e "${YELLOW}您可以使用以下命令启动容器：${NC}"
        echo -e "$0 start"
    else
        echo -e "${YELLOW}保留压缩后的镜像为 deep-learning-env:compressed_with_metadata${NC}"
        echo -e "${YELLOW}您可以稍后手动使用它${NC}"
    fi
    
    return 0
}

# 设置镜像的启动命令(CMD)
set_cmd() {
    # 检查容器是否在运行
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${RED}错误：容器正在运行！${NC}"
        echo -e "${YELLOW}请先停止容器：$0 stop${NC}"
        return 1
    fi
    
    # 显示当前的CMD和ENTRYPOINT
    echo -e "${YELLOW}当前镜像的启动配置：${NC}"
    CURRENT_CMD=$(docker inspect --format='{{json .Config.Cmd}}' deep-learning-env:latest)
    CURRENT_ENTRYPOINT=$(docker inspect --format='{{json .Config.Entrypoint}}' deep-learning-env:latest)
    CURRENT_WORKDIR=$(docker inspect --format='{{.Config.WorkingDir}}' deep-learning-env:latest)
    
    echo -e "CMD: ${CURRENT_CMD}"
    echo -e "ENTRYPOINT: ${CURRENT_ENTRYPOINT}"
    echo -e "WORKDIR: ${CURRENT_WORKDIR}"
    echo
    
    # 询问用户要修改哪个配置
    echo -e "${YELLOW}请选择要修改的配置：${NC}"
    echo "1) CMD (启动命令)"
    echo "2) ENTRYPOINT (入口点)"
    echo "3) WORKDIR (工作目录)"
    echo "4) 全部重置为默认值"
    echo "5) 取消操作"
    
    read -p "请选择 [1-5]: " option
    
    case $option in
        1)
            echo -e "${YELLOW}请输入新的CMD命令${NC}"
            echo -e "格式示例: [\"/bin/bash\", \"-c\", \"echo hello\"]"
            echo -e "或者简单命令: \"/bin/bash\""
            read -p "新CMD: " new_cmd
            
            # 获取当前时间作为标签
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
            
            # 备份当前镜像
            echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
            docker tag deep-learning-env:latest ${BACKUP_IMAGE_NAME}
            
            # 创建临时Dockerfile
            TEMP_DOCKERFILE=$(mktemp)
            cat > "${TEMP_DOCKERFILE}" << EOF
FROM deep-learning-env:latest
CMD ${new_cmd}
EOF
            
            # 构建新镜像
            echo -e "${YELLOW}构建新镜像...${NC}"
            docker build -t deep-learning-env:latest -f "${TEMP_DOCKERFILE}" .
            
            # 删除临时Dockerfile
            rm "${TEMP_DOCKERFILE}"
            
            echo -e "${GREEN}CMD已更新！${NC}"
            ;;
        2)
            echo -e "${YELLOW}请输入新的ENTRYPOINT${NC}"
            echo -e "格式示例: [\"/bin/bash\", \"-c\"]"
            echo -e "或者简单命令: \"/bin/bash\""
            read -p "新ENTRYPOINT: " new_entrypoint
            
            # 获取当前时间作为标签
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
            
            # 备份当前镜像
            echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
            docker tag deep-learning-env:latest ${BACKUP_IMAGE_NAME}
            
            # 创建临时Dockerfile
            TEMP_DOCKERFILE=$(mktemp)
            cat > "${TEMP_DOCKERFILE}" << EOF
FROM deep-learning-env:latest
ENTRYPOINT ${new_entrypoint}
EOF
            
            # 构建新镜像
            echo -e "${YELLOW}构建新镜像...${NC}"
            docker build -t deep-learning-env:latest -f "${TEMP_DOCKERFILE}" .
            
            # 删除临时Dockerfile
            rm "${TEMP_DOCKERFILE}"
            
            echo -e "${GREEN}ENTRYPOINT已更新！${NC}"
            ;;
        3)
            echo -e "${YELLOW}请输入新的工作目录${NC}"
            echo -e "格式示例: /workspace"
            read -p "新WORKDIR: " new_workdir
            
            # 获取当前时间作为标签
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
            
            # 备份当前镜像
            echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
            docker tag deep-learning-env:latest ${BACKUP_IMAGE_NAME}
            
            # 创建临时Dockerfile
            TEMP_DOCKERFILE=$(mktemp)
            cat > "${TEMP_DOCKERFILE}" << EOF
FROM deep-learning-env:latest
WORKDIR ${new_workdir}
EOF
            
            # 构建新镜像
            echo -e "${YELLOW}构建新镜像...${NC}"
            docker build -t deep-learning-env:latest -f "${TEMP_DOCKERFILE}" .
            
            # 删除临时Dockerfile
            rm "${TEMP_DOCKERFILE}"
            
            echo -e "${GREEN}WORKDIR已更新！${NC}"
            ;;
        4)
            echo -e "${YELLOW}将重置所有配置为默认值...${NC}"
            
            # 获取当前时间作为标签
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            BACKUP_IMAGE_NAME="deep-learning-env:backup_${TIMESTAMP}"
            
            # 备份当前镜像
            echo -e "${YELLOW}备份当前镜像为 ${BACKUP_IMAGE_NAME}...${NC}"
            docker tag deep-learning-env:latest ${BACKUP_IMAGE_NAME}
            
            # 创建临时Dockerfile
            TEMP_DOCKERFILE=$(mktemp)
            cat > "${TEMP_DOCKERFILE}" << EOF
FROM deep-learning-env:latest
WORKDIR /workspace
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/start_service.sh"]
EOF
            
            # 构建新镜像
            echo -e "${YELLOW}构建新镜像...${NC}"
            docker build -t deep-learning-env:latest -f "${TEMP_DOCKERFILE}" .
            
            # 删除临时Dockerfile
            rm "${TEMP_DOCKERFILE}"
            
            echo -e "${GREEN}所有配置已重置为默认值！${NC}"
            ;;
        5)
            echo -e "${GREEN}操作已取消${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}无效的选项${NC}"
            return 1
            ;;
    esac
    
    echo -e "${YELLOW}您可以使用以下命令启动容器：${NC}"
    echo -e "$0 start"
    
    return 0
}

# 设置定期自动保存
setup_cron() {
    # 获取当前目录的绝对路径
    CURRENT_DIR=$(pwd)
    SCRIPT_PATH="${CURRENT_DIR}/$(basename "$0")"

    # 检查脚本是否可执行
    if [ ! -x "$SCRIPT_PATH" ]; then
        echo -e "${RED}错误：${SCRIPT_PATH} 不可执行${NC}"
        echo -e "${YELLOW}正在尝试修复权限...${NC}"
        chmod +x "$SCRIPT_PATH" 2>/dev/null
        
        if [ ! -x "$SCRIPT_PATH" ]; then
            echo -e "${RED}无法修复权限，请检查文件是否存在${NC}"
            return 1
        fi
    fi

    echo -e "${YELLOW}请选择定期执行的频率：${NC}"
    echo "1) 每天执行一次"
    echo "2) 每周执行一次"
    echo "3) 每月执行一次"
    echo "4) 自定义cron表达式"
    echo "5) 取消定期执行"
    read -p "请选择 [1-5]: " option

    case $option in
        1)
            read -p "请输入每天执行的时间 (格式: HH:MM，例如 03:30): " time
            hour=${time%:*}
            minute=${time#*:}
            cron_expression="$minute $hour * * *"
            frequency_text="每天 $time"
            ;;
        2)
            read -p "请输入每周执行的星期几 (0-6，0表示周日): " day_of_week
            read -p "请输入执行时间 (格式: HH:MM): " time
            hour=${time%:*}
            minute=${time#*:}
            cron_expression="$minute $hour * * $day_of_week"
            
            # 将数字转换为星期几的文字描述
            days=("周日" "周一" "周二" "周三" "周四" "周五" "周六")
            frequency_text="每周${days[$day_of_week]} $time"
            ;;
        3)
            read -p "请输入每月执行的日期 (1-31): " day_of_month
            read -p "请输入执行时间 (格式: HH:MM): " time
            hour=${time%:*}
            minute=${time#*:}
            cron_expression="$minute $hour $day_of_month * *"
            frequency_text="每月 $day_of_month 日 $time"
            ;;
        4)
            read -p "请输入自定义cron表达式 (格式: 分 时 日 月 星期): " cron_expression
            frequency_text="自定义频率: $cron_expression"
            ;;
        5)
            # 移除现有的cron任务
            (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH") | crontab -
            echo -e "${GREEN}已取消定期执行任务${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}无效的选项${NC}"
            return 1
            ;;
    esac

    # 询问是否在保存前自动清理容器内的缓存文件
    read -p "是否在保存前自动清理容器内的缓存文件？(y/N): " auto_clean
    auto_clean_cmd=""
    if [[ "$auto_clean" == "y" || "$auto_clean" == "Y" ]]; then
        auto_clean_cmd="clean && "
    fi

    # 询问是否在保存后自动推送镜像
    read -p "是否在保存后自动推送镜像？(y/N): " auto_push
    auto_push_cmd=""
    if [[ "$auto_push" == "y" || "$auto_push" == "Y" ]]; then
        # 检查是否已配置自动推送
        local config_exists=false
        if [ -f "./docker_push_config" ]; then
            config_exists=true
            echo -e "${GREEN}检测到项目目录中的自动推送配置${NC}"
            auto_push_cmd=" && $SCRIPT_PATH push auto skip_save_check"
        elif [ -f "${HOME}/.docker_push_config" ]; then
            config_exists=true
            echo -e "${GREEN}检测到用户主目录中的自动推送配置${NC}"
            auto_push_cmd=" && $SCRIPT_PATH push auto skip_save_check"
        fi
        
        if [ "$config_exists" = false ]; then
            echo -e "${YELLOW}未检测到自动推送配置${NC}"
            echo -e "${YELLOW}请先配置自动推送${NC}"
            read -p "是否现在配置自动推送？(y/N): " setup_push_now
            if [[ "$setup_push_now" == "y" || "$setup_push_now" == "Y" ]]; then
                # 调用push_image函数，传递skip_save_check参数
                push_image "skip_save_check"
                
                # 检查配置文件是否已创建
                if [ -f "./docker_push_config" ] || [ -f "${HOME}/.docker_push_config" ]; then
                    echo -e "${GREEN}自动推送配置已完成${NC}"
                    auto_push_cmd=" && $SCRIPT_PATH push auto skip_save_check"
                else
                    echo -e "${RED}自动推送配置失败，将不会自动推送${NC}"
                    auto_push_cmd=""
                fi
            else
                echo -e "${YELLOW}跳过自动推送配置${NC}"
                auto_push_cmd=""
            fi
        fi
    fi

    # 创建临时文件
    TEMP_CRON=$(mktemp)
    if [ $? -ne 0 ]; then
        echo -e "${RED}创建临时文件失败！${NC}"
        return 1
    fi

    # 获取现有的crontab内容，移除旧的相同任务
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH") > "$TEMP_CRON"

    # 添加新的cron任务
    echo "# 自动备份并重启deep-learning容器" >> "$TEMP_CRON"
    echo "$cron_expression $SCRIPT_PATH ${auto_clean_cmd}save${auto_push_cmd} >> ${CURRENT_DIR}/container_restart.log 2>&1" >> "$TEMP_CRON"

    # 应用新的crontab
    crontab "$TEMP_CRON"
    crontab_result=$?
    rm "$TEMP_CRON"
    
    if [ $crontab_result -ne 0 ]; then
        echo -e "${RED}设置crontab失败！${NC}"
        return 1
    fi

    echo -e "${GREEN}已成功设置定期执行任务：${frequency_text}${NC}"
    if [[ "$auto_clean" == "y" || "$auto_clean" == "Y" ]]; then
        echo -e "${GREEN}已启用自动清理容器${NC}"
    fi
    if [[ "$auto_push" == "y" || "$auto_push" == "Y" ]] && [ ! -z "$auto_push_cmd" ]; then
        echo -e "${GREEN}已启用自动推送镜像${NC}"
    fi
    echo -e "${YELLOW}执行日志将保存在：${CURRENT_DIR}/container_restart.log${NC}"
    echo -e "${YELLOW}您可以随时运行此命令修改或取消定期执行${NC}"

    # 显示当前的cron任务
    echo -e "${YELLOW}当前的cron任务：${NC}"
    crontab -l | grep -v "^#" | grep -v "^$"
    
    return 0
}

# 列出所有备份镜像
list_backups() {
    echo -e "${YELLOW}备份镜像列表：${NC}"
    docker images "deep-learning-env:backup_*" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}"
    
    return 0
}

# 清理旧的备份镜像
clean_backups() {
    echo -e "${YELLOW}备份镜像列表：${NC}"
    docker images "deep-learning-env:backup_*" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}"
    
    echo
    echo -e "${YELLOW}清理选项：${NC}"
    echo "1) 保留最新的N个备份"
    echo "2) 删除特定的备份"
    echo "3) 删除所有备份"
    echo "4) 取消操作"
    
    read -p "请选择操作 [1-4]: " option
    
    case $option in
        1)
            read -p "保留最新的几个备份？ " keep_count
            if [[ ! $keep_count =~ ^[0-9]+$ ]]; then
                echo -e "${RED}错误：请输入有效的数字${NC}"
                return 1
            fi
            
            # 获取所有备份镜像，按创建时间排序
            backups=($(docker images "deep-learning-env:backup_*" --format "{{.Repository}}:{{.Tag}}" | sort -r))
            
            if [ ${#backups[@]} -le $keep_count ]; then
                echo -e "${GREEN}当前备份数量(${#backups[@]})不超过要保留的数量($keep_count)，无需清理${NC}"
                return 0
            fi
            
            # 删除旧的备份
            for ((i=$keep_count; i<${#backups[@]}; i++)); do
                echo -e "${YELLOW}删除备份: ${backups[$i]}${NC}"
                docker rmi ${backups[$i]}
            done
            ;;
        2)
            read -p "请输入要删除的备份标签(例如 backup_20240601_120000): " tag
            if docker images "deep-learning-env:$tag" --format "{{.Repository}}:{{.Tag}}" | grep -q "deep-learning-env:$tag"; then
                echo -e "${YELLOW}删除备份: deep-learning-env:$tag${NC}"
                docker rmi deep-learning-env:$tag
            else
                echo -e "${RED}错误：找不到备份 deep-learning-env:$tag${NC}"
                return 1
            fi
            ;;
        3)
            read -p "确定要删除所有备份吗？这无法撤销！(y/N): " confirm
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                echo -e "${GREEN}操作已取消${NC}"
                return 0
            fi
            
            echo -e "${YELLOW}删除所有备份...${NC}"
            docker images "deep-learning-env:backup_*" --format "{{.Repository}}:{{.Tag}}" | xargs -r docker rmi
            ;;
        4)
            echo -e "${GREEN}操作已取消${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}无效的选项${NC}"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}清理完成！${NC}"
    return 0
}

# 恢复到指定的备份镜像
restore_backup() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}可用的备份镜像：${NC}"
        docker images "deep-learning-env:backup_*" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}"
        
        read -p "请输入要恢复的备份标签(例如 backup_20240601_120000): " tag
    else
        tag=$1
    fi
    
    if ! docker images "deep-learning-env:$tag" --format "{{.Repository}}:{{.Tag}}" | grep -q "deep-learning-env:$tag"; then
        echo -e "${RED}错误：找不到备份 deep-learning-env:$tag${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}将从备份 deep-learning-env:$tag 恢复...${NC}"
    read -p "这将覆盖当前的镜像，确定要继续吗？(y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo -e "${GREEN}操作已取消${NC}"
        return 0
    fi
    
    # 获取当前时间作为标签
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    CURRENT_BACKUP="deep-learning-env:pre_restore_${TIMESTAMP}"
    
    # 备份当前镜像
    echo -e "${YELLOW}备份当前镜像为 ${CURRENT_BACKUP}...${NC}"
    docker tag deep-learning-env:latest ${CURRENT_BACKUP}
    
    # 恢复备份镜像
    echo -e "${YELLOW}恢复备份镜像 deep-learning-env:$tag...${NC}"
    docker tag deep-learning-env:$tag deep-learning-env:latest
    
    # 重启容器
    echo -e "${YELLOW}重启容器...${NC}"
    ${DOCKER_COMPOSE_CMD} down
    ${DOCKER_COMPOSE_CMD} up -d
    
    # 等待容器启动
    echo -e "${YELLOW}等待容器启动...${NC}"
    sleep 5
    
    # 检查容器状态
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${GREEN}容器已成功重启！${NC}"
        echo -e "${GREEN}已恢复到备份 deep-learning-env:$tag${NC}"
        echo -e "${GREEN}之前的镜像已备份为 ${CURRENT_BACKUP}${NC}"
    else
        echo -e "${YELLOW}容器可能未正常启动，请检查日志：${NC}"
        ${DOCKER_COMPOSE_CMD} logs
    fi
    
    return 0
}

# 启动容器
start_container() {
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${YELLOW}容器已经在运行中${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}启动容器...${NC}"
    ${DOCKER_COMPOSE_CMD} up -d
    
    # 等待容器启动
    echo -e "${YELLOW}等待容器启动...${NC}"
    sleep 5
    
    # 检查容器状态
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${GREEN}容器已成功启动！${NC}"
    else
        echo -e "${RED}容器启动失败，请检查日志：${NC}"
        ${DOCKER_COMPOSE_CMD} logs
    fi
    
    return 0
}

# 停止容器
stop_container() {
    if ! docker ps | grep -q "deep-learning-env"; then
        echo -e "${YELLOW}容器未在运行${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}停止容器...${NC}"
    ${DOCKER_COMPOSE_CMD} down
    
    echo -e "${GREEN}容器已停止${NC}"
    return 0
}

# 重启容器
restart_container() {
    echo -e "${YELLOW}重启容器...${NC}"
    ${DOCKER_COMPOSE_CMD} down
    ${DOCKER_COMPOSE_CMD} up -d
    
    # 等待容器启动
    echo -e "${YELLOW}等待容器启动...${NC}"
    sleep 5
    
    # 检查容器状态
    if docker ps | grep -q "deep-learning-env"; then
        echo -e "${GREEN}容器已成功重启！${NC}"
    else
        echo -e "${RED}容器启动失败，请检查日志：${NC}"
        ${DOCKER_COMPOSE_CMD} logs
    fi
    
    return 0
}

# 查看容器日志
view_logs() {
    echo -e "${YELLOW}查看容器日志...${NC}"
    ${DOCKER_COMPOSE_CMD} logs
    
    return 0
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        return 0
    fi
    
    local command="$1"
    shift  # 移除第一个参数，剩余的参数可以传递给子命令
    
    case "$command" in
        init)
            init_environment
            ;;
        rebuild-base)
            rebuild_base
            ;;
        save)
            save_container
            ;;
        clean)
            clean_container
            ;;
        compress)
            compress_image
            ;;
        set-cmd)
            set_cmd
            ;;
        setup-cron)
            setup_cron
            ;;
        list-backups)
            list_backups
            ;;
        clean-backups)
            clean_backups
            ;;
        restore)
            restore_backup "$1"
            ;;
        start)
            start_container
            ;;
        stop)
            stop_container
            ;;
        restart)
            restart_container
            ;;
        logs)
            view_logs
            ;;
        push)
            push_image "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误：未知的命令 '$command'${NC}"
            show_help
            return 1
            ;;
    esac
    
    return $?
}

# 执行主函数
main "$@" 