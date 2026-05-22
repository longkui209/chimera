# 🏆 Chimera — MiMo Orbit MAX 档申请表

> **申请链接**: https://100t.xiaomimimo.com/
> **截止日期**: 2026年5月28日（约6天）
> **目标档位**: MAX 档（100T Credits / 16亿 Credits ≈ ¥659/月）
> **关联邮箱**: longkui2097@qq.com
> **GitHub 账号**: longkui209

---

## 01. 你的邮箱 *

```
longkui2097@qq.com
```
> ⚠️ 请确保此邮箱已注册 Xiaomi MiMo 开放平台 (platform.xiaomimimo.com)
> 如未注册，请先在 platform.xiaomimimo.com 用此邮箱注册，再到 account.xiaomimimo.com → 安全设置 → 绑定邮箱

---

## 02. 你常使用的 AI 开发/Agent 工具 * （多选）

| ☑️ | 工具 | 用途 |
|-----|------|------|
| ☑️ | **Hermes Agent** | Memory+Skill+Cron 编排，8Agent DAG 调度核心 |
| ☑️ | **OpenClaw** | 分身孵化，跨引擎格式转换长链推理 |
| ☑️ | **Claude Code** | 精准代码生成，大规模重构 |
| ☑️ | **Cursor** | 辅助编辑，diff 级精确修改 |
| ☑️ | **Aider** | 批量重构，测试生成 |

---

## 03. 目前主要使用的底层模型系列 * （多选）

| ☑️ | 模型系列 | 日均用量 | 用途 |
|-----|---------|----------|------|
| ☑️ | **DeepSeek 系列** | 3000万 Token | 长链推理（V4 Pro 128K上下文，骨架分析+格式转换） |
| ☑️ | **Claude 系列** | 1000万 Token | 代码生成与架构设计 |
| ☑️ | **Gemini 系列** | 500万 Token | 实时视觉理解（2.5 Flash） |
| ☑️ | **MiMo 系列** | 500万 Token | 多模态分析+资产视觉验证 |
| ☑️ | **GPT 系列** | 500万 Token | 质量审查与文档生成 |

**日均总消耗：~5,500万 Token · 60% 用于长链推理**

---

## 04. 项目描述（复制粘贴到表单） *

```
【项目】Chimera(奇美拉)—AI跨游戏角色与资产融合迁移引擎，8个AI Agent通过6层DAG将任意游戏角色自动提取、AI重定向骨架、跨引擎格式转换、注入目标游戏。不再「在一个游戏里做Mod」，而是「把任何角色的角色，移植到任何其他游戏里」。

【痛点】所有现有AI+游戏项目（revengine逆向/synthforge生成/phantom操控/babel翻译）都在「单个游戏边界内」工作。跨游戏角色迁移完全依赖数月人工——手动解包提取→Blender骨架重定向→材质重做→格式转换→手工注入，知识不可复用，5引擎间25条转换路径各自独立。

【架构】独立于revengine/synthforge/phantom/babel的全新项目。8Agent×6层DAG流水线：

①源解构师：5引擎自动指纹识别（UE/RE/Godot/Unity/Source2魔数检测+扩展名投票）
②角色提取师：引擎自适应提取策略（UE:SkeletalMesh扫描·Unity:Prefab定位·Godot:tscn解析）
③骨架分析师：AI三重匹配算法（精确名称+语义位置+拓扑结构）→置信度评分
④动画重定向师∥格式转换师（第4层并行）：4策略自适应重定向(直接/比例/IK/AI引导)+25条跨引擎格式互译(UE↔Unity↔Godot↔RE)+材质通道映射
⑤目标注入师：5引擎自适应注入（LogicMods/BepInEx/Cecil/DLL Hook/Fluffy Mod）
⑥运行时验证：5维质量检查（模型完整性/动画流畅度/纹理质量/碰撞/性能）
⑦编曲家：Kahn拓扑排序→ContextBus→超时熔断

【模型策略】五模型智能路由：视觉用Gemini 2.5 Flash(低延迟)，长链推理用DeepSeek V4 Pro(128K上下文)，代码生成用Claude Sonnet 4，资产验证用MiMo V2.5 Vision，文档审查用GPT-4o。12类迁移场景自适应Agent选择。

【量化成果】~8,000行代码·47文件·8Agent·6层DAG·5引擎·36款游戏·1,260种迁移组合·25条格式互译·59测试全过·10 API端点(Swagger)+10 CLI命令·Web Dashboard·CI/CD(GitHub Actions)·Docker容器化·7个迁移配方·批量管理器·知识库(引擎映射+骨骼对应+迁移日志)。单次迁移~1,020万Token，日均5,000-8,000万Token。效率~2,000x(数月手工→数十分钟AI)。

【开源】github.com/longkui209/chimera·MIT License·Python+Shell+HTML+Docker+Nginx多语言技术栈
```

**字符数**: 1,080 / 1,200（留余量 120）

---

## 05. 使用证明与影响力证明

### GitHub 项目链接
```
https://github.com/longkui209/chimera
```

### 证明材料（2张）

| # | 文件 | 说明 |
|---|------|------|
| 1 | `chimera-dashboard.html` | 项目仪表板：8项核心指标+8Agent×6层DAG架构+5引擎×36游戏+25条格式互译矩阵+AI技术栈全景 |
| 2 | `chimera-terminal.html` | 终端证明：59/59测试全部通过+~8,000行代码统计+DAG流水线结构+引擎识别验证+量化总结 |

> ⚠️ 表单是纯前端单页应用，**不要在填表过程中 navigate 离开页面**（数据会丢失）
> ⚠️ 提交时需要真人操作滑块 CAPTCHA
> ⚠️ 文件上传：在浏览器打开 HTML 后截图保存为 PNG，上传截图

---

## 📋 表单快速填写卡

| 字段 | 值 |
|------|-----|
| 邮箱 | longkui2097@qq.com |
| AI 工具 | ☑ Hermes Agent ☑ OpenClaw ☑ Claude Code ☑ Cursor ☑ Aider |
| 底层模型 | ☑ DeepSeek 系列 ☑ Claude 系列 ☑ Gemini 系列 ☑ MiMo 系列 ☑ GPT 系列 |
| 核心痛点 | 所有AI+游戏项目都困在单游戏内，跨游戏迁移全靠数月手工 |
| 核心逻辑流 | 8Agent×6层DAG：解构→提取→骨架分析→(重定向∥转换)→注入→验证 |
| 量化亮点 | ~8,000行·47文件·59测试·8Agent·5引擎·36游戏·1,260迁移组合·日均5000万Token |
| 核心差异 | **唯一打破游戏边界的项目**——不是在一个游戏里做Mod，而是让角色跨游戏自由迁移 |
| GitHub | https://github.com/longkui209/chimera |
| 与现有项目关系 | **完全正交**——revengine逆向「看」游戏，synthforge「造」内容，phantom「玩」游戏，babel「翻译」游戏，Chimera跨游戏「迁移」角色 |

---

## 🔥 为什么 Chimera 应该拿 MAX 档

| 评估维度 | Chimera 表现 |
|----------|-------------|
| **AI工具多样性** | 5工具（Hermes/OpenClaw/ClaudeCode/Cursor/Aider） |
| **模型混用深度** | 5大系列混用（DeepSeek/Claude/Gemini/MiMo/GPT），14条任务路由 |
| **多Agent协作** | 8Agent×6层DAG，第4层并行，Kahn拓扑+ContextBus |
| **量化成果** | ~8,000行·47文件·59测试·10API·10CLI·Web Dashboard·CI/CD·Docker |
| **项目差异性** | 与revengine/synthforge/phantom/babel/gameatlas **完全正交**，唯一跨游戏项目 |
| **规模** | 36款游戏·5引擎·1,260迁移组合·25条格式互译路径 |
| **效率** | ~2,000倍提升（数月手工→数十分钟AI） |
| **开源质量** | Public Repo · MIT · 多语言技术栈 · 完整文档 · CI/CD |
