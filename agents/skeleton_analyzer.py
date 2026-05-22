"""
Agent 3: 骨架分析师 SkeletonAnalyzer

分析源角色和目标角色的骨架结构，建立骨骼映射关系。
核心算法：基于骨骼名称、拓扑结构、空间位置的相似度匹配。
"""

import sys
from pathlib import Path as _Path
_sys_path = str(_Path(__file__).parent.parent)
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("chimera.skeleton_analyzer")


@dataclass
class BoneInfo:
    """骨骼信息"""
    name: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    position_hint: str = ""  # 位置提示: "root", "spine", "arm", "leg", "head"


class SkeletonAnalyzer:
    """
    骨架分析师

    通过多维度特征匹配建立源→目标骨骼映射：
    1. 名称相似度（编辑距离 / 子串匹配）
    2. 拓扑结构（父子关系、层级深度）
    3. 语义位置（root/spine/arm/leg/head 等）
    """

    # 通用骨骼名称模式（不区分引擎）
    BONE_PATTERNS = {
        "root": ["root", "pelvis", "hips", "hip", "bip001"],
        "spine": ["spine", "spine0", "spine1", "spine2", "spine3", "spine01", "spine02"],
        "neck": ["neck", "neck0", "neck1", "neck01", "neck_01"],
        "head": ["head", "head_end", "skull", "cabeza"],
        "left_arm": ["clavicle_l", "l_clavicle", "leftshoulder", "shoulder_l"],
        "left_upper_arm": ["upperarm_l", "l_upperarm", "leftupperarm", "arm_l", "l_arm"],
        "left_lower_arm": ["lowerarm_l", "l_lowerarm", "leftlowerarm", "forearm_l", "l_forearm"],
        "left_hand": ["hand_l", "l_hand", "lefthand", "wrist_l"],
        "right_arm": ["clavicle_r", "r_clavicle", "rightshoulder", "shoulder_r"],
        "right_upper_arm": ["upperarm_r", "r_upperarm", "rightupperarm", "arm_r", "r_arm"],
        "right_lower_arm": ["lowerarm_r", "r_lowerarm", "rightlowerarm", "forearm_r", "r_forearm"],
        "right_hand": ["hand_r", "r_hand", "righthand", "wrist_r"],
        "left_leg": ["thigh_l", "l_thigh", "leftthigh", "upleg_l", "l_upleg"],
        "left_lower_leg": ["calf_l", "l_calf", "leftcalf", "shin_l"],
        "left_foot": ["foot_l", "l_foot", "leftfoot", "ankle_l"],
        "right_leg": ["thigh_r", "r_thigh", "rightthigh", "upleg_r", "r_upleg"],
        "right_lower_leg": ["calf_r", "r_calf", "rightcalf", "shin_r"],
        "right_foot": ["foot_r", "r_foot", "rightfoot", "ankle_r"],
    }

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析骨架并建立映射

        Args:
            context: 包含 bus、upstream_results

        Returns:
            骨骼映射关系
        """
        bus = context.get("bus")
        upstream = context.get("upstream_results", {})

        # 获取源角色骨架信息
        source_characters = (
            (bus.get("extracted_characters") if bus else None) or
            upstream.get("source_characters", [])
        )
        source_engine = (
            (bus.get("source_engine") if bus else None) or
            upstream.get("source_engine", "unknown")
        )

        if not source_characters:
            return {"error": "没有可用的源角色骨骼数据"}

        source_char = source_characters[0] if isinstance(source_characters, list) else source_characters

        logger.info(f"🦴 开始分析骨架: {source_char.get('name', 'unknown')}")

        # 模拟骨架分析（实际会从提取的资产中解析）
        source_bones = self._extract_bone_list(source_char)
        target_bones = self._generate_target_bone_list(source_engine)

        # 建立映射
        bone_mapping = self._match_bones(source_bones, target_bones)
        confidence = self._calculate_confidence(bone_mapping)

        report = {
            "source_character": source_char.get("name", "unknown"),
            "source_engine": source_engine,
            "source_bones": source_bones,
            "target_bones": target_bones,
            "bone_mapping": bone_mapping,
            "mapping_confidence": confidence,
            "mapped_count": len(bone_mapping),
            "total_source_bones": len(source_bones),
            "total_target_bones": len(target_bones),
        }

        if bus:
            bus.put("bone_mapping", bone_mapping)
            bus.put("mapping_confidence", confidence)

        logger.info(f"✅ 骨架分析完成: {len(bone_mapping)}/{len(source_bones)} 骨骼映射 "
                     f"(置信度 {confidence:.0%})")
        return report

    def _extract_bone_list(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从角色资产中提取骨骼列表"""
        engine = character.get("engine", "unknown")

        if engine == "ue4":
            return self._ue4_bone_list(character)
        elif engine == "unity":
            return self._unity_bone_list()
        elif engine == "godot":
            return self._godot_bone_list()
        else:
            return self._generic_bone_list()

    def _ue4_bone_list(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """UE4 标准人形骨骼"""
        bones = [
            {"name": "Root", "parent": None, "position": "root"},
            {"name": "Pelvis", "parent": "Root", "position": "spine"},
            {"name": "spine_01", "parent": "Pelvis", "position": "spine"},
            {"name": "spine_02", "parent": "spine_01", "position": "spine"},
            {"name": "spine_03", "parent": "spine_02", "position": "spine"},
            {"name": "neck_01", "parent": "spine_03", "position": "neck"},
            {"name": "head", "parent": "neck_01", "position": "head"},
            {"name": "clavicle_l", "parent": "spine_03", "position": "left_arm"},
            {"name": "upperarm_l", "parent": "clavicle_l", "position": "left_upper_arm"},
            {"name": "lowerarm_l", "parent": "upperarm_l", "position": "left_lower_arm"},
            {"name": "hand_l", "parent": "lowerarm_l", "position": "left_hand"},
            {"name": "clavicle_r", "parent": "spine_03", "position": "right_arm"},
            {"name": "upperarm_r", "parent": "clavicle_r", "position": "right_upper_arm"},
            {"name": "lowerarm_r", "parent": "upperarm_r", "position": "right_lower_arm"},
            {"name": "hand_r", "parent": "lowerarm_r", "position": "right_hand"},
            {"name": "thigh_l", "parent": "Pelvis", "position": "left_leg"},
            {"name": "calf_l", "parent": "thigh_l", "position": "left_lower_leg"},
            {"name": "foot_l", "parent": "calf_l", "position": "left_foot"},
            {"name": "thigh_r", "parent": "Pelvis", "position": "right_leg"},
            {"name": "calf_r", "parent": "thigh_r", "position": "right_lower_leg"},
            {"name": "foot_r", "parent": "calf_r", "position": "right_foot"},
        ]

        # 尝试从实际资产中找到更多骨骼名
        skeleton_files = character.get("skeletons", [])
        if skeleton_files:
            # 实际项目中会解析 .uasset 获取完整骨骼列表
            pass

        return bones

    def _unity_bone_list(self) -> List[Dict[str, Any]]:
        """Unity 标准人形骨骼"""
        return [
            {"name": "Hips", "parent": None, "position": "root"},
            {"name": "Spine", "parent": "Hips", "position": "spine"},
            {"name": "Chest", "parent": "Spine", "position": "spine"},
            {"name": "Neck", "parent": "Chest", "position": "neck"},
            {"name": "Head", "parent": "Neck", "position": "head"},
            {"name": "LeftShoulder", "parent": "Chest", "position": "left_arm"},
            {"name": "LeftUpperArm", "parent": "LeftShoulder", "position": "left_upper_arm"},
            {"name": "LeftLowerArm", "parent": "LeftUpperArm", "position": "left_lower_arm"},
            {"name": "LeftHand", "parent": "LeftLowerArm", "position": "left_hand"},
            {"name": "RightShoulder", "parent": "Chest", "position": "right_arm"},
            {"name": "RightUpperArm", "parent": "RightShoulder", "position": "right_upper_arm"},
            {"name": "RightLowerArm", "parent": "RightUpperArm", "position": "right_lower_arm"},
            {"name": "RightHand", "parent": "RightLowerArm", "position": "right_hand"},
            {"name": "LeftUpperLeg", "parent": "Hips", "position": "left_leg"},
            {"name": "LeftLowerLeg", "parent": "LeftUpperLeg", "position": "left_lower_leg"},
            {"name": "LeftFoot", "parent": "LeftLowerLeg", "position": "left_foot"},
            {"name": "RightUpperLeg", "parent": "Hips", "position": "right_leg"},
            {"name": "RightLowerLeg", "parent": "RightUpperLeg", "position": "right_lower_leg"},
            {"name": "RightFoot", "parent": "RightLowerLeg", "position": "right_foot"},
        ]

    def _godot_bone_list(self) -> List[Dict[str, Any]]:
        """Godot 标准骨骼"""
        return [
            {"name": "Root", "parent": None, "position": "root"},
            {"name": "Hips", "parent": "Root", "position": "spine"},
            {"name": "Spine", "parent": "Hips", "position": "spine"},
            {"name": "Spine1", "parent": "Spine", "position": "spine"},
            {"name": "Neck", "parent": "Spine1", "position": "neck"},
            {"name": "Head", "parent": "Neck", "position": "head"},
            {"name": "LeftShoulder", "parent": "Spine1", "position": "left_arm"},
            {"name": "LeftArm", "parent": "LeftShoulder", "position": "left_upper_arm"},
            {"name": "LeftForeArm", "parent": "LeftArm", "position": "left_lower_arm"},
            {"name": "LeftHand", "parent": "LeftForeArm", "position": "left_hand"},
            {"name": "RightShoulder", "parent": "Spine1", "position": "right_arm"},
            {"name": "RightArm", "parent": "RightShoulder", "position": "right_upper_arm"},
            {"name": "RightForeArm", "parent": "RightArm", "position": "right_lower_arm"},
            {"name": "RightHand", "parent": "RightForeArm", "position": "right_hand"},
            {"name": "LeftUpLeg", "parent": "Hips", "position": "left_leg"},
            {"name": "LeftLeg", "parent": "LeftUpLeg", "position": "left_lower_leg"},
            {"name": "LeftFoot", "parent": "LeftLeg", "position": "left_foot"},
            {"name": "RightUpLeg", "parent": "Hips", "position": "right_leg"},
            {"name": "RightLeg", "parent": "RightUpLeg", "position": "right_lower_leg"},
            {"name": "RightFoot", "parent": "RightLeg", "position": "right_foot"},
        ]

    def _generic_bone_list(self) -> List[Dict[str, Any]]:
        """通用骨骼模板"""
        return self._ue4_bone_list({})

    def _generate_target_bone_list(self, source_engine: str) -> List[Dict[str, Any]]:
        """生成目标骨架（目前使用 UE4 标准骨架作为演示）"""
        # 实际项目中会根据目标游戏引擎生成对应骨架
        return self._ue4_bone_list({})

    def _match_bones(
        self,
        source_bones: List[Dict[str, Any]],
        target_bones: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        匹配源→目标骨骼映射

        策略：
        1. 精确名称匹配
        2. 位置语义匹配
        3. 拓扑结构匹配
        """
        mapping = []

        for src_bone in source_bones:
            src_name = src_bone["name"].lower()
            src_pos = src_bone.get("position", "")

            # 1. 精确匹配
            exact_match = None
            for tgt_bone in target_bones:
                if tgt_bone["name"].lower() == src_name:
                    exact_match = tgt_bone
                    break

            if exact_match:
                mapping.append({
                    "source_bone": src_bone["name"],
                    "target_bone": exact_match["name"],
                    "method": "exact",
                    "confidence": 1.0,
                })
                continue

            # 2. 位置语义匹配
            best_match = None
            best_score = 0.0

            for tgt_bone in target_bones:
                tgt_pos = tgt_bone.get("position", "")
                if src_pos and src_pos == tgt_pos:
                    # 计算名称相似度
                    similarity = self._name_similarity(src_name, tgt_bone["name"].lower())
                    score = 0.7 + 0.3 * similarity  # 位置匹配基础分 0.7
                    if score > best_score:
                        best_score = score
                        best_match = tgt_bone

            if best_match and best_score >= 0.5:
                mapping.append({
                    "source_bone": src_bone["name"],
                    "target_bone": best_match["name"],
                    "method": "semantic",
                    "confidence": round(best_score, 2),
                })
            else:
                mapping.append({
                    "source_bone": src_bone["name"],
                    "target_bone": None,
                    "method": "unmatched",
                    "confidence": 0.0,
                })

        return mapping

    def _name_similarity(self, name1: str, name2: str) -> float:
        """计算两个骨骼名称的相似度（简化 Levenshtein）"""
        if name1 == name2:
            return 1.0
        if name1 in name2 or name2 in name1:
            return 0.8

        # 简化的 Jaccard 相似度
        set1 = set(name1.replace("_", "").replace(" ", ""))
        set2 = set(name2.replace("_", "").replace(" ", ""))
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _calculate_confidence(self, mapping: List[Dict]) -> float:
        """计算整体映射置信度"""
        if not mapping:
            return 0.0
        confidences = [m.get("confidence", 0.0) for m in mapping]
        return sum(confidences) / len(confidences) if confidences else 0.0
