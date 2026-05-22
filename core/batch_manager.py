"""
Chimera 批量迁移管理器

支持：
- 从 recipes.json 批量执行迁移
- 进度跟踪
- 并行任务调度
- 结果汇总
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .error_handler import SafeExecutor, ErrorHandler

logger = logging.getLogger("chimera.batch")


@dataclass
class BatchTask:
    """批量任务"""
    recipe_id: str
    recipe_name: str
    source_path: str
    target_path: str
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    status: str = "pending"  # pending | running | completed | failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class BatchReport:
    """批量报告"""
    batch_id: str
    started_at: str
    completed_at: Optional[str] = None
    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    tasks: List[BatchTask] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class BatchManager:
    """
    批量迁移管理器

    从 recipes.json 加载迁移配方，批量执行。
    """

    def __init__(self, recipes_path: str = "/data/chimera/config/recipes.json"):
        self.recipes_path = Path(recipes_path)
        self.tasks: List[BatchTask] = []
        self.report: Optional[BatchReport] = None

    def load_recipes(self) -> List[Dict]:
        """加载迁移配方"""
        if not self.recipes_path.exists():
            logger.warning(f"配方文件不存在: {self.recipes_path}")
            return []

        with open(self.recipes_path) as f:
            data = json.load(f)

        recipes = data.get("recipes", [])
        logger.info(f"📋 加载 {len(recipes)} 个迁移配方")
        return recipes

    def create_tasks(self, recipes: List[Dict] = None) -> List[BatchTask]:
        """创建任务列表"""
        if recipes is None:
            recipes = self.load_recipes()

        self.tasks = []
        for recipe in recipes:
            # 检查路径是否存在
            src_path = recipe["source"]["game_path"]
            tgt_path = recipe["target"]["game_path"]

            task = BatchTask(
                recipe_id=recipe["id"],
                recipe_name=recipe["name"],
                source_path=src_path,
                target_path=tgt_path,
                source_id=recipe["source"].get("game_id"),
                target_id=recipe["target"].get("game_id"),
            )

            if Path(src_path).exists() and Path(tgt_path).exists():
                task.status = "pending"
            else:
                task.status = "failed"
                task.error = f"路径不存在: {src_path if not Path(src_path).exists() else tgt_path}"

            self.tasks.append(task)

        logger.info(f"📋 创建 {len(self.tasks)} 个任务 "
                     f"({sum(1 for t in self.tasks if t.status == 'pending')} 就绪)")
        return self.tasks

    async def execute_batch(
        self,
        max_parallel: int = 2,
        recipes: List[Dict] = None,
    ) -> BatchReport:
        """
        批量执行迁移

        Args:
            max_parallel: 最大并行任务数
            recipes: 可选，指定配方列表
        """
        if recipes is None and not self.tasks:
            self.create_tasks()

        pending = [t for t in self.tasks if t.status == "pending"]
        if not pending:
            logger.warning("没有可执行的任务")
            return self._empty_report()

        self.report = BatchReport(
            batch_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            started_at=datetime.now().isoformat(),
            total_tasks=len(pending),
        )

        logger.info(f"🚀 批量迁移启动: {len(pending)} 个任务, 并行度 {max_parallel}")

        from ..agents.orchestrator import ChimeraOrchestrator

        # 分批执行
        for i in range(0, len(pending), max_parallel):
            batch = pending[i:i + max_parallel]
            logger.info(f"  批次 {i // max_parallel + 1}: {[t.recipe_name for t in batch]}")

            for task in batch:
                task.status = "running"
                task.started_at = datetime.now().isoformat()

                try:
                    orch = ChimeraOrchestrator()
                    result = await orch.migrate(
                        source_game_path=task.source_path,
                        target_game_path=task.target_path,
                        source_game_id=task.source_id,
                        target_game_id=task.target_id,
                    )

                    task.result = result
                    task.status = "completed" if result.get("success") else "failed"
                    task.completed_at = datetime.now().isoformat()

                    if task.status == "completed":
                        self.report.completed += 1
                        logger.info(f"  ✅ {task.recipe_name}")
                    else:
                        self.report.failed += 1
                        task.error = "迁移流水线返回失败"
                        logger.warning(f"  ❌ {task.recipe_name}")

                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                    task.completed_at = datetime.now().isoformat()
                    self.report.failed += 1
                    logger.error(f"  ❌ {task.recipe_name}: {e}")

        self.report.completed_at = datetime.now().isoformat()
        self._build_summary()

        logger.info(f"✅ 批量迁移完成: {self.report.completed}/{self.report.total_tasks} 成功")
        return self.report

    def execute_sync(
        self,
        recipes: List[Dict] = None,
    ) -> BatchReport:
        """同步批量执行（包装异步）"""
        return asyncio.run(self.execute_batch(recipes=recipes))

    def _build_summary(self):
        """构建汇总"""
        if not self.report:
            return
        self.report.summary = {
            "total": self.report.total_tasks,
            "completed": self.report.completed,
            "failed": self.report.failed,
            "success_rate": (
                self.report.completed / self.report.total_tasks * 100
                if self.report.total_tasks > 0 else 0
            ),
            "by_engine_pair": {},
            "total_tokens": sum(
                t.result.get("total_tokens", 0)
                for t in self.tasks if t.result
            ),
        }

        # 按引擎对统计
        for task in self.tasks:
            if task.result:
                pair = f"{task.result.get('source_game', '?')}→{task.result.get('target_game', '?')}"
                if pair not in self.report.summary["by_engine_pair"]:
                    self.report.summary["by_engine_pair"][pair] = {"success": 0, "failed": 0}
                key = "success" if task.status == "completed" else "failed"
                self.report.summary["by_engine_pair"][pair][key] += 1

    def _empty_report(self) -> BatchReport:
        return BatchReport(
            batch_id="empty",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            total_tasks=0,
        )

    def get_status(self) -> Dict[str, Any]:
        """获取批量状态"""
        if not self.tasks:
            return {"status": "no_tasks"}

        return {
            "total": len(self.tasks),
            "pending": sum(1 for t in self.tasks if t.status == "pending"),
            "running": sum(1 for t in self.tasks if t.status == "running"),
            "completed": sum(1 for t in self.tasks if t.status == "completed"),
            "failed": sum(1 for t in self.tasks if t.status == "failed"),
            "tasks": [
                {
                    "id": t.recipe_id,
                    "name": t.recipe_name,
                    "status": t.status,
                    "error": t.error,
                }
                for t in self.tasks
            ],
        }
