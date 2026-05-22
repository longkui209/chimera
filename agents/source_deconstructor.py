"""
Agent 1: 源解构师 SourceDeconstructor

负责分析源游戏：引擎识别、资产结构扫描、加密检测、角色资源定位。
这是整个流水线的起点 —— 必须精准识别，否则下游全错。
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

import sys
from pathlib import Path as _Path
_sys_path = str(_Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

from core.engine_fingerprint import EngineFingerprinter
from core.config import Config

logger = logging.getLogger("chimera.source_deconstructor")


class SourceDeconstructor:
    """
    源解构师

    任务：
    1. 识别游戏引擎及版本
    2. 扫描资产目录结构
    3. 检测加密/压缩方案
    4. 定位角色相关资源路径
    """

    def __init__(self):
        self.fingerprinter = EngineFingerprinter()

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析源游戏

        Args:
            context: 包含 bus、game_path、game_id 等

        Returns:
            源游戏完整分析报告
        """
        bus = context.get("bus")
        game_path = context.get("upstream_results", {}).get("source_game_path") or \
                     (bus.get("source_game_path") if bus else None)
        game_id = context.get("upstream_results", {}).get("source_game_id") or \
                  (bus.get("source_game_id") if bus else None)

        if not game_path:
            return {"error": "未提供源游戏路径"}

        path = Path(game_path)
        logger.info(f"🔍 开始解构源游戏: {path.name}")

        # 1. 引擎指纹识别
        fingerprint = self.fingerprinter.identify(game_path, game_id)
        logger.info(f"🎯 引擎识别: {fingerprint.engine_display} (置信度 {fingerprint.confidence:.0%})")

        # 2. 资产目录结构扫描
        asset_structure = self._scan_asset_structure(path, fingerprint)

        # 3. 角色资源定位
        character_assets = self._locate_characters(path, fingerprint)

        # 4. 构建分析报告
        report = {
            "game_name": path.name,
            "game_path": str(path),
            "engine": fingerprint.engine,
            "engine_display": fingerprint.engine_display,
            "confidence": fingerprint.confidence,
            "evidence": fingerprint.evidence,
            "encryption": fingerprint.encryption,
            "asset_structure": asset_structure,
            "character_assets": character_assets,
            "profile": {
                "mesh_format": fingerprint.binary_format,
                "skeleton_format": fingerprint.profile.skeleton_format if fingerprint.profile else "",
                "anim_format": fingerprint.profile.anim_format if fingerprint.profile else "",
                "injection_methods": fingerprint.profile.injection_methods if fingerprint.profile else [],
            },
        }

        # 写入 ContextBus
        if bus:
            bus.put("source_engine", fingerprint.engine)
            bus.put("source_encryption", fingerprint.encryption)
            bus.put("source_characters", character_assets)

        logger.info(f"✅ 源解构完成: {fingerprint.engine_display}, "
                     f"发现 {len(character_assets)} 个角色资产组")
        return report

    def _scan_asset_structure(self, game_path: Path, fingerprint) -> Dict[str, Any]:
        """扫描资产目录结构"""
        structure = {
            "total_files": 0,
            "total_size_gb": 0,
            "directories": [],
            "file_types": {},
        }

        # 快速扫描顶层目录
        for item in sorted(game_path.iterdir()):
            if item.is_dir():
                structure["directories"].append({
                    "name": item.name,
                    "type": self._classify_directory(item.name),
                })

        # 统计文件类型分布
        ext_count = {}
        file_count = 0
        total_size = 0
        for f in game_path.rglob("*"):
            if f.is_file():
                ext = f.suffix.lower()
                ext_count[ext] = ext_count.get(ext, 0) + 1
                file_count += 1
                total_size += f.stat().st_size
                if file_count >= 10000:
                    break

        structure["total_files"] = file_count
        structure["total_size_gb"] = round(total_size / (1024**3), 2)
        structure["file_types"] = dict(
            sorted(ext_count.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return structure

    def _classify_directory(self, dirname: str) -> str:
        """分类目录类型"""
        dirname_lower = dirname.lower()
        if "content" in dirname_lower:
            return "content_root"
        if "character" in dirname_lower or "char" in dirname_lower:
            return "characters"
        if "anim" in dirname_lower:
            return "animations"
        if "texture" in dirname_lower:
            return "textures"
        if "audio" in dirname_lower or "sound" in dirname_lower:
            return "audio"
        if "plugin" in dirname_lower:
            return "plugins"
        if "bin" in dirname_lower:
            return "binaries"
        if "engine" in dirname_lower:
            return "engine"
        return "other"

    def _locate_characters(self, game_path: Path, fingerprint) -> List[Dict[str, Any]]:
        """定位角色相关资源"""
        characters = []
        engine = fingerprint.engine

        # 根据引擎类型使用不同搜索策略
        if engine == "ue4":
            # UE4: 搜索 SkeletalMesh 文件
            mesh_files = list(game_path.rglob("SK_*.uasset"))[:50]
            skeleton_files = list(game_path.rglob("*_Skeleton.uasset"))[:50]

            # 按目录分组
            char_dirs = set()
            for mf in mesh_files:
                char_dirs.add(mf.parent)
            for sf in skeleton_files:
                char_dirs.add(sf.parent)

            for cd in sorted(char_dirs):
                meshes = list(cd.glob("SK_*.uasset"))
                skeletons = list(cd.glob("*_Skeleton.uasset"))
                anims = list(cd.glob("*_AnimBP*.uasset"))
                textures = list(cd.glob("T_*.uasset")) + list(cd.glob("*_D.uasset"))

                if meshes or skeletons:
                    characters.append({
                        "path": str(cd),
                        "name": cd.name,
                        "skeletal_meshes": len(meshes),
                        "skeletons": len(skeletons),
                        "anim_blueprints": len(anims),
                        "textures": len(textures),
                    })

        elif engine == "unity":
            # Unity: 搜索 Character 相关 Prefab 和 Mesh
            prefab_files = list(game_path.rglob("*Character*.prefab"))[:50]
            for pf in prefab_files:
                characters.append({
                    "path": str(pf.parent),
                    "name": pf.stem,
                    "type": "prefab",
                })

        elif engine == "godot":
            # Godot: 搜索 .tscn 场景文件
            scene_files = list(game_path.rglob("*character*.tscn")) + \
                         list(game_path.rglob("*player*.tscn"))
            for sf in scene_files[:50]:
                characters.append({
                    "path": str(sf.parent),
                    "name": sf.stem,
                    "type": "scene",
                })

        elif engine == "re":
            # RE Engine: 搜索角色相关
            char_dirs = list(game_path.rglob("*char*"))[:50]
            for cd in char_dirs:
                if cd.is_dir():
                    characters.append({
                        "path": str(cd),
                        "name": cd.name,
                        "type": "character_dir",
                    })

        return characters[:20]  # 限制返回数量
