"""
Chimera API Server

FastAPI 服务，提供跨游戏角色迁移的 RESTful API。
"""

import sys
from pathlib import Path as _Path
_sys_path = str(_Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import Config
from core.engine_fingerprint import EngineFingerprinter
from core.knowledge_base import KnowledgeBase
from agents.orchestrator import ChimeraOrchestrator

logger = logging.getLogger("chimera.api")

# 初始化
app = FastAPI(
    title="Chimera API",
    description="AI 跨游戏角色与资产融合迁移引擎",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ChimeraOrchestrator()
fingerprinter = EngineFingerprinter()
kb = KnowledgeBase()


# === Pydantic Models ===

class MigrationRequest(BaseModel):
    source_game_path: str = Field(..., description="源游戏根目录路径")
    target_game_path: str = Field(..., description="目标游戏根目录路径")
    source_game_id: Optional[str] = Field(None, description="源游戏注册 ID")
    target_game_id: Optional[str] = Field(None, description="目标游戏注册 ID")


class FingerprintRequest(BaseModel):
    game_path: str = Field(..., description="游戏根目录路径")
    game_id: Optional[str] = Field(None, description="游戏注册 ID")


class RollbackRequest(BaseModel):
    game_path: str = Field(..., description="游戏根目录路径")


# === API Endpoints ===

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Chimera",
        "version": "0.1.0",
        "agents": 8,
        "dag_layers": 6,
    }


@app.get("/api/v1/pipeline/inspect")
async def inspect_pipeline():
    """查看流水线结构"""
    return orchestrator.inspect_pipeline()


@app.get("/api/v1/games")
async def list_games():
    """列出支持的游戏"""
    return {
        "games": orchestrator.list_supported_games(),
        "total": len(orchestrator.list_supported_games()),
    }


@app.get("/api/v1/engines")
async def list_engines():
    """列出支持的引擎"""
    engines = {}
    for name, profile in Config.ENGINES.items():
        engines[name] = {
            "display_name": profile.display_name,
            "file_extensions": profile.file_extensions,
            "injection_methods": profile.injection_methods,
            "mesh_format": profile.mesh_format,
            "skeleton_format": profile.skeleton_format,
        }
    return {"engines": engines, "count": len(engines)}


@app.get("/api/v1/conversions")
async def list_conversions():
    """列出支持的格式转换路径"""
    return {
        "paths": orchestrator.list_conversion_paths(),
        "total": len(orchestrator.list_conversion_paths()),
    }


@app.post("/api/v1/fingerprint")
async def fingerprint_game(req: FingerprintRequest):
    """识别游戏引擎"""
    result = fingerprinter.identify(req.game_path, req.game_id)
    return {
        "game_path": req.game_path,
        "engine": result.engine,
        "engine_display": result.engine_display,
        "confidence": result.confidence,
        "evidence": result.evidence,
        "encryption": result.encryption,
    }


@app.post("/api/v1/migrate")
async def migrate(req: MigrationRequest):
    """
    执行跨游戏角色迁移

    完整流水线：
    源解构 → 角色提取 → 骨架分析 → 动画重定向 → 格式转换 → 目标注入 → 运行时验证
    """
    if not Path(req.source_game_path).exists():
        raise HTTPException(404, f"源游戏路径不存在: {req.source_game_path}")
    if not Path(req.target_game_path).exists():
        raise HTTPException(404, f"目标游戏路径不存在: {req.target_game_path}")

    result = await orchestrator.migrate(
        source_game_path=req.source_game_path,
        target_game_path=req.target_game_path,
        source_game_id=req.source_game_id,
        target_game_id=req.target_game_id,
    )

    return result


@app.post("/api/v1/rollback")
async def rollback(req: RollbackRequest):
    """回滚注入（恢复备份）"""
    from target_injector import TargetInjector
    injector = TargetInjector()
    result = injector.rollback(req.game_path)
    if not result["success"]:
        raise HTTPException(400, result.get("error", "回滚失败"))
    return result


@app.get("/api/v1/knowledge/stats")
async def knowledge_stats():
    """知识库统计"""
    return kb.stats()


@app.get("/api/v1/knowledge/migrations")
async def knowledge_migrations(source_game: Optional[str] = None, limit: int = 50):
    """查询迁移历史"""
    return {
        "migrations": kb.query_migrations(source_game, limit),
        "count": len(kb.query_migrations(source_game, limit)),
    }


# === 启动入口 ===

def main():
    import uvicorn
    uvicorn.run(
        "chimera.api.server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
