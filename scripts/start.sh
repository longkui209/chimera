#!/bin/bash
# ============================================================
# Chimera 快速启动脚本
# ============================================================

set -euo pipefail

CHIMERA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CHIMERA_DIR"

MODE="${1:-serve}"  # serve | scan | doctor | migrate

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

case "$MODE" in
    serve)
        echo -e "${GREEN}${BOLD}🚀 启动 Chimera API 服务...${NC}"
        echo -e "  地址: ${CYAN}http://0.0.0.0:8004${NC}"
        echo -e "  文档: ${CYAN}http://0.0.0.0:8004/docs${NC}"
        echo ""
        exec python3 cli.py serve --reload
        ;;

    scan)
        python3 cli.py scan
        ;;

    doctor)
        python3 cli.py doctor
        ;;

    daemon)
        echo -e "${GREEN}${BOLD}🦁🐐🐍 Chimera 后台服务启动...${NC}"
        nohup python3 -m uvicorn api.server:app \
            --host 0.0.0.0 \
            --port 8004 \
            --log-level info \
            > logs/chimera.log 2>&1 &
        PID=$!
        echo "  PID: $PID"
        echo "  日志: logs/chimera.log"
        echo $PID > /tmp/chimera.pid
        echo -e "${GREEN}✅ 服务已启动${NC}"

        # 等待启动完成
        sleep 2
        if curl -s http://localhost:8004/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 健康检查通过${NC}"
        else
            echo -e "${RED}❌ 健康检查失败，查看日志: tail -f $CHIMERA_DIR/logs/chimera.log${NC}"
        fi
        ;;

    stop)
        if [ -f /tmp/chimera.pid ]; then
            PID=$(cat /tmp/chimera.pid)
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo -e "${GREEN}✅ 已停止 Chimera (PID: $PID)${NC}"
            else
                echo -e "${YELLOW}⚠️ 进程不存在${NC}"
            fi
            rm -f /tmp/chimera.pid
        else
            # 查找进程
            PIDS=$(pgrep -f "uvicorn api.server:app" || true)
            if [ -n "$PIDS" ]; then
                echo "$PIDS" | xargs kill
                echo -e "${GREEN}✅ 已停止所有 Chimera 进程${NC}"
            else
                echo -e "${YELLOW}⚠️ 没有运行中的 Chimera 进程${NC}"
            fi
        fi
        ;;

    status)
        if [ -f /tmp/chimera.pid ]; then
            PID=$(cat /tmp/chimera.pid)
            if kill -0 "$PID" 2>/dev/null; then
                echo -e "${GREEN}✅ Chimera 运行中 (PID: $PID)${NC}"
                curl -s http://localhost:8004/health | python3 -m json.tool 2>/dev/null || true
            else
                echo -e "${RED}❌ Chimera 未运行${NC}"
            fi
        else
            if pgrep -f "uvicorn api.server:app" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Chimera 运行中${NC}"
            else
                echo -e "${RED}❌ Chimera 未运行${NC}"
            fi
        fi
        ;;

    migrate)
        if [ $# -lt 3 ]; then
            echo "用法: $0 migrate <源游戏路径> <目标游戏路径>"
            exit 1
        fi
        python3 cli.py migrate "$2" "$3"
        ;;

    *)
        echo "用法: $0 {serve|scan|doctor|daemon|stop|status|migrate}"
        echo ""
        echo "  serve    - 前台启动 API 服务（开发模式）"
        echo "  scan     - 扫描工具链"
        echo "  doctor   - 系统诊断"
        echo "  daemon   - 后台启动服务"
        echo "  stop     - 停止服务"
        echo "  status   - 查看服务状态"
        echo "  migrate  - 执行迁移（需指定源和目标路径）"
        exit 1
        ;;
esac
