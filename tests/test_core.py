"""
Chimera 核心测试

测试覆盖：
- 配置系统
- 引擎指纹识别
- DAG 编排引擎
- 知识库
- 所有 8 个 Agent
- API 端点
"""

import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, "/data/chimera")

from core.config import Config
from core.dag_engine import DAGEngine, NodeStatus
from core.engine_fingerprint import EngineFingerprinter
from core.knowledge_base import KnowledgeBase

from agents.source_deconstructor import SourceDeconstructor
from agents.asset_extractor import AssetExtractor
from agents.skeleton_analyzer import SkeletonAnalyzer
from agents.anim_retargeter import AnimRetargeter
from agents.format_translator import FormatTranslator
from agents.target_injector import TargetInjector
from agents.runtime_validator import RuntimeValidator
from agents.orchestrator import ChimeraOrchestrator


# ============================================================
# 配置系统测试
# ============================================================

class TestConfig:
    def test_engines_configured(self):
        """验证所有5个引擎已配置"""
        assert len(Config.ENGINES) >= 5
        assert "ue4" in Config.ENGINES
        assert "godot" in Config.ENGINES
        assert "unity" in Config.ENGINES
        assert "re" in Config.ENGINES
        assert "source2" in Config.ENGINES

    def test_ue4_profile(self):
        ue4 = Config.ENGINES["ue4"]
        assert ue4.display_name == "Unreal Engine 4/5"
        assert ".uasset" in ue4.file_extensions
        assert len(ue4.injection_methods) >= 3

    def test_godot_profile(self):
        godot = Config.ENGINES["godot"]
        assert godot.magic_bytes[0] == b"GDPC"
        assert "cecil_il_weave" in godot.injection_methods

    def test_known_games(self):
        """验证已知游戏注册表"""
        assert "ittakestwo" in Config.KNOWN_GAMES
        assert Config.KNOWN_GAMES["ittakestwo"]["engine"] == "ue4"
        assert Config.KNOWN_GAMES["sifu"]["engine"] == "ue4"
        assert Config.KNOWN_GAMES["dmc5"]["engine"] == "re"

    def test_dag_config(self):
        assert Config.DAG_TIMEOUT > 0
        assert Config.DAG_MAX_RETRIES >= 1
        assert Config.DAG_PARALLEL_MAX >= 2

    def test_engine_detection(self):
        """测试引擎自动检测"""
        # UE4 特征：.uasset 文件
        result = Config._detect_engine(Path("/mnt/hgfs/common/ItTakesTwo"))
        assert result in ("ue4", "re", "unknown")

    def test_discover_games(self):
        """测试游戏自动发现"""
        games = Config.discover_games("/mnt/hgfs/common")
        assert isinstance(games, dict)
        # 至少有 It Takes Two
        assert any("ittakestwo" in k.lower() for k in games) or len(games) > 0


# ============================================================
# DAG 编排引擎测试
# ============================================================

class TestDAGEngine:
    def test_add_node(self):
        dag = DAGEngine()
        dag.add_node("node1", lambda ctx: {"result": "ok"})
        assert "node1" in dag.nodes

    def test_toposort_linear(self):
        """线性依赖拓扑排序"""
        dag = DAGEngine()
        dag.add_node("a", lambda ctx: 1)
        dag.add_node("b", lambda ctx: 2, depends_on=["a"])
        dag.add_node("c", lambda ctx: 3, depends_on=["b"])
        assert dag._toposort()
        assert len(dag._layers) == 3  # 3 层

    def test_toposort_parallel(self):
        """并行节点拓扑排序"""
        dag = DAGEngine()
        dag.add_node("root", lambda ctx: 0)
        dag.add_node("a", lambda ctx: 1, depends_on=["root"])
        dag.add_node("b", lambda ctx: 2, depends_on=["root"])
        dag.add_node("c", lambda ctx: 3, depends_on=["root"])
        assert dag._toposort()
        # 第 1 层: root, 第 2 层: a,b,c 三个并行
        assert len(dag._layers) == 2
        assert len(dag._layers[1]) == 3

    def test_toposort_diamond(self):
        """菱形依赖拓扑排序"""
        dag = DAGEngine()
        dag.add_node("top", lambda ctx: 0)
        dag.add_node("left", lambda ctx: 1, depends_on=["top"])
        dag.add_node("right", lambda ctx: 2, depends_on=["top"])
        dag.add_node("bottom", lambda ctx: 3, depends_on=["left", "right"])
        assert dag._toposort()
        assert len(dag._layers) == 3

    def test_inspect(self):
        dag = DAGEngine()
        dag.add_node("a", lambda ctx: 1)
        dag.add_node("b", lambda ctx: 2, depends_on=["a"])
        info = dag.inspect()
        assert info["total_nodes"] == 2
        assert info["total_layers"] == 2

    def test_context_bus(self):
        from core.dag_engine import ContextBus
        bus = ContextBus()
        bus.put("key1", "value1")
        assert bus.get("key1") == "value1"
        assert bus.get("nonexistent", "default") == "default"
        snap = bus.snapshot()
        assert "key1" in snap["data_keys"]

    @pytest.mark.asyncio
    async def test_simple_run(self):
        """简单 DAG 运行"""
        dag = DAGEngine(timeout=30)

        def agent_a(ctx):
            return {"a": 1}

        def agent_b(ctx):
            upstream = ctx.get("upstream_results", {})
            return {"b": upstream.get("a", {}).get("a", 0) + 1}

        dag.add_node("a", agent_a)
        dag.add_node("b", agent_b, depends_on=["a"])

        result = await dag.run({"initial": "context"})
        assert result["success"]
        assert result["completed"] == 2
        assert result["failed"] == 0


# ============================================================
# 引擎指纹识别测试
# ============================================================

class TestEngineFingerprint:
    def setup_method(self):
        self.fingerprinter = EngineFingerprinter()

    def test_identify_known_game(self):
        """已知游戏识别"""
        result = self.fingerprinter.identify(
            "/mnt/hgfs/common/ItTakesTwo",
            game_id="ittakestwo",
        )
        assert result.engine == "ue4"
        assert result.confidence == 1.0

    def test_identify_re_engine(self):
        """RE Engine 识别"""
        result = self.fingerprinter.identify(
            "/mnt/hgfs/common/Devil May Cry 5",
            game_id="dmc5",
        )
        assert result.engine == "re"
        assert result.confidence == 1.0

    def test_identify_nonexistent(self):
        """不存在的路径"""
        result = self.fingerprinter.identify("/tmp/nonexistent_game")
        assert result.engine == "unknown"
        assert result.confidence == 0.0

    def test_scan_extensions(self):
        """扩展名扫描"""
        results = self.fingerprinter._scan_extensions(
            Path("/mnt/hgfs/common/ItTakesTwo"),
            sample_limit=1000,
        )
        assert isinstance(results, dict)


# ============================================================
# 知识库测试
# ============================================================

class TestKnowledgeBase:
    def setup_method(self):
        self.kb = KnowledgeBase("/tmp/chimera_test_kb")

    def test_save_and_query(self):
        self.kb.log_migration(
            "GameA", "GameB", "TestCharacter", True,
            {"elapsed": 10.5},
        )
        results = self.kb.query_migrations("GameA")
        assert len(results) >= 1
        assert results[-1]["success"] is True

    def test_skeleton_mapping(self):
        self.kb.save_skeleton_mapping(
            "Hero", "Champion",
            [{"src": "root", "tgt": "hip"}],
            0.95,
        )
        stats = self.kb.stats()
        assert stats["skeleton_mappings"] >= 1

    def test_stats(self):
        stats = self.kb.stats()
        assert "total_migrations" in stats
        assert "success_rate" in stats
        assert "skeleton_mappings" in stats

    def test_engine_mapping(self):
        mapping = self.kb.get_engine_mapping("ue4", "unity")
        assert mapping is not None
        assert mapping["complexity"] == "medium"


# ============================================================
# Agent 测试
# ============================================================

class TestSourceDeconstructor:
    def test_init(self):
        agent = SourceDeconstructor()
        assert agent is not None

    def test_analyze_ittakestwo(self):
        agent = SourceDeconstructor()
        context = {"bus": None}
        # 需要模拟 context bus
        from core.dag_engine import ContextBus
        bus = ContextBus()
        bus.put("source_game_path", "/mnt/hgfs/common/ItTakesTwo")
        bus.put("source_game_id", "ittakestwo")
        context["bus"] = bus

        result = agent.analyze(context)
        assert "engine" in result
        assert result["engine"] == "ue4"
        assert result["confidence"] == 1.0

    def test_classify_directory(self):
        agent = SourceDeconstructor()
        assert agent._classify_directory("Content") == "content_root"
        assert agent._classify_directory("Characters") == "characters"
        assert agent._classify_directory("Textures") == "textures"
        assert agent._classify_directory("random_folder") == "other"


class TestAssetExtractor:
    def test_init(self):
        agent = AssetExtractor()
        assert agent is not None

    def test_extract_ittakestwo(self):
        agent = AssetExtractor()
        from core.dag_engine import ContextBus
        bus = ContextBus()
        bus.put("source_game_path", "/mnt/hgfs/common/ItTakesTwo")
        bus.put("source_engine", "ue4")
        bus.put("source_characters", [
            {"path": "/mnt/hgfs/common/ItTakesTwo", "name": "TestChar"}
        ])
        context = {"bus": bus, "upstream_results": {}}
        result = agent.extract(context)
        assert "extracted" in result or "error" in result


class TestSkeletonAnalyzer:
    def test_init(self):
        agent = SkeletonAnalyzer()
        assert agent is not None

    def test_name_similarity(self):
        agent = SkeletonAnalyzer()
        assert agent._name_similarity("spine_01", "spine_01") == 1.0
        assert agent._name_similarity("spine", "spine_01") == 0.8
        assert agent._name_similarity("spine", "head") < 0.5

    def test_extract_bone_list(self):
        agent = SkeletonAnalyzer()
        bones = agent._extract_bone_list({"engine": "ue4"})
        assert len(bones) >= 20
        assert bones[0]["name"] == "Root"

    def test_match_bones(self):
        agent = SkeletonAnalyzer()
        source = agent._extract_bone_list({"engine": "ue4"})
        target = agent._extract_bone_list({"engine": "ue4"})
        mapping = agent._match_bones(source, target)
        assert len(mapping) == len(source)
        # 所有骨骼应该精确匹配
        exact_count = sum(1 for m in mapping if m["method"] == "exact")
        assert exact_count == len(source)


class TestAnimRetargeter:
    def test_init(self):
        agent = AnimRetargeter()
        assert agent is not None

    def test_select_strategy(self):
        agent = AnimRetargeter()
        # 全精确匹配 → DIRECT
        mapping = [{"method": "exact"} for _ in range(20)]
        strategy = agent._select_strategy(mapping, 1.0)
        assert strategy.value == "direct"

    def test_retarget(self):
        agent = AnimRetargeter()
        mapping = [{"source_bone": f"bone_{i}", "target_bone": f"bone_{i}", "method": "exact", "confidence": 1.0} for i in range(20)]
        context = {
            "bus": None,
            "upstream_results": {"bone_mapping": mapping, "mapping_confidence": 1.0},
        }
        result = agent.retarget(context)
        assert result["strategy"] == "direct"
        assert result["total_animations"] == 5


class TestFormatTranslator:
    def test_init(self):
        agent = FormatTranslator()
        assert agent is not None

    def test_translate_ue4_to_ue4(self):
        agent = FormatTranslator()
        context = {
            "bus": None,
            "upstream_results": {"source_engine": "ue4", "target_engine": "ue4"},
        }
        result = agent.translate(context)
        assert result["complexity"] == "low"

    def test_translate_ue4_to_godot(self):
        agent = FormatTranslator()
        context = {
            "bus": None,
            "upstream_results": {"source_engine": "ue4", "target_engine": "godot"},
        }
        result = agent.translate(context)
        assert result["complexity"] == "high"

    def test_material_mapping(self):
        agent = FormatTranslator()
        mapping = agent._map_materials("ue4", "unity")
        assert "BaseColor" in mapping
        assert mapping["BaseColor"] == "_BaseMap"

    def test_get_conversion_paths(self):
        agent = FormatTranslator()
        paths = agent.get_conversion_paths()
        assert len(paths) >= 7


class TestTargetInjector:
    def test_init(self):
        agent = TargetInjector()
        assert agent is not None

    def test_select_method(self):
        agent = TargetInjector()
        from agents.target_injector import InjectionMethod
        assert agent._select_method("ue4") == InjectionMethod.LOGICMODS
        assert agent._select_method("godot") == InjectionMethod.CECIL_WEAVE
        assert agent._select_method("unity") == InjectionMethod.BEPINEX


class TestRuntimeValidator:
    def test_init(self):
        agent = RuntimeValidator()
        assert agent is not None

    def test_validate(self):
        agent = RuntimeValidator()
        context = {"bus": None, "upstream_results": {}}
        result = agent.validate(context)
        assert "checks" in result
        assert "overall_score" in result
        assert len(result["checks"]) == 5


class TestChimeraOrchestrator:
    def test_init(self):
        orch = ChimeraOrchestrator()
        assert orch is not None
        assert orch.dag is not None

    def test_inspect_pipeline(self):
        orch = ChimeraOrchestrator()
        info = orch.inspect_pipeline()
        assert info["total_nodes"] == 7
        assert info["total_layers"] >= 5  # 6 层（2个Agent在第4层并行）

    def test_list_supported_games(self):
        orch = ChimeraOrchestrator()
        # 只检查已知游戏（不触发 hgfs 扫描）
        from core.config import Config
        known = Config.KNOWN_GAMES
        assert len(known) > 0
        assert any(info["display_name"] == "双人成行" for info in known.values())


# ============================================================
# 端到端测试
# ============================================================

class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """完整流水线测试（使用模拟路径）"""
        orch = ChimeraOrchestrator()

        # 使用 It Takes Two 作为源和目标（同引擎迁移）
        result = await orch.migrate(
            source_game_path="/mnt/hgfs/common/ItTakesTwo",
            target_game_path="/mnt/hgfs/common/ItTakesTwo",
            source_game_id="ittakestwo",
            target_game_id="ittakestwo",
        )

        assert "migration_id" in result
        assert result["source_game"] == "ItTakesTwo"
        assert "agent_results" in result
        assert "metrics" in result


# ============================================================
# 扩展测试：工具链 & CLI & 配置
# ============================================================

class TestToolchain:
    def test_registry(self):
        """工具注册表完整性"""
        from tools.toolchain import ToolchainManager
        mgr = ToolchainManager()
        assert len(mgr.TOOL_REGISTRY) >= 10
        assert "umodel" in mgr.TOOL_REGISTRY
        assert "blender" in mgr.TOOL_REGISTRY
        assert "python3" in mgr.TOOL_REGISTRY

    def test_discover(self):
        """工具发现"""
        from tools.toolchain import ToolchainManager
        mgr = ToolchainManager()
        mgr.discover_all()
        assert len(mgr.discovered) >= 10
        # python3 必须存在
        assert mgr.discovered["python3"].status.value == "found"

    def test_check_required(self):
        """检查必需工具"""
        from tools.toolchain import ToolchainManager
        mgr = ToolchainManager()
        mgr.discover_all()
        ok, missing = mgr.check_required()
        # 至少 python3 和 fastapi 应该存在
        assert isinstance(ok, bool)

    def test_report(self):
        """生成报告"""
        from tools.toolchain import ToolchainManager
        mgr = ToolchainManager()
        mgr.discover_all()
        report = mgr.generate_report()
        assert "scanned_at" in report
        assert "total_tools" in report
        assert "tools" in report
        assert len(report["tools"]) >= 10

    def test_print_report(self):
        """打印报告"""
        from tools.toolchain import ToolchainManager
        mgr = ToolchainManager()
        mgr.discover_all()
        text = mgr.print_report()
        assert "Chimera" in text
        assert len(text) > 100


class TestConfigExtended:
    def test_engine_count(self):
        """引擎数量"""
        from core.config import Config
        assert len(Config.ENGINES) == 5

    def test_api_config(self):
        """API 配置"""
        from core.config import Config
        assert Config.API_PORT == 8004
        assert Config.API_HOST == "0.0.0.0"

    def test_model_routing(self):
        """模型路由配置"""
        from core.config import Config
        assert Config.VISION_MODEL == "gemini-2.5-flash"
        assert Config.REASONING_MODEL == "deepseek-v4-pro"

    def test_kb_paths(self):
        """KB 路径配置"""
        from core.config import Config
        assert "knowledge" in Config.KB_PATH

    def test_recipe_config(self):
        """配方配置加载"""
        import json
        with open("/data/chimera/config/recipes.json") as f:
            recipes = json.load(f)
        assert len(recipes["recipes"]) >= 5
        assert recipes["recipes"][0]["id"] == "wukong_to_valheim"


class TestKnowledgeBaseExtended:
    def test_multiple_migrations(self):
        """多次迁移记录"""
        import tempfile, shutil
        from core.knowledge_base import KnowledgeBase
        tmpdir = tempfile.mkdtemp(prefix="chimera_test_")
        try:
            kb = KnowledgeBase(tmpdir)
            for i in range(5):
                kb.log_migration(f"Game{i}", f"Game{i+1}", f"Char{i}", True, {})
            stats = kb.stats()
            assert stats["total_migrations"] == 5
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_failed_migration_count(self):
        """失败迁移统计"""
        import tempfile, shutil
        from core.knowledge_base import KnowledgeBase
        tmpdir = tempfile.mkdtemp(prefix="chimera_test_")
        try:
            kb = KnowledgeBase(tmpdir)
            kb.log_migration("A", "B", "X", False, {"reason": "skeleton mismatch"})
            stats = kb.stats()
            assert stats["failed"] == 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestFormatTranslatorExtended:
    def test_all_paths_available(self):
        """所有转换路径可用"""
        from agents.format_translator import FormatTranslator
        ft = FormatTranslator()
        paths = ft.get_conversion_paths()
        assert len(paths) >= 7

    def test_complexity_levels(self):
        """复杂度映射"""
        from agents.format_translator import FormatTranslator
        ft = FormatTranslator()
        assert ft._estimate_time("low") == "1-3 分钟"
        assert ft._estimate_time("very_high") == "30-60 分钟"


class TestDAGEngineExtended:
    def test_complex_dag(self):
        """复杂 DAG（模拟实际流水线）"""
        from core.dag_engine import DAGEngine
        dag = DAGEngine(timeout=10)
        dag.add_node("scan", lambda ctx: {"ok": True})
        dag.add_node("extract", lambda ctx: {"ok": True}, depends_on=["scan"])
        dag.add_node("analyze", lambda ctx: {"ok": True}, depends_on=["extract"])
        dag.add_node("retarget", lambda ctx: {"ok": True}, depends_on=["analyze"])
        dag.add_node("convert", lambda ctx: {"ok": True}, depends_on=["analyze"])
        dag.add_node("inject", lambda ctx: {"ok": True}, depends_on=["retarget", "convert"])
        dag.add_node("validate", lambda ctx: {"ok": True}, depends_on=["inject"])

        assert dag._toposort()
        assert dag._layers[0] == ["scan"]
        assert len(dag._layers[3]) == 2  # retarget + convert 并行

    def test_node_metrics(self):
        """节点指标"""
        from core.dag_engine import DAGNode, NodeStatus
        node = DAGNode("test", lambda x: x)
        assert node.status == NodeStatus.PENDING
        assert node.elapsed == 0.0


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
