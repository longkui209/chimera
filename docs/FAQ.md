# Chimera 常见问题

## Q: Chimera 支持哪些游戏？
A: 理论上支持所有 5 大引擎的游戏（UE4/5、RE Engine、Godot、Unity、Source 2）。目前已在 36 款商业游戏上验证架构可行性。

## Q: 迁移后的角色能正常游戏吗？
A: 同引擎迁移（如 UE4→UE4）质量最高，动画、材质、碰撞均可保持。跨引擎迁移（如 UE4→Unity）需要更复杂的格式转换，部分特性可能降级。

## Q: 迁移需要多长时间？
A: 同引擎 5-15 分钟，跨引擎 30-60 分钟。具体取决于游戏大小、骨架复杂度、AI 推理速度。

## Q: 迁移会修改原始游戏文件吗？
A: 会自动备份到 `.chimera_backup/` 目录。支持一键回滚。但不建议在生产环境直接操作。

## Q: 需要什么硬件配置？
A: 最低 8GB 内存 + 50GB 磁盘。推荐 16GB+ 内存。AI 推理消耗较多 Token，建议配合大模型 API 使用。

## Q: 如何添加新的游戏支持？
A: 在 `core/config.py` 的 `KNOWN_GAMES` 中注册即可。引擎会自动识别。

## Q: 如何添加新的引擎支持？
A: 参见 `CONTRIBUTING.md` 中的「添加新引擎」章节。需要实现指纹识别、格式转换、注入策略三步。

## Q: Chimera 和 ReVEngine 的区别？
A: ReVEngine 在单个游戏内逆向分析做 Mod。Chimera 跨游戏迁移角色。两者互补：ReVEngine 提供提取能力，Chimera 提供迁移能力。

## Q: 可以批量迁移吗？
A: 支持。使用 `BatchManager` 或 `config/recipes.json` 定义配方后批量执行。

## Q: 如何贡献代码？
A: Fork → 创建分支 → 编写代码+测试 → PR。详见 `CONTRIBUTING.md`。

## Q: 迁移角色的版权问题？
A: Chimera 是技术工具。用户应确保迁移操作符合相关游戏的 EULA 和当地法律。本项目仅用于技术研究和教育目的。

## Q: 支持 macOS / Windows 吗？
A: Chimera 核心是跨平台的 Python 项目。工具链部分依赖 Linux 生态（Wine/umodel），macOS/Windows 可通过 Docker 运行。

## Q: 如何查看实时日志？
A: API 模式: `tail -f logs/chimera.log`。CLI 模式: 日志输出到终端。Docker 模式: `docker logs -f chimera-engine`。
