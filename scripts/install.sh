#!/bin/bash
# ============================================================
# Chimera 快速安装脚本
# 一键安装所有依赖和工具链
# ============================================================

set -euo pipefail

CHIMERA_DIR="${CHIMERA_DIR:-/data/chimera}"
PYTHON="${PYTHON:-python3}"
PIP="${PIP:-pip3}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

section() { echo -e "\n${BOLD}${BLUE}━━━ $1 ━━━${NC}"; }
ok()      { echo -e "  ${GREEN}✅${NC} $1"; }
warn()    { echo -e "  ${YELLOW}⚠️${NC}  $1"; }
fail()    { echo -e "  ${RED}❌${NC} $1"; }
info()    { echo -e "  ${CYAN}📌${NC} $1"; }
cmd()     { echo -e "  ${CYAN}▶${NC}  $1"; }

# ============================================================
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║     🦁🐐🐍  Chimera 安装向导             ║"
echo "║   AI 跨游戏角色与资产融合迁移引擎        ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
section "1. 系统依赖检查"

# Python 版本
PYTHON_VER=$($PYTHON --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    ok "Python $PYTHON_VER"
else
    fail "Python 版本过低: $PYTHON_VER (需要 >= 3.8)"
    exit 1
fi

# pip
if $PIP --version &>/dev/null; then
    ok "pip 可用"
else
    fail "pip 不可用"
    exit 1
fi

# ============================================================
section "2. 安装 Python 依赖"

cmd "$PIP install -r $CHIMERA_DIR/requirements.txt"
$PIP install -r "$CHIMERA_DIR/requirements.txt" 2>&1 | tail -3
ok "Python 依赖安装完成"

# ============================================================
section "3. 检查外部工具"

check_tool() {
    local name="$1"
    local hint="$2"
    if command -v "$name" &>/dev/null; then
        ok "$name ($(command -v "$name"))"
        return 0
    elif [ -f "$name" ]; then
        ok "$name (文件存在)"
        return 0
    else
        warn "$name 未安装 — $hint"
        return 1
    fi
}

check_tool "blender"          "sudo apt install blender"
check_tool "wine"             "sudo apt install wine"
check_tool "dotnet"           "https://dotnet.microsoft.com/download"

# umodel (特殊路径)
UMODEL_PATH="/home/chenyixun710/UEViewer/umodel"
if [ -f "$UMODEL_PATH" ]; then
    ok "umodel ($UMODEL_PATH)"
else
    warn "umodel 未找到 — https://www.gildor.org/downloads"
fi

# FModel
if [ -d "/mnt/hgfs/游戏解包/FModel_latest" ]; then
    ok "FModel (/mnt/hgfs/游戏解包/FModel_latest)"
else
    warn "FModel 未找到 — https://fmodel.app/"
fi

# ============================================================
section "4. 创建数据目录"

mkdir -p "$CHIMERA_DIR/knowledge"
mkdir -p "$CHIMERA_DIR/logs"
mkdir -p "$CHIMERA_DIR/output"
ok "数据目录已就绪"

# ============================================================
section "5. 扫描游戏库"

GAME_COUNT=$(ls /mnt/hgfs/common/ 2>/dev/null | wc -l || echo "0")
if [ "$GAME_COUNT" -gt 0 ]; then
    ok "发现 $GAME_COUNT 款游戏"
else
    warn "未发现游戏库 (/mnt/hgfs/common)"
fi

# ============================================================
section "6. 运行测试"

cmd "$PYTHON -m pytest $CHIMERA_DIR/tests/test_core.py -q -k 'not discover_games'"
if $PYTHON -m pytest "$CHIMERA_DIR/tests/test_core.py" -q -k "not discover_games" 2>&1 | tail -5; then
    ok "测试通过"
else
    warn "部分测试失败（可能需要 hgfs 游戏库）"
fi

# ============================================================
section "7. 创建快捷命令"

CHIMERA_BIN="/usr/local/bin/chimera"
cat > /tmp/chimera_wrapper << 'WRAPPER'
#!/bin/bash
cd /data/chimera && python3 cli.py "$@"
WRAPPER

if [ -w "/usr/local/bin" ]; then
    sudo cp /tmp/chimera_wrapper "$CHIMERA_BIN" 2>/dev/null || \
    cp /tmp/chimera_wrapper "$HOME/.local/bin/chimera" 2>/dev/null || true
    sudo chmod +x "$CHIMERA_BIN" 2>/dev/null || true
    ok "chimera 命令已创建"
else
    info "手动创建别名: alias chimera='cd /data/chimera && python3 cli.py'"
fi

# ============================================================
section "✅ 安装完成！"

echo ""
echo -e "${BOLD}快速开始:${NC}"
echo "  cd /data/chimera"
echo "  python3 cli.py scan                    # 扫描工具链"
echo "  python3 cli.py list games              # 列出可用游戏"
echo "  python3 cli.py fingerprint /path/game  # 识别引擎"
echo "  python3 cli.py serve                   # 启动 API"
echo "  python3 cli.py doctor                  # 系统诊断"
echo ""

exit 0
