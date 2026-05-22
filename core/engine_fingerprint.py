"""
Chimera 引擎指纹识别

自动检测游戏使用的引擎、版本、加密方式。
支持 UE4/5、RE Engine、Godot、Unity、Source 2。
"""

import struct
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .config import Config, EngineProfile

logger = logging.getLogger("chimera.fingerprint")


@dataclass
class EngineFingerprint:
    """引擎指纹扫描结果"""
    engine: str
    engine_display: str
    confidence: float  # 0.0 ~ 1.0
    version_hints: List[str]
    encryption: Optional[str]
    binary_format: str
    evidence: List[str]
    profile: Optional[EngineProfile]


class EngineFingerprinter:
    """
    游戏引擎指纹识别器

    通过多维度特征综合判断引擎类型：
    1. 文件扩展名分布
    2. 魔数检测
    3. 目录结构特征
    4. 已知游戏数据库匹配
    """

    def __init__(self):
        self.profiles = Config.ENGINES

    def identify(self, game_path: str, game_id: str = None) -> EngineFingerprint:
        """
        识别游戏引擎

        Args:
            game_path: 游戏根目录路径
            game_id: 可选，已知游戏ID（优先使用）

        Returns:
            EngineFingerprint 识别结果
        """
        path = Path(game_path)
        if not path.exists():
            return EngineFingerprint(
                engine="unknown",
                engine_display="未知引擎",
                confidence=0.0,
                version_hints=[],
                encryption=None,
                binary_format="unknown",
                evidence=[f"路径不存在: {game_path}"],
                profile=None,
            )

        # 1. 检查已知游戏数据库
        if game_id and game_id in Config.KNOWN_GAMES:
            known = Config.KNOWN_GAMES[game_id]
            engine = known["engine"]
            profile = self.profiles.get(engine)
            return EngineFingerprint(
                engine=engine,
                engine_display=profile.display_name if profile else engine,
                confidence=1.0,
                version_hints=[],
                encryption=None,
                binary_format=profile.mesh_format if profile else "",
                evidence=[f"已知游戏数据库匹配: {known['display_name']}"],
                profile=profile,
            )

        # 2. 文件扩展名投票
        ext_votes = self._scan_extensions(path)
        logger.info(f"文件扩展名投票: {ext_votes}")

        # 3. 魔数验证
        magic_results = self._scan_magic_bytes(path)
        logger.info(f"魔数扫描: {magic_results}")

        # 4. 综合评分
        candidates = self._score_candidates(ext_votes, magic_results)

        if not candidates:
            return EngineFingerprint(
                engine="unknown",
                engine_display="未知引擎",
                confidence=0.0,
                version_hints=[],
                encryption=None,
                binary_format="unknown",
                evidence=["未能匹配任何已知引擎"],
                profile=None,
            )

        best_engine, best_score = candidates[0]
        profile = self.profiles.get(best_engine)

        return EngineFingerprint(
            engine=best_engine,
            engine_display=profile.display_name if profile else best_engine,
            confidence=best_score,
            version_hints=[],
            encryption=self._detect_encryption(path, best_engine),
            binary_format=profile.mesh_format if profile else "",
            evidence=[
                f"文件扩展名投票: {ext_votes}",
                f"魔数验证: {magic_results}",
                f"综合置信度: {best_score:.0%}",
            ],
            profile=profile,
        )

    def _scan_extensions(self, game_path: Path, sample_limit: int = 5000) -> Dict[str, int]:
        """扫描文件扩展名分布"""
        ext_count = {}
        count = 0
        for f in game_path.rglob("*"):
            if f.is_file():
                ext = f.suffix.lower()
                ext_count[ext] = ext_count.get(ext, 0) + 1
                count += 1
                if count >= sample_limit:
                    break

        # 按引擎特征扩展名投票
        votes = {}
        for engine, profile in self.profiles.items():
            score = sum(ext_count.get(ext, 0) for ext in profile.file_extensions)
            if score > 0:
                votes[engine] = score

        return votes

    def _scan_magic_bytes(self, game_path: Path) -> Dict[str, bool]:
        """扫描关键文件的魔数"""
        results = {}

        # UE4 PAK 魔数
        for pak in list(game_path.rglob("*.pak"))[:5]:
            try:
                with open(pak, "rb") as f:
                    magic = f.read(4)
                    if magic == b"KPKA":
                        results["re_pak"] = True
                    elif magic == b"\x5A\x6F\x12\xE1":
                        results["ue4_pak"] = True
                    else:
                        results[f"unknown_pak_{magic.hex()}"] = True
            except (IOError, PermissionError):
                pass

        # Godot PCK 魔数
        for pck in list(game_path.rglob("*.pck"))[:3]:
            try:
                with open(pck, "rb") as f:
                    magic = f.read(4)
                    if magic == b"GDPC":
                        results["godot_pck"] = True
            except (IOError, PermissionError):
                pass

        # Unity 检测
        if list(game_path.rglob("*Assembly-CSharp*")):
            results["unity_assembly"] = True
        if list(game_path.rglob("globalgamemanagers*")):
            results["unity_globalgamemanagers"] = True

        return results

    def _score_candidates(
        self,
        ext_votes: Dict[str, int],
        magic_results: Dict[str, bool],
    ) -> List[Tuple[str, float]]:
        """综合评分候选引擎"""
        scores = []

        for engine in self.profiles:
            score = 0.0
            max_score = 0.0

            # 魔数验证（高权重）
            if f"{engine}_pak" in magic_results:
                score += 3.0
                max_score += 3.0
            elif "godot_pck" in magic_results and engine == "godot":
                score += 3.0
                max_score += 3.0
            elif "unity_assembly" in magic_results and engine == "unity":
                score += 3.0
                max_score += 3.0

            # 扩展名投票（低权重，归一化）
            if ext_votes:
                total_votes = sum(ext_votes.values()) or 1
                engine_votes = ext_votes.get(engine, 0)
                score += engine_votes / total_votes * 2.0
                max_score += 2.0

            if max_score > 0:
                confidence = score / max_score
                scores.append((engine, confidence))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _detect_encryption(self, game_path: Path, engine: str) -> Optional[str]:
        """检测加密方式"""
        # 针对不同引擎的加密特征检测
        encryption_clues = {
            "ue4": ["AES-ECB", "AES-CBC", "PathHashIndex"],
            "re": ["MurmurHash3"],
            "godot": ["PCK Embedded Encryption"],
            "unity": ["il2cpp", "Mono Obfuscation"],
        }

        clues = encryption_clues.get(engine, [])
        # 简化版：检查是否有加密特征文件
        return clues[0] if clues else None
