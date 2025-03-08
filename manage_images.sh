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

# 保存容器状态并重启
save_container() {
    # 检查容器是否在运行
    if ! docker ps | grep -q "deep-learning-env"; then
        echo -e "${RED}错误：容器 deep-learning-env 未运行！${NC}"
        echo -e "${YELLOW}请先启动容器：$0 start${NC}"
        return 1
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
    
    if [ ! -z "$1" ] && [ "$1" == "auto" ]; then
        auto_mode=true
        
        # 读取配置文件
        if [ -f "${HOME}/.docker_push_config" ]; then
            source "${HOME}/.docker_push_config"
            echo -e "${YELLOW}已读取自动推送配置${NC}"
        else
            echo -e "${RED}错误：未找到自动推送配置文件${NC}"
            echo -e "${YELLOW}请先运行 $0 push 并设置自动推送配置${NC}"
            return 1
        fi
    fi
    
    # 检查容器是否在运行（非自动模式下）
    if ! $auto_mode && docker ps | grep -q "deep-learning-env"; then
        echo -e "${YELLOW}检测到容器正在运行${NC}"
        read -p "是否先保存当前容器状态？(y/N): " save_first
        if [[ "$save_first" == "y" || "$save_first" == "Y" ]]; then
            save_container
        fi
    fi
    
    if ! $auto_mode; then
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
            # 创建配置文件
            cat > "${HOME}/.docker_push_config" << EOF
# Docker推送自动配置
# 由manage_images.sh生成于$(date)
auto_target="${auto_target}"
auto_username="${auto_username}"
auto_registry="${auto_registry}"
auto_image_name="${auto_image_name}"
auto_push_base=${auto_push_base}
auto_tag="${auto_tag}"
EOF
            chmod 600 "${HOME}/.docker_push_config"
            echo -e "${GREEN}已保存推送配置到 ${HOME}/.docker_push_config${NC}"
        fi
    else
        # 自动模式，使用配置文件中的设置
        if [ "${auto_target}" == "dockerhub" ]; then
            target_image="${auto_username}/${auto_image_name}:latest"
            echo -e "${YELLOW}自动模式：推送到Docker Hub (${target_image})${NC}"
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
        if $auto_mode; then
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
        
        # 如果添加了额外标签，也推送它
        if [ ! -z "${auto_tag}" ] || [[ "$add_tag" == "y" || "$add_tag" == "Y" ]]; then
            extra_tag=${auto_tag:-$extra_tag}
            base_image_name=${base_target_image%:latest}
            echo -e "${YELLOW}推送基础镜像: ${base_image_name}:${extra_tag}${NC}"
            docker push ${base_image_name}:${extra_tag}
        fi
    fi
    
    echo -e "${GREEN}镜像推送完成！${NC}"
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
    read -p "请输入选项 [1-5]: " option

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

    # 询问是否在保存后自动推送镜像
    read -p "是否在保存后自动推送镜像？(y/N): " auto_push
    auto_push_cmd=""
    if [[ "$auto_push" == "y" || "$auto_push" == "Y" ]]; then
        # 检查是否已配置自动推送
        if [ -f "${HOME}/.docker_push_config" ]; then
            echo -e "${GREEN}检测到自动推送配置${NC}"
            auto_push_cmd=" && $SCRIPT_PATH push auto"
        else
            echo -e "${YELLOW}未检测到自动推送配置${NC}"
            echo -e "${YELLOW}请先运行 $0 push 并设置自动推送配置${NC}"
            read -p "是否现在配置自动推送？(y/N): " setup_push_now
            if [[ "$setup_push_now" == "y" || "$setup_push_now" == "Y" ]]; then
                push_image
                if [ -f "${HOME}/.docker_push_config" ]; then
                    echo -e "${GREEN}自动推送配置已完成${NC}"
                    auto_push_cmd=" && $SCRIPT_PATH push auto"
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

    # 获取现有的crontab内容，移除旧的相同任务
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH") > "$TEMP_CRON"

    # 添加新的cron任务
    echo "# 自动备份并重启deep-learning容器" >> "$TEMP_CRON"
    echo "$cron_expression $SCRIPT_PATH save${auto_push_cmd} >> ${CURRENT_DIR}/container_restart.log 2>&1" >> "$TEMP_CRON"

    # 应用新的crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"

    echo -e "${GREEN}已成功设置定期执行任务：${frequency_text}${NC}"
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
    
    case "$1" in
        init)
            init_environment
            ;;
        rebuild-base)
            rebuild_base
            ;;
        save)
            save_container
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
            restore_backup "$2"
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
            push_image
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误：未知的命令 '$1'${NC}"
            show_help
            return 1
            ;;
    esac
    
    return $?
}

# 执行主函数
main "$@" 