# Chimera 开发指南

## 快速开始

```bash
# 1. 安装
cd /data/chimera
pip install -r requirements.txt

# 2. 扫描工具链
python3 cli.py scan

# 3. 识别游戏引擎
python3 cli.py fingerprint /mnt/hgfs/common/ItTakesTwo --id ittakestwo

# 4. 运行测试
python3 -m pytest tests/test_core.py -v -k "not discover_games"

# 5. 启动 API
python3 cli.py serve
```

## 项目结构

```
chimera/
├── README.md               # 项目文档（面向用户）
├── ARCHITECTURE.md          # 架构文档（面向开发者）
├── Makefile                 # 构建命令
├── cli.py                   # CLI 入口
├── requirements.txt         # Python 依赖
│
├── agents/                  # 8 个 AI Agent
│   ├── source_deconstructor.py
│   ├── asset_extractor.py
│   ├── skeleton_analyzer.py
│   ├── anim_retargeter.py
│   ├── format_translator.py
│   ├── target_injector.py
│   ├── runtime_validator.py
│   └── orchestrator.py
│
├── core/                    # 核心引擎
│   ├── config.py            # 配置·引擎库·游戏注册表
│   ├── dag_engine.py        # DAG 编排引擎
│   ├── engine_fingerprint.py # 引擎指纹识别
│   └── knowledge_base.py    # 知识库
│
├── api/                     # REST API
│   └── server.py            # FastAPI 服务
│
├── tools/                   # 工具链
│   └── toolchain.py         # 工具发现·管理
│
├── tests/                   # 测试
│   └── test_core.py         # 43+ 测试用例
│
├── scripts/                 # Shell 脚本
│   ├── install.sh           # 一键安装
│   └── start.sh             # 启动/停止/状态
│
├── docker/                  # Docker 支持
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── config/                  # 配置文件
│   ├── .env.example         # 环境变量示例
│   ├── chimera.service      # systemd 服务
│   └── recipes.json         # 迁移配方
│
├── dashboard/               # Web Dashboard
│   └── index.html           # 单页监控面板
│
└── docs/                    # 文档
    └── ARCHITECTURE.md       # 架构详解
```

## 添加新的游戏

在 `core/config.py` 的 `KNOWN_GAMES` 中添加：

```python
"new_game": {
    "path": "/mnt/hgfs/common/NewGame",
    "engine": "ue4",       # ue4 | unity | godot | re | source2
    "display_name": "新游戏",
    "size_gb": 50,
}
```

## 添加新的迁移配方

在 `config/recipes.json` 的 `recipes` 数组中添加：

```json
{
    "id": "my_recipe",
    "name": "配方名称",
    "source": {"game_id": "src", "engine": "ue4", "character": "Hero"},
    "target": {"game_id": "dst", "engine": "unity", "injection": "bepinex"},
    "complexity": "medium",
    "estimated_time": "20-30 min",
    "estimated_tokens": "10M"
}
```

## 运行测试

```bash
# 快速（跳过 hgfs 测试）
make test

# 完整
make test-all

# 单个文件
python3 -m pytest tests/test_core.py::TestDAGEngine -v
```

## API 使用

```bash
# 健康检查
curl http://localhost:8004/health

# 识别引擎
curl -X POST http://localhost:8004/api/v1/fingerprint \
  -H "Content-Type: application/json" \
  -d '{"game_path": "/mnt/hgfs/common/ItTakesTwo", "game_id": "ittakestwo"}'

# 执行迁移
curl -X POST http://localhost:8004/api/v1/migrate \
  -H "Content-Type: application/json" \
  -d '{"source_game_path": "/path/to/source", "target_game_path": "/path/to/target"}'
```

## Docker 部署

```bash
# 构建
make docker-build

# 启动
make docker-up

# 日志
make docker-logs

# 停止
make docker-down
```

## 常用命令

```bash
make install     # 安装依赖
make test        # 运行测试
make serve       # 启动服务
make daemon      # 后台启动
make stop        # 停止
make status      # 状态
make scan        # 工具链扫描
make doctor      # 系统诊断
make loc         # 代码统计
make clean       # 清理缓存
```
