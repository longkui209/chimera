"""
Chimera DAG 编排引擎

Kahn 拓扑排序 + 并行调度 + 超时重试 + ContextBus 通信。
支持 6 层 DAG，最高 4 Agent 并行。
"""

import time
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from collections import defaultdict

from .config import Config

logger = logging.getLogger("chimera.dag")


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """DAG 节点 —— 一个 Agent 的一次执行"""
    name: str
    agent_fn: Callable
    depends_on: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    retries: int = 0
    token_count: int = 0

    @property
    def elapsed(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        if self.start_time:
            return time.time() - self.start_time
        return 0.0


@dataclass
class ContextBus:
    """上下文总线 —— Agent 间数据传递"""
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "total_tokens": 0,
        "total_time": 0.0,
        "node_count": 0,
        "errors": 0,
    })

    def put(self, key: str, value: Any) -> None:
        """写入上下文"""
        self.data[key] = value
        self.history.append({"action": "put", "key": key, "timestamp": time.time()})

    def get(self, key: str, default: Any = None) -> Any:
        """读取上下文"""
        return self.data.get(key, default)

    def snapshot(self) -> Dict[str, Any]:
        """上下文快照"""
        return {
            "data_keys": list(self.data.keys()),
            "metrics": dict(self.metrics),
            "history_count": len(self.history),
        }


class DAGEngine:
    """
    DAG 编排引擎

    特性：
    - Kahn 拓扑排序，保证依赖顺序
    - 同一层级节点并行执行
    - 超时重试 + 指数退避
    - 失败节点不影响独立兄弟节点
    - 全链路 ContextBus 通信
    """

    def __init__(self, timeout: int = None, max_retries: int = None, max_parallel: int = None):
        self.timeout = timeout or Config.DAG_TIMEOUT
        self.max_retries = max_retries or Config.DAG_MAX_RETRIES
        self.max_parallel = max_parallel or Config.DAG_PARALLEL_MAX
        self.bus = ContextBus()
        self.nodes: Dict[str, DAGNode] = {}
        self._layers: List[List[str]] = []

    def add_node(self, name: str, agent_fn: Callable, depends_on: List[str] = None) -> "DAGEngine":
        """注册一个 Agent 节点"""
        self.nodes[name] = DAGNode(
            name=name,
            agent_fn=agent_fn,
            depends_on=depends_on or [],
        )
        return self

    def _toposort(self) -> bool:
        """
        Kahn 拓扑排序，将节点分层。

        Returns:
            bool: 成功返回 True，有环返回 False
        """
        # 构建入度表
        in_degree: Dict[str, int] = defaultdict(int)
        graph: Dict[str, List[str]] = defaultdict(list)

        for name, node in self.nodes.items():
            if name not in in_degree:
                in_degree[name] = 0
            for dep in node.depends_on:
                graph[dep].append(name)
                in_degree[name] += 1

        # Kahn 算法
        self._layers = []
        frontier = [name for name, deg in in_degree.items() if deg == 0]

        while frontier:
            self._layers.append(sorted(frontier))
            next_frontier = []
            for node_name in frontier:
                for dependent in graph.get(node_name, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_frontier.append(dependent)
            frontier = next_frontier

        # 检查是否有环
        total_nodes = sum(len(layer) for layer in self._layers)
        if total_nodes != len(self.nodes):
            missing = set(self.nodes.keys()) - set(n for layer in self._layers for n in layer)
            logger.error(f"DAG 存在循环依赖！未排序节点: {missing}")
            return False

        logger.info(f"DAG 拓扑排序完成: {len(self._layers)} 层, {total_nodes} 节点")
        for i, layer in enumerate(self._layers):
            logger.info(f"  第{i+1}层: {layer}")

        return True

    async def _execute_node(self, node: DAGNode, context: Dict[str, Any]) -> Any:
        """
        执行单个节点（带超时和重试）

        Args:
            node: DAG 节点
            context: 上游节点的输出上下文

        Returns:
            节点执行结果
        """
        node.start_time = time.time()
        node.status = NodeStatus.RUNNING

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(node.agent_fn):
                    result = await asyncio.wait_for(
                        node.agent_fn(context),
                        timeout=self.timeout,
                    )
                else:
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, node.agent_fn, context),
                        timeout=self.timeout,
                    )

                node.end_time = time.time()
                node.status = NodeStatus.COMPLETED
                node.result = result

                # 估算 token（基于输出长度）
                if isinstance(result, dict):
                    node.token_count = len(str(result)) // 4
                elif isinstance(result, str):
                    node.token_count = len(result) // 4

                self.bus.metrics["total_tokens"] += node.token_count
                logger.info(
                    f"[{node.name}] ✅ 完成 "
                    f"({node.elapsed:.1f}s, ~{node.token_count:,} tokens)"
                )
                return result

            except asyncio.TimeoutError:
                node.retries = attempt + 1
                if attempt < self.max_retries:
                    wait = 2 ** attempt  # 指数退避
                    logger.warning(
                        f"[{node.name}] ⏱️ 超时 ({self.timeout}s)，"
                        f"第{attempt+1}次重试，等待{wait}s..."
                    )
                    node.status = NodeStatus.RETRYING
                    await asyncio.sleep(wait)
                else:
                    node.end_time = time.time()
                    node.status = NodeStatus.FAILED
                    node.error = f"超时 ({self.timeout}s)，已重试{self.max_retries}次"
                    self.bus.metrics["errors"] += 1
                    logger.error(f"[{node.name}] ❌ {node.error}")
                    return None

            except Exception as e:
                node.retries = attempt + 1
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"[{node.name}] ⚠️ 错误: {e}，第{attempt+1}次重试，等待{wait}s..."
                    )
                    node.status = NodeStatus.RETRYING
                    await asyncio.sleep(wait)
                else:
                    node.end_time = time.time()
                    node.status = NodeStatus.FAILED
                    node.error = str(e)
                    self.bus.metrics["errors"] += 1
                    logger.error(f"[{node.name}] ❌ 失败: {e}")
                    return None

    async def run(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        启动 DAG 流水线

        Args:
            initial_context: 初始上下文（源游戏路径、目标游戏路径等）

        Returns:
            包含所有节点结果和执行统计的字典
        """
        logger.info("========== Chimera DAG Pipeline 启动 ==========")
        start_time = time.time()

        if initial_context:
            for k, v in initial_context.items():
                self.bus.put(k, v)

        # 1. 拓扑排序
        if not self._toposort():
            return {"success": False, "error": "DAG 存在循环依赖"}

        # 2. 逐层执行
        all_results = {}
        for layer_idx, layer in enumerate(self._layers):
            logger.info(f"--- 第 {layer_idx+1}/{len(self._layers)} 层: {layer} ---")

            # 构建上下文（注入上游结果 + ContextBus）
            context = {
                "bus": self.bus,
                "layer": layer_idx,
                "upstream_results": {
                    name: self.nodes[name].result
                    for name in self.nodes
                    if self.nodes[name].status == NodeStatus.COMPLETED
                },
            }

            # 并行执行同层节点
            if len(layer) == 1:
                result = await self._execute_node(self.nodes[layer[0]], context)
                all_results[layer[0]] = result
            else:
                tasks = [
                    self._execute_node(self.nodes[name], context)
                    for name in layer
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for name, result in zip(layer, results):
                    if isinstance(result, Exception):
                        logger.error(f"[{name}] 未捕获异常: {result}")
                    all_results[name] = result

            # 检查是否有致命失败（该节点是所有下游的依赖）
            for name in layer:
                node = self.nodes[name]
                if node.status == NodeStatus.FAILED:
                    downstream = [
                        dn for dn, dn_node in self.nodes.items()
                        if name in dn_node.depends_on
                    ]
                    if downstream:
                        logger.warning(f"[{name}] 失败但继续，下游 {downstream} 可能受影响")

        # 3. 汇总
        elapsed = time.time() - start_time
        self.bus.metrics["total_time"] = elapsed
        self.bus.metrics["node_count"] = len(self.nodes)

        total_tokens = sum(n.token_count for n in self.nodes.values())
        self.bus.metrics["total_tokens"] = total_tokens

        completed = sum(1 for n in self.nodes.values() if n.status == NodeStatus.COMPLETED)
        failed = sum(1 for n in self.nodes.values() if n.status == NodeStatus.FAILED)

        logger.info(f"========== DAG Pipeline 完成 ==========")
        logger.info(f"  总耗时: {elapsed:.1f}s")
        logger.info(f"  Token: ~{total_tokens:,}")
        logger.info(f"  完成: {completed}/{len(self.nodes)}")
        logger.info(f"  失败: {failed}/{len(self.nodes)}")

        return {
            "success": failed == 0,
            "elapsed": elapsed,
            "total_tokens": total_tokens,
            "completed": completed,
            "failed": failed,
            "results": all_results,
            "metrics": dict(self.bus.metrics),
            "bus_snapshot": self.bus.snapshot(),
        }

    def inspect(self) -> Dict[str, Any]:
        """检查 DAG 结构"""
        layers = []
        if not self._layers:
            self._toposort()
        for i, layer in enumerate(self._layers):
            layers.append({
                "level": i + 1,
                "nodes": layer,
                "parallel": len(layer),
            })
        return {
            "total_nodes": len(self.nodes),
            "total_layers": len(layers),
            "layers": layers,
            "dependencies": {
                name: node.depends_on
                for name, node in self.nodes.items()
            },
        }
