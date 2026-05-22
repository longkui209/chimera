"""
Chimera CLI 启动入口

用法:
  chimera scan                     扫描工具链
  chimera fingerprint <path>       识别游戏引擎
  chimera migrate <src> <dst>      执行跨游戏角色迁移
  chimera serve                    启动 API 服务
  chimera list games               列出可用游戏
  chimera list engines             列出支持引擎
  chimera list paths               列出格式转换路径
  chimera inspect                  查看流水线结构
  chimera stats                    查看知识库统计
  chimera rollback <path>          回滚注入
"""

import sys
import os
import json
import asyncio
import argparse
from pathlib import Path

# 确保从项目根目录导入
_sys_path = str(Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)


def cmd_scan(args):
    """扫描工具链"""
    from tools.toolchain import scan
    scan()


def cmd_fingerprint(args):
    """识别游戏引擎"""
    from core.engine_fingerprint import EngineFingerprinter

    fp = EngineFingerprinter()
    result = fp.identify(args.path, args.game_id)

    print(f"\n🔍 引擎识别: {Path(args.path).name}")
    print(f"   引擎:    {result.engine_display}")
    print(f"   置信度:  {result.confidence:.0%}")
    print(f"   加密:    {result.encryption or '无/未知'}")
    print(f"   格式:    {result.binary_format}")
    print(f"   证据:")

    for ev in result.evidence:
        print(f"     → {ev}")

    if result.profile:
        print(f"\n📋 {result.engine_display} 特性:")
        print(f"   网格格式:   {result.profile.mesh_format}")
        print(f"   骨架格式:   {result.profile.skeleton_format}")
        print(f"   动画格式:   {result.profile.anim_format}")
        print(f"   注入方式:   {', '.join(result.profile.injection_methods)}")


def cmd_migrate(args):
    """执行跨游戏角色迁移"""
    from agents.orchestrator import ChimeraOrchestrator

    async def _run():
        orch = ChimeraOrchestrator()
        print(f"\n🦁🐐🐍 Chimera 跨游戏迁移启动")
        print(f"   源游戏:   {Path(args.source).name}")
        print(f"   目标游戏: {Path(args.target).name}")
        print(f"   {'-'*40}")

        result = await orch.migrate(
            source_game_path=args.source,
            target_game_path=args.target,
            source_game_id=args.source_id,
            target_game_id=args.target_id,
        )

        print(f"\n{'='*40}")
        print(f"📊 迁移结果:")
        print(f"   成功:     {'✅' if result['success'] else '❌'}")
        print(f"   耗时:     {result['elapsed_seconds']:.1f}s")
        print(f"   Token:    ~{result['total_tokens']:,}")
        print(f"   指标:     {json.dumps(result['metrics'], indent=2)}")
        return result

    return asyncio.run(_run())


def cmd_serve(args):
    """启动 API 服务"""
    import uvicorn
    from core.config import Config

    print(f"\n🚀 启动 Chimera API 服务")
    print(f"   地址: http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"   文档: http://{Config.API_HOST}:{Config.API_PORT}/docs")
    print(f"   {'='*40}\n")

    uvicorn.run(
        "api.server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=args.reload,
    )


def cmd_list_games(args):
    """列出可用游戏"""
    from core.config import Config

    known = Config.KNOWN_GAMES
    print(f"\n🎮 已知游戏 ({len(known)} 款):\n")
    print(f"  {'ID':<30} {'名称':<20} {'引擎':<12} {'大小'}")
    print(f"  {'-'*70}")
    for game_id, info in sorted(known.items()):
        print(f"  {game_id:<30} {info['display_name']:<20} {info['engine']:<12} {info['size_gb']}GB")


def cmd_list_engines(args):
    """列出支持引擎"""
    from core.config import Config

    print(f"\n🔧 支持引擎 ({len(Config.ENGINES)}):\n")
    for name, profile in Config.ENGINES.items():
        print(f"  🎯 {profile.display_name}")
        print(f"     ID:         {name}")
        print(f"     魔数:       {[m.hex() for m in profile.magic_bytes]}")
        print(f"     文件扩展:   {', '.join(profile.file_extensions)}")
        print(f"     注入方式:   {', '.join(profile.injection_methods)}")
        print()


def cmd_list_paths(args):
    """列出格式转换路径"""
    from agents.format_translator import FormatTranslator

    ft = FormatTranslator()
    paths = ft.get_conversion_paths()
    print(f"\n🔀 格式转换路径 ({len(paths)} 条):\n")
    print(f"  {'源引擎':<10} {'→':<2} {'目标引擎':<10} {'复杂度':<12} {'中间格式'}")
    print(f"  {'-'*55}")
    for p in paths:
        print(f"  {p['source']:<10} →  {p['target']:<10} {p['complexity']:<12} {p['intermediate'] or '直接'}")


def cmd_inspect(args):
    """查看流水线结构"""
    from agents.orchestrator import ChimeraOrchestrator

    orch = ChimeraOrchestrator()
    info = orch.inspect_pipeline()

    print(f"\n🏗️ Chimera DAG 流水线")
    print(f"   总节点: {info['total_nodes']}")
    print(f"   总层级: {info['total_layers']}")
    print(f"   {'='*40}")
    for layer in info["layers"]:
        nodes = " + ".join(layer["nodes"])
        print(f"   第{layer['level']}层 [{layer['parallel']}并行]: {nodes}")


def cmd_stats(args):
    """查看知识库统计"""
    from core.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    stats = kb.stats()

    print(f"\n📚 知识库统计")
    print(f"   {'='*30}")
    print(f"   总迁移次数:   {stats['total_migrations']}")
    print(f"   成功:         {stats['successful']}")
    print(f"   失败:         {stats['failed']}")
    print(f"   成功率:       {stats['success_rate']:.1f}%")
    print(f"   骨骼映射:     {stats['skeleton_mappings']}")
    print(f"   引擎配对:     {len(stats['engine_pairs'])}")
    for pair in stats["engine_pairs"]:
        print(f"     → {pair}")


def cmd_rollback(args):
    """回滚注入"""
    from agents.target_injector import TargetInjector

    print(f"\n⏪ 回滚: {Path(args.path).name}")
    injector = TargetInjector()
    result = injector.rollback(args.path)

    if result["success"]:
        print(f"   ✅ 回滚成功: {result['files_restored']} 文件恢复")
    else:
        print(f"   ❌ 回滚失败: {result.get('error', '未知错误')}")


def cmd_doctor(args):
    """系统诊断"""
    print("\n🏥 Chimera 系统诊断\n" + "=" * 40)

    # Python 版本
    print(f"  Python:    {sys.version.split()[0]}")

    # 项目路径
    print(f"  项目路径:  /data/chimera")

    # 依赖检查
    deps = ["fastapi", "uvicorn", "pydantic", "pytest"]
    for dep in deps:
        try:
            __import__(dep)
            print(f"  {dep:<15} ✅")
        except ImportError:
            print(f"  {dep:<15} ❌")

    # 磁盘空间
    import shutil
    total, used, free = shutil.disk_usage("/data/chimera")
    print(f"  磁盘空间:   {free // (1024**3)}GB 可用")

    # 游戏库
    from core.config import Config
    games = Config.discover_games()
    print(f"  游戏库:     {len(games)} 款游戏可用")

    print("\n🔧 工具链:")
    from tools.toolchain import scan
    scan()


def main():
    parser = argparse.ArgumentParser(
        description="🦁🐐🐍 Chimera - AI 跨游戏角色与资产融合迁移引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  chimera scan                     扫描工具链
  chimera fingerprint /path/game   识别游戏引擎
  chimera migrate /src /dst        迁移角色
  chimera serve                    启动 API 服务
  chimera list games               列出可用游戏
  chimera doctor                   系统诊断
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # scan
    p_scan = subparsers.add_parser("scan", help="扫描工具链")
    p_scan.set_defaults(func=cmd_scan)

    # fingerprint
    p_fp = subparsers.add_parser("fingerprint", help="识别游戏引擎")
    p_fp.add_argument("path", help="游戏路径")
    p_fp.add_argument("--id", dest="game_id", help="已知游戏ID")
    p_fp.set_defaults(func=cmd_fingerprint)

    # migrate
    p_mig = subparsers.add_parser("migrate", help="执行跨游戏迁移")
    p_mig.add_argument("source", help="源游戏路径")
    p_mig.add_argument("target", help="目标游戏路径")
    p_mig.add_argument("--source-id", dest="source_id", help="源游戏ID")
    p_mig.add_argument("--target-id", dest="target_id", help="目标游戏ID")
    p_mig.set_defaults(func=cmd_migrate)

    # serve
    p_srv = subparsers.add_parser("serve", help="启动 API 服务")
    p_srv.add_argument("--reload", action="store_true", help="热重载")
    p_srv.set_defaults(func=cmd_serve)

    # list games
    p_lg = subparsers.add_parser("list", help="列出资源")
    p_lg.add_argument("what", choices=["games", "engines", "paths"],
                      help="列出类型")
    p_lg.set_defaults(func=lambda a: {
        "games": cmd_list_games,
        "engines": cmd_list_engines,
        "paths": cmd_list_paths,
    }[a.what](a))

    # inspect
    p_ins = subparsers.add_parser("inspect", help="查看流水线结构")
    p_ins.set_defaults(func=cmd_inspect)

    # stats
    p_sts = subparsers.add_parser("stats", help="查看知识库统计")
    p_sts.set_defaults(func=cmd_stats)

    # rollback
    p_rb = subparsers.add_parser("rollback", help="回滚注入")
    p_rb.add_argument("path", help="游戏路径")
    p_rb.set_defaults(func=cmd_rollback)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="系统诊断")
    p_doc.set_defaults(func=cmd_doctor)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
