#!/bin/bash
# ============================================================
# Chimera 清理脚本
# 清理缓存、临时文件、测试残留
# ============================================================

CHIMERA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CHIMERA_DIR"

echo "🧹 Chimera 清理..."

# Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "  ✅ Python 缓存已清理"

# Pytest 缓存
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
echo "  ✅ pytest 缓存已清理"

# 临时文件
rm -f /tmp/chimera*.jsonl 2>/dev/null
rm -f /tmp/chimera*.log 2>/dev/null
rm -f /tmp/chimera.pid 2>/dev/null
echo "  ✅ 临时文件已清理"

# 知识库（可选）
if [ "${1:-}" = "--all" ]; then
    rm -f knowledge/*.jsonl 2>/dev/null
    rm -f knowledge/*.json 2>/dev/null
    echo "  ✅ 知识库已重置"
fi

# 日志
if [ "${1:-}" = "--all" ]; then
    rm -f logs/*.log 2>/dev/null
    echo "  ✅ 日志已清理"
fi

echo ""
echo "✅ 清理完成"
echo "  使用 '--all' 参数可同时清理知识库和日志"
