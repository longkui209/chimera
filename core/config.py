"""
Chimera 核心配置系统

管理引擎指纹、格式映射、Agent参数、运行时配置。
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path


@dataclass
class EngineProfile:
    """游戏引擎特征档案"""
    name: str
    display_name: str
    # 二进制指纹
    magic_bytes: List[bytes] = field(default_factory=list)
    file_extensions: List[str] = field(default_factory=list)
    encryption_clues: List[str] = field(default_factory=list)
    # 资产特征
    mesh_format: str = ""
    skeleton_format: str = ""
    anim_format: str = ""
    texture_format: str = ""
    material_format: str = ""
    # 注入方式
    injection_methods: List[str] = field(default_factory=list)


class Config:
    """Chimera 全局配置"""

    # === 引擎指纹库 ===
    ENGINES: Dict[str, EngineProfile] = {
        "ue4": EngineProfile(
            name="ue4",
            display_name="Unreal Engine 4/5",
            magic_bytes=[b"\x5A\x6F\x12\xE1"],  # PAK magic
            file_extensions=[".uasset", ".uexp", ".ubulk", ".pak"],
            encryption_clues=["AES-ECB", "AES-CBC", "PathHashIndex"],
            mesh_format="SkeletalMesh (.uasset)",
            skeleton_format="Skeleton (.uasset)",
            anim_format="AnimSequence (.uasset)",
            texture_format="Texture2D (.uasset)",
            material_format="Material (.uasset)",
            injection_methods=["pak_patch", "dll_hook", "logicmods"],
        ),
        "godot": EngineProfile(
            name="godot",
            display_name="Godot 4.x",
            magic_bytes=[b"GDPC"],
            file_extensions=[".pck", ".scn", ".res", ".tres"],
            encryption_clues=["PCK embedded", ".NET Assembly"],
            mesh_format="Mesh (PCK embedded)",
            skeleton_format="Skeleton3D (PCK)",
            anim_format="Animation (PCK)",
            texture_format="CompressedTexture2D",
            material_format="ShaderMaterial",
            injection_methods=["cecil_il_weave", "pck_patch"],
        ),
        "unity": EngineProfile(
            name="unity",
            display_name="Unity",
            magic_bytes=[b"UnityFS"],
            file_extensions=[".assets", ".bundle", ".prefab"],
            encryption_clues=["Mono/il2cpp", "Assembly-CSharp"],
            mesh_format="Mesh (AssetBundle)",
            skeleton_format="Avatar/Humanoid",
            anim_format="AnimationClip",
            texture_format="Texture2D",
            material_format="Material",
            injection_methods=["harmony_patch", "bepinex", "assetbundle_replace"],
        ),
        "re": EngineProfile(
            name="re",
            display_name="RE Engine",
            magic_bytes=[b"KPKA"],
            file_extensions=[".pak", ".tex", ".mdf2"],
            encryption_clues=["MurmurHash3", "PAK v3"],
            mesh_format="Mesh (.mdf2)",
            skeleton_format="Skeleton (PAK embedded)",
            anim_format="Motion (PAK embedded)",
            texture_format="Texture (.tex)",
            material_format="Material (.mdf2)",
            injection_methods=["lua_script", "pak_patch", "fluffy_mod"],
        ),
        "source2": EngineProfile(
            name="source2",
            display_name="Source 2",
            magic_bytes=[b"VBKV"],
            file_extensions=[".vpk", ".vmdl", ".vmat", ".vtex"],
            encryption_clues=["LZMA compressed"],
            mesh_format="Model (.vmdl)",
            skeleton_format="Skeleton (.vmdl)",
            anim_format="Animation (.vanim)",
            texture_format="Texture (.vtex)",
            material_format="Material (.vmat)",
            injection_methods=["vpk_patch", "addon"],
        ),
    }

    # === 已知游戏注册表 ===
    KNOWN_GAMES: Dict[str, dict] = {
        "black_myth_wukong": {
            "path": "/mnt/hgfs/common/BlackMythWukong",
            "engine": "ue4",
            "display_name": "黑神话：悟空",
            "size_gb": 140,
        },
        "ittakestwo": {
            "path": "/mnt/hgfs/common/ItTakesTwo",
            "engine": "ue4",
            "display_name": "双人成行",
            "size_gb": 46,
        },
        "sifu": {
            "path": "/mnt/hgfs/common/Sifu",
            "engine": "ue4",
            "display_name": "师父",
            "size_gb": 31,
        },
        "dmc5": {
            "path": "/mnt/hgfs/common/Devil May Cry 5",
            "engine": "re",
            "display_name": "鬼泣5",
            "size_gb": 41,
        },
        "valheim": {
            "path": "/mnt/hgfs/common/Valheim",
            "engine": "unity",
            "display_name": "英灵神殿",
            "size_gb": 1.5,
        },
        "enshrouded": {
            "path": "/mnt/hgfs/common/Enshrouded",
            "engine": "ue4",
            "display_name": "禁闭求生：迷雾",
            "size_gb": 42,
        },
        "palworld": {
            "path": "/mnt/hgfs/common/Palworld",
            "engine": "ue4",
            "display_name": "幻兽帕鲁",
            "size_gb": 31,
        },
        "pratfall": {
            "path": "/mnt/hgfs/common/Pratfall",
            "engine": "godot",
            "display_name": "Pratfall",
            "size_gb": 1,
        },
        "grounded": {
            "path": "/mnt/hgfs/common/Grounded",
            "engine": "ue4",
            "display_name": "禁闭求生",
            "size_gb": 12,
        },
        "sons_of_the_forest": {
            "path": "/mnt/hgfs/common/Sons Of The Forest",
            "engine": "unity",
            "display_name": "森林之子",
            "size_gb": 16,
        },
    }

    # === DAG 编排参数 ===
    DAG_TIMEOUT: int = int(os.getenv("CHIMERA_DAG_TIMEOUT", "600"))  # 单Agent超时秒数
    DAG_MAX_RETRIES: int = int(os.getenv("CHIMERA_DAG_MAX_RETRIES", "2"))
    DAG_PARALLEL_MAX: int = int(os.getenv("CHIMERA_DAG_PARALLEL_MAX", "4"))

    # === 资产提取参数 ===
    EXTRACT_TIMEOUT: int = int(os.getenv("CHIMERA_EXTRACT_TIMEOUT", "300"))
    EXTRACT_MAX_FILES: int = int(os.getenv("CHIMERA_EXTRACT_MAX_FILES", "10000"))

    # === AI 模型路由 ===
    VISION_MODEL: str = os.getenv("CHIMERA_VISION_MODEL", "gemini-2.5-flash")
    REASONING_MODEL: str = os.getenv("CHIMERA_REASONING_MODEL", "deepseek-v4-pro")
    CODE_MODEL: str = os.getenv("CHIMERA_CODE_MODEL", "claude-sonnet-4")

    # === 知识库路径 ===
    KB_PATH: str = os.getenv("CHIMERA_KB_PATH", "/data/chimera/knowledge")
    KB_ENGINE_MAPPING: str = os.path.join(KB_PATH, "engine_mapping.json")
    KB_SKELETON_MAPPING: str = os.path.join(KB_PATH, "skeleton_mapping.json")
    KB_MIGRATION_LOG: str = os.path.join(KB_PATH, "migration_log.jsonl")

    # === API 服务 ===
    API_HOST: str = os.getenv("CHIMERA_API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("CHIMERA_API_PORT", "8004"))

    # === 支持的游戏列表（自动从 common 目录扫描） ===
    @classmethod
    def discover_games(cls, base_path: str = "/mnt/hgfs/common") -> Dict[str, dict]:
        """扫描目录自动发现游戏"""
        discovered = {}
        base = Path(base_path)
        if not base.exists():
            return discovered
        for game_dir in sorted(base.iterdir()):
            if game_dir.is_dir() and not game_dir.name.startswith("."):
                size_gb = sum(f.stat().st_size for f in game_dir.rglob("*") if f.is_file()) / (1024**3)
                # 自动检测引擎
                engine = cls._detect_engine(game_dir)
                discovered[game_dir.name.lower().replace(" ", "_")] = {
                    "path": str(game_dir),
                    "engine": engine,
                    "display_name": game_dir.name,
                    "size_gb": round(size_gb, 1),
                }
        return discovered

    @classmethod
    def _detect_engine(cls, game_dir: Path) -> str:
        """自动检测游戏引擎"""
        # 检查 .uasset 文件 → UE4/5
        if list(game_dir.rglob("*.uasset")):
            return "ue4"
        # 检查 .pck 文件 → Godot
        if list(game_dir.rglob("*.pck")):
            return "godot"
        # 检查 Unity 特征
        if list(game_dir.rglob("*Assembly-CSharp*")):
            return "unity"
        # 检查 RE Engine
        if list(game_dir.rglob("*.pak")):
            # 进一步检查 PAK 魔数
            for pak in game_dir.rglob("*.pak"):
                try:
                    with open(pak, "rb") as f:
                        magic = f.read(4)
                        if magic == b"KPKA":
                            return "re"
                except (IOError, PermissionError):
                    pass
            return "ue4"  # 默认假设 UE4 PAK
        return "unknown"
