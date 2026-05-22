"""
Chimera 工具链管理器

管理系统级工具的发现、安装、版本验证：
- umodel (UE4/5 资产导出)
- FModel (UE4/5 资产浏览)
- AssetRipper (Unity 资产提取)
- QuickBMS (通用 PAK 解包)
- Blender (3D 模型处理)
- ikdasm (IL 反编译)
- Godot (引擎运行时)
"""

import os
import re
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger("chimera.toolchain")


class ToolStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    UNKNOWN_VERSION = "unknown_version"
    ERROR = "error"


@dataclass
class ToolInfo:
    """单个工具信息"""
    name: str
    display_name: str
    category: str  # "extraction", "conversion", "injection", "analysis"
    description: str
    required: bool = False
    # 发现路径
    known_paths: List[str] = field(default_factory=list)
    found_path: Optional[str] = None
    # 版本
    version: Optional[str] = None
    status: ToolStatus = ToolStatus.NOT_FOUND
    # 命令
    test_command: Optional[str] = None
    install_hint: str = ""


class ToolchainManager:
    """
    工具链管理器

    职责：
    1. 自动发现系统已安装的工具
    2. 版本验证
    3. 缺失工具提示
    4. 为 Agent 提供工具路径
    """

    # === 已知工具注册表 ===
    TOOL_REGISTRY: Dict[str, ToolInfo] = {
        "umodel": ToolInfo(
            name="umodel",
            display_name="UE Viewer (umodel)",
            category="extraction",
            description="UE4/5 资产导出工具，支持 SkeletalMesh/Texture/Animation 提取",
            required=True,
            known_paths=[
                "/home/chenyixun710/UEViewer/umodel",
                "/mnt/hgfs/游戏解包/umodel",
                "/usr/local/bin/umodel",
                str(Path.home() / "UEViewer/umodel"),
            ],
            test_command="umodel -help 2>&1 | head -3",
            install_hint="下载: https://www.gildor.org/downloads",
        ),
        "fmodel": ToolInfo(
            name="fmodel",
            display_name="FModel",
            category="extraction",
            description="UE4/5 资产浏览器，支持 PAK 解析和批量导出",
            required=False,
            known_paths=[
                "/mnt/hgfs/游戏解包/FModel_latest",
                "/mnt/hgfs/游戏解包/FModel",
            ],
            test_command="ls FModel 2>/dev/null || ls FModel* 2>/dev/null",
            install_hint="下载: https://fmodel.app/",
        ),
        "assetripper": ToolInfo(
            name="assetripper",
            display_name="AssetRipper",
            category="extraction",
            description="Unity 资产提取工具，支持 AssetBundle 和序列化资源",
            required=False,
            known_paths=[
                "/mnt/hgfs/游戏解包/AssetRipper",
                str(Path.home() / "AssetRipper"),
            ],
            test_command="ls AssetRipper* 2>/dev/null",
            install_hint="下载: https://github.com/AssetRipper/AssetRipper",
        ),
        "quickbms": ToolInfo(
            name="quickbms",
            display_name="QuickBMS",
            category="extraction",
            description="通用 PAK/资源包解包工具，支持数千种游戏格式",
            required=False,
            known_paths=[
                "/home/chenyixun710/quickbms.exe",
                "/usr/local/bin/quickbms",
            ],
            test_command="wine quickbms.exe 2>&1 | head -3 || quickbms 2>&1 | head -3",
            install_hint="下载: https://aluigi.altervista.org/quickbms.htm",
        ),
        "godot": ToolInfo(
            name="godot",
            display_name="Godot Engine",
            category="conversion",
            description="Godot 引擎运行时，用于 Godot 游戏的 PCK 分析和导入",
            required=False,
            known_paths=[
                "/mnt/hgfs/游戏解包/Godot_v4.6.1-stable_mono_win64",
                "/usr/local/bin/godot",
                str(Path.home() / "Godot"),
            ],
            test_command="ls Godot* 2>/dev/null | head -1",
            install_hint="下载: https://godotengine.org/download",
        ),
        "blender": ToolInfo(
            name="blender",
            display_name="Blender",
            category="conversion",
            description="3D 模型处理，骨架重定向，FBX/glTF 导入导出",
            required=True,
            known_paths=["/usr/bin/blender", "/usr/local/bin/blender"],
            test_command="blender --version 2>&1 | head -1",
            install_hint="sudo apt install blender 或 https://www.blender.org/download",
        ),
        "ikdasm": ToolInfo(
            name="ikdasm",
            display_name="ikdasm (IL Disassembler)",
            category="analysis",
            description=".NET IL 反编译工具，用于 Godot .NET 游戏分析",
            required=False,
            known_paths=[
                "/usr/lib/dotnet/sdk/*/ikdasm",
                str(Path.home() / ".dotnet/tools/ikdasm"),
                "/usr/local/bin/ikdasm",
            ],
            test_command="ikdasm 2>&1 | head -3 || dotnet ikdasm 2>&1 | head -3",
            install_hint="dotnet tool install -g dotnet-ikdasm",
        ),
        "dotnet": ToolInfo(
            name="dotnet",
            display_name=".NET SDK",
            category="analysis",
            description="C# 操作运行时，用于 Cecil IL 织入和 Godot .NET 分析",
            required=False,
            known_paths=["/usr/bin/dotnet", "/usr/local/bin/dotnet"],
            test_command="dotnet --version 2>&1",
            install_hint="下载: https://dotnet.microsoft.com/download",
        ),
        "wine": ToolInfo(
            name="wine",
            display_name="Wine",
            category="extraction",
            description="Windows 兼容层，用于运行 Windows 专用工具 (umodel, quickbms 等)",
            required=False,
            known_paths=["/usr/bin/wine", "/usr/local/bin/wine"],
            test_command="wine --version 2>&1",
            install_hint="sudo apt install wine",
        ),
        "python3": ToolInfo(
            name="python3",
            display_name="Python 3",
            category="analysis",
            description="Python 运行时 (>= 3.8)",
            required=True,
            known_paths=["/usr/bin/python3"],
            test_command="python3 --version 2>&1",
            install_hint="sudo apt install python3",
        ),
        "fastapi": ToolInfo(
            name="fastapi",
            display_name="FastAPI",
            category="analysis",
            description="Web 框架",
            required=True,
            known_paths=["/usr/local/lib/python3*/dist-packages/fastapi"],
            test_command="python3 -c 'import fastapi; print(fastapi.__version__)' 2>&1",
            install_hint="pip install fastapi",
        ),
    }

    def __init__(self):
        self.discovered: Dict[str, ToolInfo] = {}

    def discover_all(self) -> Dict[str, ToolInfo]:
        """发现所有工具"""
        logger.info("🔧 开始工具链扫描...")
        self.discovered = {}

        for name, tool in self.TOOL_REGISTRY.items():
            found = self._find_tool(tool)
            self.discovered[name] = found
            if found.status == ToolStatus.FOUND:
                logger.info(f"  ✅ {tool.display_name}: {found.found_path} ({found.version or '未知版本'})")
            elif tool.required:
                logger.warning(f"  ❌ {tool.display_name}: 未找到（必需）")
            else:
                logger.info(f"  ⚠️ {tool.display_name}: 未找到（可选）")

        return self.discovered

    def _find_tool(self, tool: ToolInfo) -> ToolInfo:
        """查找单个工具"""
        result = ToolInfo(
            name=tool.name,
            display_name=tool.display_name,
            category=tool.category,
            description=tool.description,
            required=tool.required,
            known_paths=list(tool.known_paths),
            install_hint=tool.install_hint,
        )

        # 1. 遍历已知路径
        for path_pattern in tool.known_paths:
            # 展开 glob
            if "*" in path_pattern:
                import glob as _glob
                matches = _glob.glob(path_pattern)
                for m in matches:
                    if self._check_path(m, tool):
                        result.found_path = m
                        result.status = ToolStatus.FOUND
                        break
            else:
                if self._check_path(path_pattern, tool):
                    result.found_path = path_pattern
                    result.status = ToolStatus.FOUND
                    break

        # 2. PATH 查找
        if result.status != ToolStatus.FOUND:
            which = shutil.which(tool.name)
            if which:
                result.found_path = which
                result.status = ToolStatus.FOUND

        # 3. 获取版本
        if result.status == ToolStatus.FOUND and tool.test_command:
            result.version = self._get_version(result.found_path, tool)

        return result

    def _check_path(self, path: str, tool: ToolInfo) -> bool:
        """检查路径是否有效"""
        p = Path(path)
        if tool.name in ("fmodel", "godot", "assetripper"):
            # 目录类型工具
            return p.is_dir()
        else:
            # 可执行文件
            return p.is_file() and (os.access(p, os.X_OK) or path.endswith(".exe"))

    def _get_version(self, path: str, tool: ToolInfo) -> Optional[str]:
        """获取工具版本"""
        try:
            if tool.test_command:
                cmd = tool.test_command.replace(tool.name, path)
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=10
                )
                output = result.stdout or result.stderr
                # 尝试提取版本号
                version_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
                if version_match:
                    return version_match.group(1)
                return output.strip().split("\n")[0][:50]
        except Exception:
            pass
        return None

    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """获取指定工具的路径"""
        if tool_name in self.discovered:
            tool = self.discovered[tool_name]
            if tool.status == ToolStatus.FOUND:
                return tool.found_path
        return None

    def check_required(self) -> Tuple[bool, List[str]]:
        """检查必需工具是否就绪"""
        missing = []
        for name, tool in self.discovered.items():
            if tool.required and tool.status != ToolStatus.FOUND:
                missing.append(f"{tool.display_name} ({tool.install_hint})")

        return len(missing) == 0, missing

    def generate_report(self) -> Dict:
        """生成工具链报告"""
        report = {
            "scanned_at": str(subprocess.run(
                ["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True
            ).stdout.strip()),
            "total_tools": len(self.discovered),
            "found": sum(1 for t in self.discovered.values() if t.status == ToolStatus.FOUND),
            "required_missing": [],
            "optional_missing": [],
            "tools": {},
        }

        for name, tool in self.discovered.items():
            report["tools"][name] = {
                "display_name": tool.display_name,
                "category": tool.category,
                "required": tool.required,
                "status": tool.status.value,
                "path": tool.found_path,
                "version": tool.version,
            }

            if tool.required and tool.status != ToolStatus.FOUND:
                report["required_missing"].append({
                    "name": tool.display_name,
                    "install_hint": tool.install_hint,
                })
            elif not tool.required and tool.status != ToolStatus.FOUND:
                report["optional_missing"].append({
                    "name": tool.display_name,
                    "install_hint": tool.install_hint,
                })

        return report

    def print_report(self) -> str:
        """打印可读的工具链报告"""
        report = self.generate_report()
        lines = []
        lines.append("=" * 60)
        lines.append("🔧 Chimera 工具链状态报告")
        lines.append("=" * 60)
        lines.append(f"扫描时间: {report['scanned_at']}")
        lines.append(f"总计: {report['total_tools']} 工具")
        lines.append(f"已找到: {report['found']}")
        lines.append(f"缺失(必需): {len(report['required_missing'])}")
        lines.append(f"缺失(可选): {len(report['optional_missing'])}")
        lines.append("-" * 60)

        # 按分类分组
        categories = {}
        for name, info in report["tools"].items():
            cat = info["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name, info))

        for cat, tools in categories.items():
            lines.append(f"\n📂 {cat.upper()}:")
            for name, info in tools:
                icon = "✅" if info["status"] == "found" else ("❌" if info["required"] else "⚠️")
                path_str = info["path"] or "—"
                ver_str = f" v{info['version']}" if info["version"] else ""
                lines.append(f"  {icon} {info['display_name']}{ver_str}")
                lines.append(f"     {path_str}")

        if report["required_missing"]:
            lines.append("\n❌ 必需工具缺失:")
            for t in report["required_missing"]:
                lines.append(f"   • {t['name']}: {t['install_hint']}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# ============================================================
# 快速入口
# ============================================================

def scan():
    """快速扫描工具链"""
    mgr = ToolchainManager()
    mgr.discover_all()
    print(mgr.print_report())
    return mgr


if __name__ == "__main__":
    scan()
