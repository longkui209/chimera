"""
Agent 2: 角色提取师 AssetExtractor

从源游戏中提取指定角色的完整资产：
- 骨骼网格 (SkeletalMesh)
- 骨架 (Skeleton)
- 动画 (Animation)
- 纹理 (Texture)
- 材质 (Material)
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import sys
from pathlib import Path as _Path
_sys_path = str(_Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

from core.config import Config

logger = logging.getLogger("chimera.asset_extractor")


class AssetExtractor:
    """
    角色提取师

    根据引擎类型选择合适的提取工具链：
    UE4/5: umodel / FModel / 自研 PAK 解析器
    Unity: AssetRipper / AssetStudio
    Godot: 自研 PCK 解析器
    RE Engine: 自研 PAK 解析器
    """

    # 已知提取工具路径
    TOOLS = {
        "umodel": "/home/chenyixun710/UEViewer/umodel",
        "fmodel": "/mnt/hgfs/游戏解包/FModel_latest",
        "quickbms": "/home/chenyixun710/quickbms.exe",
    }

    def extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取角色资产

        Args:
            context: 包含 bus、upstream_results（含源解构师输出）

        Returns:
            提取结果清单
        """
        bus = context.get("bus")
        upstream = context.get("upstream_results", {})

        # 获取上游数据
        source_characters = (
            (bus.get("source_characters") if bus else None) or
            upstream.get("source_characters", [])
        )
        source_engine = (
            (bus.get("source_engine") if bus else None) or
            upstream.get("source_engine", "unknown")
        )
        source_path = (
            (bus.get("source_game_path") if bus else None) or
            upstream.get("source_game_path", "")
        )

        if not source_characters:
            return {"error": "未找到角色资源", "extracted": []}

        logger.info(f"📦 开始提取角色资产 (引擎: {source_engine}, 角色候选: {len(source_characters)})")

        extracted = []
        errors = []

        for char in source_characters[:5]:  # 提取前5个角色
            try:
                result = self._extract_character(source_path, char, source_engine)
                if result:
                    extracted.append(result)
                    logger.info(f"  ✅ 提取成功: {char.get('name', 'unknown')} "
                                f"(网格: {result.get('meshes', 0)}, "
                                f"骨架: {result.get('skeletons', 0)}, "
                                f"纹理: {result.get('textures', 0)})")
            except Exception as e:
                errors.append({"character": char.get("name", "unknown"), "error": str(e)})
                logger.warning(f"  ❌ 提取失败: {char.get('name', 'unknown')} - {e}")

        report = {
            "total_candidates": len(source_characters),
            "successfully_extracted": len(extracted),
            "failed": len(errors),
            "extracted": extracted,
            "errors": errors,
        }

        if bus:
            bus.put("extracted_characters", extracted)
            bus.put("extraction_count", len(extracted))

        logger.info(f"✅ 角色提取完成: {len(extracted)}/{len(source_characters)} 成功")
        return report

    def _extract_character(
        self,
        game_path: str,
        char_info: Dict[str, Any],
        engine: str,
    ) -> Optional[Dict[str, Any]]:
        """提取单个角色资产"""
        char_path = Path(char_info.get("path", ""))
        char_name = char_info.get("name", "unknown")

        if not char_path.exists():
            return None

        # 根据引擎类型选择提取策略
        if engine == "ue4":
            return self._extract_ue4_character(char_path, char_name)
        elif engine == "unity":
            return self._extract_unity_character(char_path, char_name)
        elif engine == "godot":
            return self._extract_godot_character(char_path, char_name)
        elif engine == "re":
            return self._extract_re_character(char_path, char_name)
        else:
            return self._extract_generic(char_path, char_name)

    def _extract_ue4_character(self, char_path: Path, char_name: str) -> Dict[str, Any]:
        """提取 UE4/5 角色资产"""
        result = {
            "name": char_name,
            "path": str(char_path),
            "engine": "ue4",
            "meshes": [],
            "skeletons": [],
            "animations": [],
            "textures": [],
            "materials": [],
        }

        # 扫描骨骼网格
        for mesh_file in sorted(char_path.glob("SK_*.uasset")):
            result["meshes"].append({
                "file": mesh_file.name,
                "size_kb": round(mesh_file.stat().st_size / 1024, 1),
            })

        # 扫描骨架
        for skel_file in sorted(char_path.glob("*_Skeleton.uasset")):
            result["skeletons"].append({
                "file": skel_file.name,
                "size_kb": round(skel_file.stat().st_size / 1024, 1),
            })

        # 扫描动画蓝图
        for anim_file in sorted(char_path.glob("*_AnimBP*.uasset")):
            result["animations"].append({
                "file": anim_file.name,
                "size_kb": round(anim_file.stat().st_size / 1024, 1),
            })

        # 扫描纹理（常见纹理前缀）
        tex_patterns = ["T_*.uasset", "*_D.uasset", "*_N.uasset", "*_BC.uasset"]
        for pattern in tex_patterns:
            for tex_file in sorted(char_path.glob(pattern)):
                result["textures"].append({
                    "file": tex_file.name,
                    "size_kb": round(tex_file.stat().st_size / 1024, 1),
                })

        # 扫描材质
        for mat_file in sorted(char_path.glob("M_*.uasset")) + sorted(char_path.glob("MI_*.uasset")):
            result["materials"].append({
                "file": mat_file.name,
                "size_kb": round(mat_file.stat().st_size / 1024, 1),
            })

        # 统计
        result.update({
            "mesh_count": len(result["meshes"]),
            "skeleton_count": len(result["skeletons"]),
            "anim_count": len(result["animations"]),
            "texture_count": len(result["textures"]),
            "material_count": len(result["materials"]),
        })

        return result if result["mesh_count"] > 0 or result["skeleton_count"] > 0 else None

    def _extract_unity_character(self, char_path: Path, char_name: str) -> Dict[str, Any]:
        """提取 Unity 角色资产"""
        result = {
            "name": char_name,
            "path": str(char_path),
            "engine": "unity",
            "prefabs": [],
            "meshes": [],
            "animations": [],
        }

        for pf in char_path.glob("*.prefab"):
            result["prefabs"].append({"file": pf.name})
        for mesh in char_path.glob("*.mesh"):
            result["meshes"].append({"file": mesh.name})

        result["prefab_count"] = len(result["prefabs"])
        result["mesh_count"] = len(result["meshes"])

        return result if (result["prefab_count"] > 0 or result["mesh_count"] > 0) else None

    def _extract_godot_character(self, char_path: Path, char_name: str) -> Dict[str, Any]:
        """提取 Godot 角色资产"""
        result = {
            "name": char_name,
            "path": str(char_path),
            "engine": "godot",
            "scenes": [],
            "meshes": [],
            "animations": [],
        }

        for scn in char_path.glob("*.tscn"):
            result["scenes"].append({"file": scn.name})

        result["scene_count"] = len(result["scenes"])
        return result if result["scene_count"] > 0 else None

    def _extract_re_character(self, char_path: Path, char_name: str) -> Dict[str, Any]:
        """提取 RE Engine 角色资产"""
        result = {
            "name": char_name,
            "path": str(char_path),
            "engine": "re",
            "files": [],
        }

        for f in sorted(char_path.iterdir()):
            if f.is_file():
                result["files"].append({
                    "file": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })

        result["file_count"] = len(result["files"])
        return result if result["file_count"] > 0 else None

    def _extract_generic(self, char_path: Path, char_name: str) -> Dict[str, Any]:
        """通用提取（未知引擎）"""
        result = {
            "name": char_name,
            "path": str(char_path),
            "engine": "unknown",
            "files": [],
        }
        for f in sorted(char_path.iterdir())[:20]:
            if f.is_file():
                result["files"].append({
                    "file": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
        return result
