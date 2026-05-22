#!/bin/bash
# ============================================================
# Chimera 性能基准测试脚本
# 测试各 Agent 的响应时间和吞吐量
# ============================================================

set -euo pipefail

CHIMERA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CHIMERA_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║     Chimera 性能基准测试                  ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
# 1. 导入时间
# ============================================================
echo -e "\n${BOLD}1. 模块导入时间${NC}"
echo "────────────────────────────────────────"

modules=(
    "core.config"
    "core.dag_engine"
    "core.engine_fingerprint"
    "core.knowledge_base"
    "agents.source_deconstructor"
    "agents.skeleton_analyzer"
    "agents.format_translator"
)

for mod in "${modules[@]}"; do
    start=$(date +%s%N)
    python3 -c "import sys; sys.path.insert(0,'.'); from $mod" 2>/dev/null
    end=$(date +%s%N)
    elapsed_ms=$(( (end - start) / 1000000 ))
    if [ $elapsed_ms -lt 50 ]; then
        echo -e "  ✅ $mod: ${GREEN}${elapsed_ms}ms${NC}"
    elif [ $elapsed_ms -lt 200 ]; then
        echo -e "  ⚠️  $mod: ${YELLOW}${elapsed_ms}ms${NC}"
    else
        echo -e "  ❌ $mod: ${elapsed_ms}ms (过慢)"
    fi
done

# ============================================================
# 2. DAG 拓扑排序性能
# ============================================================
echo -e "\n${BOLD}2. DAG 拓扑排序性能${NC}"
echo "────────────────────────────────────────"

python3 -c "
import sys, time
sys.path.insert(0, '.')
from core.dag_engine import DAGEngine

def create_complex_dag(size):
    dag = DAGEngine(timeout=10)
    for i in range(size):
        deps = [f'n{j}' for j in range(max(0, i-2), i)] if i > 0 else []
        dag.add_node(f'n{i}', lambda ctx: None, depends_on=deps)
    return dag

sizes = [10, 50, 100, 200]
for size in sizes:
    dag = create_complex_dag(size)
    start = time.perf_counter()
    dag._toposort()
    elapsed = (time.perf_counter() - start) * 1000
    print(f'  {size:>4} 节点: {elapsed:>7.2f}ms')
" 2>&1

# ============================================================
# 3. 引擎指纹识别性能
# ============================================================
echo -e "\n${BOLD}3. 引擎指纹识别性能${NC}"
echo "────────────────────────────────────────"

games=(
    "/mnt/hgfs/common/ItTakesTwo|ittakestwo"
    "/mnt/hgfs/common/Sifu|sifu"
    "/mnt/hgfs/common/Devil May Cry 5|dmc5"
    "/mnt/hgfs/common/Valheim|valheim"
)

for game in "${games[@]}"; do
    path="${game%%|*}"
    gid="${game##*|}"
    gname=$(basename "$path")
    if [ -d "$path" ]; then
        start=$(date +%s%N)
        python3 -c "
import sys; sys.path.insert(0,'.')
from core.engine_fingerprint import EngineFingerprinter
fp = EngineFingerprinter()
r = fp.identify('$path', '$gid')
print(f'{r.engine_display} ({r.confidence:.0%})')
" 2>/dev/null
        end=$(date +%s%N)
        elapsed_ms=$(( (end - start) / 1000000 ))
        echo -e "  ✅ $gname: ${GREEN}${elapsed_ms}ms${NC}"
    else
        echo -e "  ⏭️  $gname: 路径不存在"
    fi
done

# ============================================================
# 4. 知识库读写性能
# ============================================================
echo -e "\n${BOLD}4. 知识库读写性能${NC}"
echo "────────────────────────────────────────"

python3 -c "
import sys, time, tempfile, os
sys.path.insert(0, '.')
from core.knowledge_base import KnowledgeBase

tmpdir = tempfile.mkdtemp()
kb = KnowledgeBase(tmpdir)

# 写入性能
start = time.perf_counter()
for i in range(1000):
    kb.log_migration(f'G{i}', f'G{i+1}', 'Test', True, {})
write_time = (time.perf_counter() - start) * 1000

# 读取性能
start = time.perf_counter()
results = kb.query_migrations(limit=1000)
read_time = (time.perf_counter() - start) * 1000

print(f'  写入 1000 条: {write_time:.2f}ms ({1000/write_time*1000:.0f} 条/秒)')
print(f'  读取 1000 条: {read_time:.2f}ms ({1000/read_time*1000:.0f} 条/秒)')

import shutil
shutil.rmtree(tmpdir)
" 2>&1

# ============================================================
# 5. 内存占用
# ============================================================
echo -e "\n${BOLD}5. 内存占用${NC}"
echo "────────────────────────────────────────"

python3 -c "
import sys, os
sys.path.insert(0, '.')
import psutil
proc = psutil.Process()
mem_before = proc.memory_info().rss

from core.config import Config
from core.dag_engine import DAGEngine
from agents.orchestrator import ChimeraOrchestrator

mem_after = proc.memory_info().rss
delta = (mem_after - mem_before) / 1024 / 1024
total = mem_after / 1024 / 1024

print(f'  加载前:  {mem_before/1024/1024:.1f} MB')
print(f'  加载后:  {mem_after/1024/1024:.1f} MB')
print(f'  增量:    {delta:.1f} MB')
" 2>&1 || echo "  ⚠️ psutil 未安装，跳过内存测试"

# ============================================================
echo -e "\n${BOLD}${GREEN}✅ 基准测试完成${NC}"
echo ""
