# 仿生大脑 · Hermes 插件

把 [BioBrain](https://github.com/Satyr-Astry/biobrain) 仿生认知架构接入 Hermes Desktop —— 提供 **7 个大脑工具** + 右侧实时状态面板。

> **铁律**：大脑**独立运行**，绝不替换 Hermes 主会话 model（防止挤爆显存卡死网关）。

## 工具

| 工具 | emoji | 说明 |
|------|-------|------|
| `brain_ask` | 🧠 | ★ 向大脑提问：检索神经记忆 → 语言区表达 |
| `brain_distill` | 📚 | ★ 自主蒸馏：生成大纲 → 逐点学习 → 自检 → 入库 |
| `brain_recall` | 🔍 | 检索记忆，看它知道什么 |
| `brain_teach` | ✍️ | 直接教一条问答对 |
| `brain_think` | 💭 | 纯思考流（激活扩散，不调语言区） |
| `brain_sleep` | 😴 | 睡眠巩固（合并可塑量、修剪弱连接） |
| `brain_state` | 📊 | 大脑状态（神经元 / 激活 / 记忆 / 语言区） |

## 桌面面板

右侧面板显示实时状态：神经组织（神经元 / 神经束 / 神经组 / 激活 / ticks）、分级驻留、自我认知（擅长 / 不擅长 / 成功率）、学习状态（经验缓冲 / REM 候选 / 集体层 / 新生神经元 / 鲁棒等级），并提供**思考 / 睡眠巩固 / 刷新**按钮。

## 安装

1. 把 `bio-brain/` 放进 Hermes 插件目录：

   ```
   $HERMES_HOME/plugins/bio-brain/
   ├── plugin.yaml
   ├── __init__.py
   ├── tools.py
   └── desktop/plugin.js
   ```

2. 把插件指向你的大脑代码，解析顺序（命中即止）：

   | # | 来源 | 示例 |
   |---|------|------|
   | 1 | 环境变量 `BIOBRAIN_PATH`（或 `HERMES_BIOBRAIN_PATH`） | `BIOBRAIN_PATH=E:\BIONIC_AI\code` |
   | 2 | 插件目录内的 `brain/` 子目录 | 自带大脑 |
   | 3 | `config.yaml` 的 `plugins.bio-brain.brain_path` | 见下 |

   ```yaml
   # $HERMES_HOME/config.yaml
   plugins:
     bio-brain:
       brain_path: "E:\\BIONIC_AI\\code"
   ```

   判定条件是该目录下存在 `conductor.py`。**仓库内不含任何硬编码本机路径**，未配置时干净返回错误而非崩溃。

3. 重启 Hermes 网关 / 桌面端，在 `config.yaml` 的 `plugins.enabled` 中启用 `bio-brain`。

## 依赖

大脑本体只需 `numpy`；`brain_distill` 需要可用的 LLM 语言区（由大脑自身的配置决定）。

## 说明

- 大脑加载为**懒加载 + 单例**，避免重复构建。
- 记忆落盘在 `<大脑目录>/agent_memory.json`，`brain_teach` / `brain_distill` / `brain_sleep` 后自动写回。
- `_NEURONS` 默认 8192（16K 单次对话约需 30s，插件用 8K 更跟手）。

## License

**MIT** —— 适用于本插件仓库（`plugin.yaml` / `tools.py` / `desktop/plugin.js` / 文档）。

> 本插件**不含**仿生大脑本体的代码。大脑代码是独立项目，采用另一套许可证：
> **[BioBrain](https://github.com/Satyr-Astry/biobrain) · CCSAL-1.0（慈善条款源可用许可证）**。
> 使用本插件时请遵守各项目各自的许可证；若把大脑代码与本插件一起分发，需同时满足 CCSAL-1.0 与 MIT 的要求。
