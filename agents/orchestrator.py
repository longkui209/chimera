"""
Agent 8: 编曲家 Orchestrator

Chimera 流水线总指挥。
负责：
- DAG 编排与调度
- 上下文路由
- 错误恢复
- 结果汇总
"""

import sys
from pathlib import Path as _Path
_sys_path = str(_Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.dag_engine import DAGEngine
from core.config import Config
from core.knowledge_base import KnowledgeBase

logger = logging.getLogger("chimera.orchestrator")


class ChimeraOrchestrator:
    """
    Chimera 编曲家

    统筹所有 Agent，管理完整的跨游戏角色迁移流水线。
    """

    def __init__(self):
        self.kb = KnowledgeBase()
        self.dag = None
        self._setup_dag()

    def _setup_dag(self):
        """构建 DAG 流水线"""
        import sys, os
        _agents_dir = os.path.dirname(os.path.abspath(__file__))
        if _agents_dir not in sys.path:
            sys.path.insert(0, _agents_dir)

        from source_deconstructor import SourceDeconstructor
        from asset_extractor import AssetExtractor
        from skeleton_analyzer import SkeletonAnalyzer
        from anim_retargeter import AnimRetargeter
        from format_translator import FormatTranslator
        from target_injector import TargetInjector
        from runtime_validator import RuntimeValidator

        # 初始化 Agent
        source_dec = SourceDeconstructor()
        asset_ext = AssetExtractor()
        skeleton_analyzer = SkeletonAnalyzer()
        anim_retargeter = AnimRetargeter()
        format_translator = FormatTranslator()
        target_injector = TargetInjector()
        runtime_validator = RuntimeValidator()

        # 构建 DAG
        self.dag = (
            DAGEngine()
            .add_node("source_deconstructor", source_dec.analyze)
            .add_node(
                "asset_extractor",
                asset_ext.extract,
                depends_on=["source_deconstructor"],
            )
            .add_node(
                "skeleton_analyzer",
                skeleton_analyzer.analyze,
                depends_on=["asset_extractor"],
            )
            .add_node(
                "anim_retargeter",
                anim_retargeter.retarget,
                depends_on=["skeleton_analyzer"],
            )
            .add_node(
                "format_translator",
                format_translator.translate,
                depends_on=["skeleton_analyzer"],
            )
            .add_node(
                "target_injector",
                target_injector.inject,
                depends_on=["format_translator", "anim_retargeter"],
            )
            .add_node(
                "runtime_validator",
                runtime_validator.validate,
                depends_on=["target_injector"],
            )
        )

    async def migrate(
        self,
        source_game_path: str,
        target_game_path: str,
        source_game_id: Optional[str] = None,
        target_game_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行完整跨游戏角色迁移

        Args:
            source_game_path: 源游戏路径
            target_game_path: 目标游戏路径
            source_game_id: 源游戏注册 ID（可选）
            target_game_id: 目标游戏注册 ID（可选）

        Returns:
            完整迁移报告
        """
        logger.info("=" * 60)
        logger.info(f"🦁🐐🐍 Chimera 跨游戏迁移启动")
        logger.info(f"  源游戏: {Path(source_game_path).name}")
        logger.info(f"  目标游戏: {Path(target_game_path).name}")
        logger.info("=" * 60)

        # 初始上下文
        initial_context = {
            "source_game_path": source_game_path,
            "target_game_path": target_game_path,
            "source_game_id": source_game_id,
            "target_game_id": target_game_id,
        }

        # 运行 DAG 流水线
        dag_result = await self.dag.run(initial_context)

        # 记录迁移日志
        self.kb.log_migration(
            source_game=Path(source_game_path).name,
            target_game=Path(target_game_path).name,
            character=dag_result.get("results", {}).get("asset_extractor", {}).get(
                "extracted", [{"name": "unknown"}]
            )[0]["name"] if dag_result.get("results", {}).get("asset_extractor", {}).get(
                "extracted"
            ) else "unknown",
            success=dag_result["success"],
            details={
                "elapsed": dag_result["elapsed"],
                "total_tokens": dag_result["total_tokens"],
            },
        )

        # 汇总报告
        report = {
            "migration_id": str(hash(f"{source_game_path}{target_game_path}"))[:8],
            "source_game": Path(source_game_path).name,
            "target_game": Path(target_game_path).name,
            "success": dag_result["success"],
            "elapsed_seconds": round(dag_result["elapsed"], 1),
            "total_tokens": dag_result["total_tokens"],
            "agent_results": dag_result["results"],
            "metrics": dag_result["metrics"],
            "knowledge_base_stats": self.kb.stats(),
        }

        return report

    def inspect_pipeline(self) -> Dict[str, Any]:
        """查看流水线结构"""
        return self.dag.inspect()

    def list_supported_games(self) -> List[Dict[str, Any]]:
        """列出已知支持的游戏"""
        known = Config.KNOWN_GAMES
        discovered = Config.discover_games()

        games = []
        for game_id, info in known.items():
            games.append({
                "id": game_id,
                "name": info["display_name"],
                "engine": info["engine"],
                "size_gb": info["size_gb"],
                "source": "known",
            })

        for game_id, info in discovered.items():
            if game_id not in known:
                games.append({
                    "id": game_id,
                    "name": info["display_name"],
                    "engine": info["engine"],
                    "size_gb": info["size_gb"],
                    "source": "discovered",
                })

        return games

    def list_conversion_paths(self) -> List[Dict[str, Any]]:
        """列出支持的所有格式转换路径"""
        from .format_translator import FormatTranslator
        ft = FormatTranslator()
        return ft.get_conversion_paths()
