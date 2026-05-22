"""
Agent 6: 目标注入师 TargetInjector

将转换后的角色资产注入目标游戏运行时。
支持多种注入方式：
- UE4/5: PAK 封包 + LogicMods
- Unity: BepInEx / Harmony
- Godot: PCK 封包 + Cecil IL 织入
- RE Engine: PAK 封包 + Fluffy Mod Manager
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger("chimera.target_injector")


class InjectionMethod(Enum):
    PAK_PATCH = "pak_patch"          # PAK 文件替换
    LOGICMODS = "logicmods"          # UE4 LogicMods 目录
    BEPINEX = "bepinex"              # Unity BepInEx 插件
    HARMONY = "harmony"              # Harmony 补丁
    CECIL_WEAVE = "cecil_weave"      # Cecil IL 织入
    DLL_HOOK = "dll_hook"            # Native DLL Hook
    FLUFFY_MOD = "fluffy_mod"        # RE Engine Fluffy Mod Manager
    ASSET_REPLACE = "asset_replace"   # 直接资产替换


class TargetInjector:
    """
    目标注入师

    根据目标游戏引擎选择合适的注入策略：
    - 备份原始文件（安全第一！）
    - 注入转换后的资产
    - 验证注入完整性
    """

    def inject(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行资产注入

        Args:
            context: 包含 bus、upstream_results

        Returns:
            注入结果
        """
        bus = context.get("bus")
        upstream = context.get("upstream_results", {})

        target_engine = (
            (bus.get("target_engine") if bus else None) or
            upstream.get("target_engine", "ue4")
        )
        target_path = (
            (bus.get("target_game_path") if bus else None) or
            upstream.get("target_game_path", "")
        )

        logger.info(f"💉 开始注入目标游戏: {target_path} (引擎: {target_engine})")

        # 1. 选择注入策略
        method = self._select_method(target_engine)
        logger.info(f"  注入方式: {method.value}")

        # 2. 备份原始文件
        backup_result = self._backup_original(target_path, target_engine)

        # 3. 执行注入
        inject_result = self._inject_assets(target_path, target_engine, method)

        # 4. 验证注入
        validation = self._validate_injection(target_path, target_engine)

        report = {
            "target_path": target_path,
            "target_engine": target_engine,
            "injection_method": method.value,
            "backup": backup_result,
            "injection": inject_result,
            "validation": validation,
            "success": validation.get("passed", False),
        }

        if bus:
            bus.put("injection_method", method.value)
            bus.put("injection_success", report["success"])

        if report["success"]:
            logger.info(f"✅ 注入成功: {method.value}")
        else:
            logger.warning(f"⚠️ 注入完成但有警告: {validation.get('warnings', [])}")

        return report

    def _select_method(self, engine: str) -> InjectionMethod:
        """根据引擎选择注入方式"""
        method_map = {
            "ue4": InjectionMethod.LOGICMODS,
            "unity": InjectionMethod.BEPINEX,
            "godot": InjectionMethod.CECIL_WEAVE,
            "re": InjectionMethod.FLUFFY_MOD,
        }
        return method_map.get(engine, InjectionMethod.ASSET_REPLACE)

    def _backup_original(self, game_path: str, engine: str) -> Dict[str, Any]:
        """备份原始文件"""
        backup_dir = Path(game_path) / ".chimera_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup = {
            "backup_path": str(backup_dir),
            "files_backed_up": 0,
            "size_bytes": 0,
        }

        # 根据引擎类型备份关键文件
        if engine == "ue4":
            # 备份 LogicMods 目录
            logicmods = Path(game_path) / "LogicMods"
            if logicmods.exists():
                backup_logicmods = backup_dir / "LogicMods"
                if not backup_logicmods.exists():
                    shutil.copytree(logicmods, backup_logicmods)
                    backup["files_backed_up"] = len(list(backup_logicmods.rglob("*")))
                    backup["size_bytes"] = sum(
                        f.stat().st_size for f in backup_logicmods.rglob("*") if f.is_file()
                    )
                    logger.info(f"  💾 已备份 LogicMods → {backup_logicmods}")

        elif engine == "godot":
            # 备份原始 .pck
            for pck in Path(game_path).glob("*.pck"):
                backup_path = backup_dir / pck.name
                shutil.copy2(pck, backup_path)
                backup["files_backed_up"] += 1
                backup["size_bytes"] += pck.stat().st_size
                logger.info(f"  💾 已备份 {pck.name}")

        return backup

    def _inject_assets(
        self,
        game_path: str,
        engine: str,
        method: InjectionMethod,
    ) -> Dict[str, Any]:
        """执行资产注入"""
        result = {
            "method": method.value,
            "files_injected": 0,
            "details": [],
        }

        game_dir = Path(game_path)

        if method == InjectionMethod.LOGICMODS:
            # UE4 LogicMods 注入
            logicmods = game_dir / "LogicMods"
            logicmods.mkdir(exist_ok=True)

            # 创建 Mod 目录结构
            mod_dir = logicmods / "ChimeraMigration"
            mod_dir.mkdir(exist_ok=True)
            content_dir = mod_dir / "Content" / "Characters" / "Imported"
            content_dir.mkdir(parents=True, exist_ok=True)

            result["details"].append(f"创建 Mod 目录: {mod_dir}")
            result["details"].append(f"资产将安装到: {content_dir}")
            result["files_injected"] = 1  # Mod 结构文件

            logger.info(f"  📁 LogicMods Mod 目录已就绪")

        elif method == InjectionMethod.CECIL_WEAVE:
            # Godot Cecil IL 织入
            result["details"].append("准备 Cecil IL 织入点")
            result["details"].append("目标: Assembly-CSharp.dll")
            result["files_injected"] = 0  # 需要实际 .dll

        elif method == InjectionMethod.BEPINEX:
            # Unity BepInEx 注入
            plugins_dir = game_dir / "BepInEx" / "plugins" / "ChimeraMigration"
            plugins_dir.mkdir(parents=True, exist_ok=True)
            result["details"].append(f"BepInEx 插件目录: {plugins_dir}")
            result["files_injected"] = 1

        return result

    def _validate_injection(self, game_path: str, engine: str) -> Dict[str, Any]:
        """验证注入完整性"""
        validation = {
            "passed": True,
            "checks": [],
            "warnings": [],
        }

        game_dir = Path(game_path)

        # 检查 Mod 目录是否存在
        if engine == "ue4":
            mod_dir = game_dir / "LogicMods" / "ChimeraMigration"
            if mod_dir.exists():
                validation["checks"].append("✅ LogicMods Mod 目录存在")
            else:
                validation["checks"].append("❌ LogicMods Mod 目录不存在")
                validation["passed"] = False

        elif engine == "godot":
            pck_files = list(game_dir.glob("*.pck"))
            if pck_files:
                validation["checks"].append(f"✅ PCK 文件存在 ({len(pck_files)} 个)")
            else:
                validation["warnings"].append("未找到 PCK 文件（可能是未封包的 Godot 项目）")

        elif engine == "unity":
            plugins = game_dir / "BepInEx" / "plugins"
            if plugins.exists():
                validation["checks"].append("✅ BepInEx 已安装")
            else:
                validation["warnings"].append("BepInEx 未安装，需要先安装 BepInEx")

        return validation

    def rollback(self, game_path: str) -> Dict[str, Any]:
        """回滚注入（恢复备份）"""
        backup_dir = Path(game_path) / ".chimera_backup"
        if not backup_dir.exists():
            return {"success": False, "error": "没有备份"}

        rollback_info = {"success": True, "files_restored": 0}

        # 恢复 LogicMods
        backup_logicmods = backup_dir / "LogicMods"
        if backup_logicmods.exists():
            logicmods = Path(game_path) / "LogicMods"
            if logicmods.exists():
                shutil.rmtree(logicmods)
            shutil.copytree(backup_logicmods, logicmods)
            rollback_info["files_restored"] += len(list(logicmods.rglob("*")))

        logger.info(f"⏪ 已回滚: {rollback_info['files_restored']} 文件恢复")
        return rollback_info
