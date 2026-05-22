# Chimera 架构设计文档

> AI 跨游戏角色与资产融合迁移引擎 — 技术架构详解

---

## 1. 设计哲学

### 1.1 核心命题

**输入：** 任意两款游戏（可同引擎、可跨引擎）
**输出：** 源游戏中的角色完整出现在目标游戏中

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **游戏不可知论** | 不绑定任何特定游戏或引擎 |
| **管道化** | 每个 Agent 是独立、可替换的处理单元 |
| **知识积累** | 每次迁移都在丰富知识库，越用越聪明 |
| **安全第一** | 注入前必须备份，支持完整回滚 |
| **渐进式复杂度** | 同引擎先通，再跨引擎 |

---

## 2. 系统架构

### 2.1 分层视图

```
┌─────────────────────────────────────────────────┐
│                    CLI / API 层                   │
│  chimera serve | migrate | fingerprint | doctor  │
├─────────────────────────────────────────────────┤
│                  Orchestrator                     │
│         DAG 编排 · ContextBus · 状态机            │
├──────────┬──────────┬──────────┬────────────────┤
│ Agent 1  │ Agent 2  │ Agent 3  │ Agent 4-5      │
│ 源解构   │ 资产提取  │ 骨架分析  │ 动画+格式(并行)│
├──────────┼──────────┼──────────┼────────────────┤
│ Agent 6  │ Agent 7  │ Agent 8  │                │
│ 目标注入  │ 运行时验证│ 编曲家   │                │
├──────────┴──────────┴──────────┴────────────────┤
│               Knowledge Base                     │
│     引擎映射 · 骨骼对应 · 迁移日志                │
├─────────────────────────────────────────────────┤
│              Core Engine                         │
│    DAG Engine · Config · Fingerprint · Tools     │
└─────────────────────────────────────────────────┘
```

### 2.2 DAG 流水线拓扑

```
                    [SourceDeconstructor]
                            │
                    [AssetExtractor]
                            │
                    [SkeletonAnalyzer]
                            │
              ┌─────────────┴─────────────┐
              │                           │
      [AnimRetargeter]           [FormatTranslator]
              │                           │
              └─────────────┬─────────────┘
                            │
                    [TargetInjector]
                            │
                    [RuntimeValidator]
```

**层级关系：**
- 第1层：源解构（1 Agent）
- 第2层：资产提取（1 Agent，依赖第1层）
- 第3层：骨架分析（1 Agent，依赖第2层）
- 第4层：动画重定向 + 格式转换（2 Agent 并行，依赖第3层）
- 第5层：目标注入（1 Agent，依赖第4层全部）
- 第6层：运行时验证（1 Agent，依赖第5层）

---

## 3. Agent 详解

### 3.1 SourceDeconstructor（源解构师）

**输入：** 游戏根目录路径
**输出：** 引擎指纹 + 资产结构 + 角色列表

**工作流：**
1. 引擎指纹识别（多维度投票）
2. 资产目录扫描（按类型分类）
3. 角色资源定位（引擎特定搜索策略）
4. 加密方案检测

**支持的引擎特征：**
- UE4/5: `.uasset`/`.uexp` + PAK magic `5A6F12E1`
- RE Engine: `KPKA` PAK magic
- Godot: `GDPC` PCK magic
- Unity: `UnityFS` + `Assembly-CSharp`
- Source 2: `VBKV` + LZMA

### 3.2 AssetExtractor（角色提取师）

**输入：** 引擎类型 + 角色路径列表
**输出：** 结构化资产清单

**引擎特定提取策略：**
- **UE4/5:** 搜索 `SK_*.uasset` (网格)、`*_Skeleton.uasset` (骨架)、`*_AnimBP*.uasset` (动画)、`T_*.uasset` (纹理)
- **Unity:** 搜索 `*.prefab`、`*.mesh`
- **Godot:** 搜索 `*.tscn`、`*.res`
- **RE Engine:** 目录级扫描

### 3.3 SkeletonAnalyzer（骨架分析师）

**输入：** 源角色骨骼 + 目标骨架模板
**输出：** 骨骼映射表（源→目标）

**三重匹配算法：**
1. **精确名称匹配** — 直接字符串比对
2. **语义位置匹配** — 基于 BONE_PATTERNS 字典
3. **拓扑结构匹配** — 基于父子关系

**置信度计算：**
```
confidence = Σ(match_confidence) / total_bones
```

### 3.4 AnimRetargeter（动画重定向师）

**4 种重定向策略（自动选择）：**

| 策略 | 触发条件 | 质量 |
|------|---------|------|
| DIRECT | 100% 精确匹配 | 95% |
| PROPORTIONAL | 置信度 ≥ 80% | 85% |
| IK_BASED | 置信度 ≥ 50% | 75% |
| AI_GUIDED | 置信度 < 50% | 65% |

### 3.5 FormatTranslator（格式转换师）

**25 条格式互译路径（5×5 引擎矩阵）：**

| 源\目标 | UE4 | Unity | Godot | RE | S2 |
|---------|-----|-------|-------|----|----|
| UE4 | 直接 | FBX | glTF | FBX→RE | — |
| Unity | FBX | 直接 | glTF | — | — |
| Godot | glTF | glTF | 直接 | — | — |
| RE | RE→FBX | — | — | 直接 | — |
| S2 | — | — | — | — | 直接 |

**材质通道映射：**
- UE4: BaseColor / Normal / Roughness / Metallic
- Unity: _BaseMap / _BumpMap / _Smoothness / _MetallicGlossMap
- Godot: albedo_texture / normal_texture / roughness_texture / metallic_texture

### 3.6 TargetInjector（目标注入师）

**注入方式（引擎自适应）：**
- UE4/5: LogicMods 目录 → PAK 封包
- Unity: BepInEx 插件
- Godot: Cecil IL 织入
- RE Engine: Fluffy Mod Manager

**安全保障：**
- 注入前自动备份到 `.chimera_backup/`
- 支持一键回滚

### 3.7 RuntimeValidator（运行时验证官）

**5 维质量检查：**
1. 模型完整性（网格/材质/LOD）
2. 动画正确性（流畅度/破面检测）
3. 纹理质量（分辨率/通道正确性）
4. 碰撞检测（物理资产）
5. 性能基准（FPS/内存/加载时间）

---

## 4. 核心技术组件

### 4.1 DAG Engine

- **算法：** Kahn 拓扑排序
- **并行度：** 同层节点自动并行（最高4）
- **容错：** 指数退避重试 + 超时熔断
- **通信：** ContextBus 发布/订阅

### 4.2 Engine Fingerprinter

- **方法：** 多维度投票（魔数 + 扩展名 + 已知数据库）
- **置信度：** 0.0 ~ 1.0，综合评分

### 4.3 Knowledge Base

- **引擎映射：** 25 条格式转换路径
- **骨骼映射：** JSONL 持久化 + 渐进积累
- **迁移日志：** 每次迁移的完整记录

---

## 5. 数据流

```
游戏文件 → [Fingerprint] → 引擎类型
                ↓
         [Extractor] → 资产清单 (JSON)
                ↓
         [SkeletonAnalyzer] → 骨骼映射 (dict)
                ↓
    ┌───────┴────────┐
    ↓                ↓
[Retargeter]    [FormatTranslator]
动画数据         格式转换方案
    ↓                ↓
    └───────┬────────┘
            ↓
     [Injector] → 注入后的游戏文件
            ↓
     [Validator] → 质量报告 (dict)
            ↓
     [KnowledgeBase] → 迁移日志
```

---

## 6. 部署架构

### 开发模式

```bash
python3 cli.py serve --reload
```

### 生产模式

```bash
# Systemd
sudo systemctl start chimera

# Docker
docker-compose -f docker/docker-compose.yml up -d

# 裸进程
nohup python3 -m uvicorn api.server:app --host 0.0.0.0 --port 8004 &
```

### 反向代理

```
Nginx (80) → Chimera API (8004)
```

---

## 7. 安全考量

| 关注点 | 措施 |
|--------|------|
| 文件安全 | 注入前备份到 `.chimera_backup/` |
| 回滚能力 | `POST /api/v1/rollback` 一键恢复 |
| 资源隔离 | 只读挂载游戏库，写操作限制在项目目录 |
| 日志审计 | 所有迁移操作记录到 JSONL |
| 进程安全 | systemd/Docker 资源限制 |

---

## 8. 性能基准

| 场景 | 时间 | Token |
|------|------|-------|
| 同引擎迁移 (UE4→UE4) | 5-15 min | ~600万 |
| 近亲引擎 (UE4→Unity) | 30-45 min | ~1200万 |
| 远亲引擎 (RE→UE4) | 50-70 min | ~1800万 |
| 全流水线（含AI推理） | 10-60 min | 800-2000万 |

---

## 9. 扩展性

### 添加新引擎

1. 在 `config.py` 注册 `EngineProfile`
2. 在 `CONVERSION_PATHS` 添加格式转换路径
3. 在 `MATERIAL_CHANNEL_MAP` 添加材质映射
4. 在 `Fingerprinter` 添加魔数检测
5. 在 `Injector` 添加注入策略

### 添加新 Agent

1. 创建 `agents/new_agent.py`
2. 在 `orchestrator._setup_dag()` 注册节点和依赖
3. 在 `api/server.py` 添加对应端点
4. 在 `tests/test_core.py` 添加测试

---

> 🦁🐐🐍 *Chimera 的架构如同它的名字——多个引擎、多种格式、多重策略融合成一个强大的迁移引擎。*
