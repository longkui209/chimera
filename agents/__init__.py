"""
Chimera Agents 模块

8 个专业化 Agent 通过 6 层 DAG 协作：
1. SourceDeconstructor  - 源解构师
2. AssetExtractor       - 角色提取师
3. SkeletonAnalyzer     - 骨架分析师
4. AnimRetargeter       - 动画重定向师
5. FormatTranslator     - 格式转换师
6. TargetInjector       - 目标注入师
7. RuntimeValidator     - 运行时验证官
8. ChimeraOrchestrator  - 编曲家
"""

from .source_deconstructor import SourceDeconstructor
from .asset_extractor import AssetExtractor
from .skeleton_analyzer import SkeletonAnalyzer
from .anim_retargeter import AnimRetargeter
from .format_translator import FormatTranslator
from .target_injector import TargetInjector
from .runtime_validator import RuntimeValidator
from .orchestrator import ChimeraOrchestrator

__all__ = [
    "SourceDeconstructor",
    "AssetExtractor",
    "SkeletonAnalyzer",
    "AnimRetargeter",
    "FormatTranslator",
    "TargetInjector",
    "RuntimeValidator",
    "ChimeraOrchestrator",
]
