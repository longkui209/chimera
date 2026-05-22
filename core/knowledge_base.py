"""
Chimera 知识库

存储跨游戏迁移的关键知识：
- 引擎格式映射
- 骨骼对应关系
- 迁移历史日志
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("chimera.knowledge")


class KnowledgeBase:
    """
    跨游戏迁移知识库

    核心数据：
    1. 引擎格式映射：记录各引擎的资产格式转换路径
    2. 骨骼映射表：记录角色间骨骼对应关系
    3. 迁移日志：记录每次成功/失败的迁移
    """

    def __init__(self, kb_path: str = "/data/chimera/knowledge"):
        self.path = Path(kb_path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = {}

    def get_engine_mapping(self, source_engine: str, target_engine: str) -> Optional[Dict]:
        """获取引擎间格式转换路径"""
        key = f"{source_engine}_to_{target_engine}"
        if key in self._cache:
            return self._cache[key]

        # 默认映射表
        default_mappings = {
            "ue4_to_ue4": {
                "path": "直接迁移",
                "complexity": "low",
                "steps": ["uasset 提取", "PAK 封包", "LogicMods 注入"],
            },
            "ue4_to_unity": {
                "path": "UE4 → FBX → Unity",
                "complexity": "medium",
                "steps": ["umodel 导出 FBX", "材质转换", "Unity AssetBundle 打包"],
            },
            "ue4_to_godot": {
                "path": "UE4 → glTF → Godot",
                "complexity": "high",
                "steps": ["umodel 导出 glTF", "骨架简化", "Godot .tres 生成"],
            },
            "unity_to_ue4": {
                "path": "Unity → FBX → UE4",
                "complexity": "medium",
                "steps": ["AssetRipper 提取", "FBX 导入 UE4", "材质重建"],
            },
            "godot_to_ue4": {
                "path": "Godot → glTF → UE4",
                "complexity": "high",
                "steps": ["glTF 提取", "UE4 导入", "材质蓝图重建"],
            },
            "re_to_ue4": {
                "path": "RE Engine → 中间格式 → UE4",
                "complexity": "very_high",
                "steps": ["RE Mesh 解析", "骨骼反推", "UE4 SkeletalMesh 构建"],
            },
        }

        return default_mappings.get(key)

    def save_skeleton_mapping(
        self,
        source_character: str,
        target_character: str,
        bone_pairs: list,
        confidence: float,
    ) -> None:
        """保存骨骼映射关系"""
        mapping_file = self.path / "skeleton_mappings.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source_character,
            "target": target_character,
            "bone_pairs": bone_pairs,
            "confidence": confidence,
        }
        with open(mapping_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(f"💾 骨骼映射已保存: {source_character} → {target_character} (置信度 {confidence:.0%})")

    def log_migration(
        self,
        source_game: str,
        target_game: str,
        character: str,
        success: bool,
        details: dict,
    ) -> None:
        """记录迁移日志"""
        log_file = self.path / "migration_log.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source_game": source_game,
            "target_game": target_game,
            "character": character,
            "success": success,
            "details": details,
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def query_migrations(self, source_game: str = None, limit: int = 50) -> list:
        """查询迁移历史"""
        log_file = self.path / "migration_log.jsonl"
        if not log_file.exists():
            return []

        results = []
        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if source_game and entry["source_game"] != source_game:
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def stats(self) -> Dict[str, Any]:
        """知识库统计"""
        stats = {
            "total_migrations": 0,
            "successful": 0,
            "failed": 0,
            "skeleton_mappings": 0,
            "engine_pairs": set(),
        }

        # 统计迁移日志
        log_file = self.path / "migration_log.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total_migrations"] += 1
                    if entry["success"]:
                        stats["successful"] += 1
                    else:
                        stats["failed"] += 1
                    stats["engine_pairs"].add(
                        f"{entry['source_game']}→{entry['target_game']}"
                    )

        # 统计骨骼映射
        mapping_file = self.path / "skeleton_mappings.jsonl"
        if mapping_file.exists():
            with open(mapping_file) as f:
                stats["skeleton_mappings"] = sum(1 for _ in f)

        stats["engine_pairs"] = list(stats["engine_pairs"])
        stats["success_rate"] = (
            stats["successful"] / stats["total_migrations"] * 100
            if stats["total_migrations"] > 0
            else 0
        )

        return stats
