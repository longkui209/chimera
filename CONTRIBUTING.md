# 贡献指南

感谢你对 Chimera 的关注！以下是参与开发的指南。

## 代码风格

- **Python**: 遵循 PEP 8，最大行宽 120 字符
- **Shell**: 遵循 Google Shell Style Guide
- **注释**: 中文注释优先，关键 API 使用英文
- **类型标注**: 所有公共函数必须有类型标注

## 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 编写代码和测试
4. 运行测试确保通过 (`make test`)
5. 提交 (`git commit -m 'feat: add amazing feature'`)
6. 推送 (`git push origin feature/amazing-feature`)
7. 创建 Pull Request

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具链
perf: 性能优化
```

示例：
```
feat: 添加 Source 2 引擎支持
fix: 修复 UE4 PAK v11 解析错误
docs: 更新 API 端点文档
test: 增加骨架分析器边界测试
```

## 添加新引擎

1. **注册引擎档案** (`core/config.py`):
```python
"new_engine": EngineProfile(
    name="new_engine",
    display_name="New Engine",
    magic_bytes=[b"MAGIC"],
    file_extensions=[".ext1", ".ext2"],
    injection_methods=["method1", "method2"],
    ...
)
```

2. **添加指纹识别** (`core/engine_fingerprint.py`):
- 在 `_scan_magic_bytes()` 添加魔数检测
- 在 `_score_candidates()` 添加评分逻辑

3. **添加格式转换** (`agents/format_translator.py`):
- 在 `CONVERSION_PATHS` 添加与现有引擎的转换路径
- 在 `MATERIAL_CHANNEL_MAP` 添加材质通道映射

4. **添加注入方式** (`agents/target_injector.py`):
- 在 `_select_method()` 添加引擎→注入方式映射
- 实现 `_inject_assets()` 中的新注入逻辑

5. **更新测试** (`tests/test_core.py`):
```python
def test_new_engine(self):
    profile = Config.ENGINES["new_engine"]
    assert profile.display_name == "New Engine"
```

## 添加新 Agent

1. 创建 `agents/new_agent.py`:
```python
class NewAgent:
    def execute(self, context):
        # Agent 逻辑
        return {"result": "..."}
```

2. 在 DAG 注册 (`agents/orchestrator.py`):
```python
dag.add_node(
    "new_agent",
    new_agent.execute,
    depends_on=["upstream_agent"],
)
```

3. 添加 API 端点 (`api/server.py`):
```python
@app.post("/api/v1/new_endpoint")
async def new_endpoint(req: Request):
    ...
```

4. 添加测试:
```python
class TestNewAgent:
    def test_execute(self):
        ...
```

## 测试要求

- 新功能必须有测试覆盖
- 测试文件命名: `test_*.py`
- 运行: `make test` 或 `pytest tests/ -v`
- CI 会自动运行 lint + test + docker build

## 文档要求

- 新功能更新 `README.md`
- 架构变更更新 `docs/ARCHITECTURE.md`
- API 变更更新 API 文档注释
- CLI 变更更新帮助文本

## 代码审查清单

- [ ] 代码风格符合规范
- [ ] 所有函数有类型标注
- [ ] 新增测试通过
- [ ] 文档已更新
- [ ] 没有引入新的 warning
- [ ] 兼容 Python 3.8+
- [ ] 中文注释清晰

## 社区

- **Issues**: 报告 bug 或提出功能建议
- **Discussions**: 技术讨论和 Q&A
- **Pull Requests**: 欢迎贡献！

## 行为准则

- 尊重所有贡献者
- 建设性反馈
- 聚焦技术，不人身攻击
- 帮助新手融入

---

> 🦁🐐🐍 *Chimera 的成长离不开每一位贡献者。让我们一起打破游戏之间的壁垒。*
