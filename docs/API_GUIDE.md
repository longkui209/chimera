# Chimera API 使用指南

## 基础信息

- **Base URL**: `http://localhost:8004`
- **Swagger 文档**: `http://localhost:8004/docs`
- **ReDoc 文档**: `http://localhost:8004/redoc`
- **Content-Type**: `application/json`

## 端点总览

### 系统

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/docs` | Swagger UI |

### 流水线

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/pipeline/inspect` | 查看 DAG 结构 |
| POST | `/api/v1/migrate` | ⭐ 执行跨游戏迁移 |
| POST | `/api/v1/rollback` | 回滚迁移 |

### 引擎 & 游戏

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/games` | 列出可用游戏 |
| GET | `/api/v1/engines` | 列出支持引擎 |
| GET | `/api/v1/conversions` | 格式转换路径 |
| POST | `/api/v1/fingerprint` | 识别引擎 |

### 知识库

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/knowledge/stats` | 知识库统计 |
| GET | `/api/v1/knowledge/migrations` | 查询迁移历史 |

---

## 详细示例

### 1. 健康检查

```bash
curl http://localhost:8004/health
```

响应：
```json
{
  "status": "healthy",
  "service": "Chimera",
  "version": "0.1.0",
  "agents": 8,
  "dag_layers": 6
}
```

### 2. 识别游戏引擎

```bash
curl -X POST http://localhost:8004/api/v1/fingerprint \
  -H "Content-Type: application/json" \
  -d '{
    "game_path": "/mnt/hgfs/common/ItTakesTwo",
    "game_id": "ittakestwo"
  }'
```

响应：
```json
{
  "game_path": "/mnt/hgfs/common/ItTakesTwo",
  "engine": "ue4",
  "engine_display": "Unreal Engine 4/5",
  "confidence": 1.0,
  "evidence": ["已知游戏数据库匹配: 双人成行"],
  "encryption": "AES-ECB"
}
```

### 3. 查看 DAG 流水线

```bash
curl http://localhost:8004/api/v1/pipeline/inspect
```

响应：
```json
{
  "total_nodes": 7,
  "total_layers": 6,
  "layers": [
    {"level": 1, "nodes": ["source_deconstructor"], "parallel": 1},
    {"level": 2, "nodes": ["asset_extractor"], "parallel": 1},
    {"level": 3, "nodes": ["skeleton_analyzer"], "parallel": 1},
    {"level": 4, "nodes": ["anim_retargeter", "format_translator"], "parallel": 2},
    {"level": 5, "nodes": ["target_injector"], "parallel": 1},
    {"level": 6, "nodes": ["runtime_validator"], "parallel": 1}
  ]
}
```

### 4. 执行跨游戏迁移 ⭐

```bash
curl -X POST http://localhost:8004/api/v1/migrate \
  -H "Content-Type: application/json" \
  -d '{
    "source_game_path": "/mnt/hgfs/common/ItTakesTwo",
    "target_game_path": "/mnt/hgfs/common/Palworld",
    "source_game_id": "ittakestwo",
    "target_game_id": "palworld"
  }'
```

响应（同引擎快速迁移）：
```json
{
  "migration_id": "a1b2c3d4",
  "source_game": "ItTakesTwo",
  "target_game": "Palworld",
  "success": true,
  "elapsed_seconds": 45.2,
  "total_tokens": 8500000,
  "agent_results": {
    "source_deconstructor": {
      "engine": "ue4",
      "engine_display": "Unreal Engine 4/5",
      "confidence": 1.0
    },
    "asset_extractor": {
      "successfully_extracted": 3,
      "extracted": [...]
    },
    "skeleton_analyzer": {
      "mapped_count": 22,
      "mapping_confidence": 0.95
    },
    "anim_retargeter": {
      "strategy": "direct",
      "average_quality": 0.95
    },
    "format_translator": {
      "conversion_path": "ue4→ue4",
      "complexity": "low"
    },
    "target_injector": {
      "injection_method": "logicmods",
      "success": true
    },
    "runtime_validator": {
      "passed": true,
      "overall_score": 0.93
    }
  },
  "metrics": {
    "total_tokens": 8500000,
    "total_time": 45.2,
    "node_count": 7,
    "errors": 0
  }
}
```

### 5. 列出可用游戏

```bash
curl http://localhost:8004/api/v1/games
```

响应：
```json
{
  "games": [
    {
      "id": "ittakestwo",
      "name": "双人成行",
      "engine": "ue4",
      "size_gb": 46,
      "source": "known"
    },
    {
      "id": "black_myth_wukong",
      "name": "黑神话：悟空",
      "engine": "ue4",
      "size_gb": 140,
      "source": "known"
    }
  ],
  "total": 10
}
```

### 6. 格式转换路径

```bash
curl http://localhost:8004/api/v1/conversions
```

响应：
```json
{
  "paths": [
    {"source": "ue4", "target": "ue4", "complexity": "low", "intermediate": null},
    {"source": "ue4", "target": "unity", "complexity": "medium", "intermediate": "FBX"},
    {"source": "ue4", "target": "godot", "complexity": "high", "intermediate": "glTF 2.0"}
  ],
  "total": 7
}
```

### 7. 回滚迁移

```bash
curl -X POST http://localhost:8004/api/v1/rollback \
  -H "Content-Type: application/json" \
  -d '{"game_path": "/mnt/hgfs/common/Palworld"}'
```

响应：
```json
{
  "success": true,
  "files_restored": 12
}
```

### 8. 知识库统计

```bash
curl http://localhost:8004/api/v1/knowledge/stats
```

响应：
```json
{
  "total_migrations": 15,
  "successful": 12,
  "failed": 3,
  "skeleton_mappings": 8,
  "engine_pairs": ["ItTakesTwo→Palworld", "Sifu→Valheim"],
  "success_rate": 80.0
}
```

### 9. 查询迁移历史

```bash
# 查看最近 20 条
curl "http://localhost:8004/api/v1/knowledge/migrations?limit=20"

# 按源游戏筛选
curl "http://localhost:8004/api/v1/knowledge/migrations?source_game=ItTakesTwo&limit=10"
```

---

## Python SDK 示例

```python
import requests

API_BASE = "http://localhost:8004"

def identify_engine(game_path: str, game_id: str = None) -> dict:
    """识别游戏引擎"""
    resp = requests.post(
        f"{API_BASE}/api/v1/fingerprint",
        json={"game_path": game_path, "game_id": game_id},
    )
    return resp.json()

def migrate(source: str, target: str, src_id: str = None, tgt_id: str = None) -> dict:
    """执行跨游戏迁移"""
    resp = requests.post(
        f"{API_BASE}/api/v1/migrate",
        json={
            "source_game_path": source,
            "target_game_path": target,
            "source_game_id": src_id,
            "target_game_id": tgt_id,
        },
        timeout=600,  # 迁移可能需要几分钟
    )
    return resp.json()

def rollback(game_path: str) -> dict:
    """回滚"""
    resp = requests.post(
        f"{API_BASE}/api/v1/rollback",
        json={"game_path": game_path},
    )
    return resp.json()

# 使用示例
if __name__ == "__main__":
    # 识别引擎
    fp = identify_engine("/mnt/hgfs/common/ItTakesTwo", "ittakestwo")
    print(f"引擎: {fp['engine_display']} (置信度 {fp['confidence']:.0%})")

    # 执行迁移（谨慎！会修改目标游戏文件）
    # result = migrate("/mnt/hgfs/common/ItTakesTwo", "/mnt/hgfs/common/Palworld")
    # print(f"迁移 {'成功' if result['success'] else '失败'}")
    # print(f"耗时: {result['elapsed_seconds']}s")
    # print(f"Token: ~{result['total_tokens']:,}")
```

---

## 错误码参考

| HTTP 状态码 | 含义 | 处理方式 |
|------------|------|---------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式 |
| 404 | 游戏路径不存在 | 检查路径是否正确 |
| 422 | 参数验证失败 | 检查必填字段 |
| 500 | 服务器内部错误 | 查看日志 `logs/chimera_error.log` |

## 速率限制

- 单次迁移：最少 5 秒间隔
- 并发迁移：最多 2 个
- 批量迁移：建议使用 `BatchManager`

## 安全注意事项

1. **只读挂载游戏库**：生产环境应将游戏目录挂载为只读
2. **备份优先**：每次注入前自动备份，可在 `.chimera_backup/` 找到
3. **网络隔离**：Chimera 不需要外部网络访问游戏文件
4. **API 鉴权**：生产环境建议在 Nginx 层添加 HTTP Basic Auth 或 API Key
5. **日志审计**：所有迁移操作记录在 JSONL 日志中，定期审计

## 监控建议

```bash
# 健康检查脚本（适合 cron）
*/5 * * * * curl -sf http://localhost:8004/health || systemctl restart chimera

# 磁盘空间监控（知识库和日志会增长）
*/30 * * * * du -sh /data/chimera/knowledge/ /data/chimera/logs/

# Token 用量统计
curl -s http://localhost:8004/api/v1/knowledge/stats | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Migrations: {d[\"total_migrations\"]}, Success: {d[\"success_rate\"]:.1f}%')"
```

## 最佳实践

1. **先识别再迁移**：使用 `/fingerprint` 确认引擎类型
2. **同引擎优先**：UE4→UE4 比 UE4→Unity 快 5-10 倍
3. **备份重要**：迁移前自动备份，失败可用 `/rollback`
4. **从小游戏开始**：先用小游戏测试（Valheim 1.5GB 比 黑神话 140GB 快得多）
5. **查看知识库**：复用已有的骨骼映射和迁移经验
