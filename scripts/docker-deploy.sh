#!/bin/bash
# ============================================================
# Chimera Docker 快速启动脚本
# 一键构建 + 启动 + 健康检查
# ============================================================

set -euo pipefail

CHIMERA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CHIMERA_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║     Chimera Docker 快速部署              ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 1. 检查 Docker
if ! command -v docker &>/dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "  安装: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
echo -e "✅ Docker: $(docker --version)"

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    echo -e "${RED}❌ docker-compose 未安装${NC}"
    exit 1
fi
echo -e "✅ docker-compose: $(docker-compose --version 2>/dev/null || docker compose version)"

# 2. 构建
echo -e "\n${BOLD}📦 构建镜像...${NC}"
docker build -f docker/Dockerfile -t chimera:latest . 2>&1 | tail -5
echo -e "${GREEN}✅ 镜像构建完成${NC}"

# 3. 创建必要目录
mkdir -p logs output knowledge

# 4. 启动
echo -e "\n${BOLD}🚀 启动容器...${NC}"
CONTAINER_NAME="chimera-$(date +%s)"

docker run -d \
    --name "$CONTAINER_NAME" \
    -p 8004:8004 \
    -v "$(pwd)/knowledge:/app/chimera/knowledge" \
    -v "$(pwd)/logs:/app/chimera/logs" \
    -v "/mnt/hgfs/common:/data/games:ro" \
    -e CHIMERA_API_HOST=0.0.0.0 \
    -e CHIMERA_API_PORT=8004 \
    --restart unless-stopped \
    chimera:latest

echo -e "${GREEN}✅ 容器已启动: $CONTAINER_NAME${NC}"

# 5. 健康检查
echo -e "\n${BOLD}🏥 等待服务就绪...${NC}"
for i in $(seq 1 20); do
    if curl -sf http://localhost:8004/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务就绪 (${i}s)${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}❌ 服务启动超时${NC}"
        echo "  日志: docker logs $CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done

# 6. 显示信息
echo ""
echo -e "${BOLD}${GREEN}🎉 Chimera 部署成功！${NC}"
echo ""
echo "  容器名:    $CONTAINER_NAME"
echo "  API:       http://localhost:8004"
echo "  文档:      http://localhost:8004/docs"
echo "  健康检查:  http://localhost:8004/health"
echo ""
echo "  管理命令:"
echo "    docker logs $CONTAINER_NAME     # 查看日志"
echo "    docker stop $CONTAINER_NAME     # 停止"
echo "    docker rm $CONTAINER_NAME       # 删除"
echo ""
