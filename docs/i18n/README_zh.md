<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### 面向 AI 智能体的经验驱动记忆基础设施

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![codecov](https://img.shields.io/codecov/c/github/kajaha06251020/Engram-AI?style=flat-square)](https://codecov.io/gh/kajaha06251020/Engram-AI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=flat-square)](https://github.com/kajaha06251020/Engram-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/hGAcEfKqgq)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **中文** | **[한국어](README_ko.md)** | **[Español](README_es.md)**

---

*当前的 AI 记忆系统只会存储文本。Engram-AI 创造的是**印记**——因果结构，让智能体从自身的行为与结果中真正学习。*

</div>

## Engram-AI 是什么？

大多数 AI 记忆系统的工作方式就像一本**日记**——它们存储文本事实：*"用户偏好 Python"*、*"API 使用 REST"*。但真正的学习并非来自记忆事实，而是来自**经验**。

Engram-AI 为 AI 智能体提供**经验式记忆**。它存储的不是智能体*知道*什么，而是智能体*做了*什么、*发生了*什么，以及结果是*好是坏*：

```
Action:   Used Optional[str] for API response field
Context:  Designing REST API response model
Outcome:  User rejected it — "no null values in responses"
Valence:  -0.8 (negative experience)
```

随着时间推移，这些经验会**结晶**为技能——智能体从自身历史的规律中提炼出来的通用规则：

```
Skill:    "Avoid Optional types in API response models"
Confidence: 0.85
Evidence: 5 experiences (3 negative, 2 positive)
```

随后，技能会**演化**进入智能体的配置，使智能体持久地变得更好：

```markdown
<!-- engram-ai:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-ai:end -->
```

## 为什么选择 Engram-AI？

| 特性 | 传统记忆系统（Mem0 等） | Engram-AI |
|------|------------------------|-----------|
| **存储内容** | 文本事实（"用户喜欢 X"） | 因果结构（行为 → 上下文 → 结果） |
| **学习方式** | 检索已存储的文本 | 从经验中提炼规律 |
| **学习信号** | 无 | 每条经验的效价（-1.0 至 +1.0） |
| **智能体改进** | 手动调整提示词 | 自动将技能演化进配置文件 |
| **记忆模型** | 日记条目 | 神经印记（经验留下的痕迹） |

## 快速开始

### 安装

```bash
pip install engram-ai
```

### 作为 Python 库使用

```python
from engram_ai import Forge

forge = Forge()

# Record an experience
forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows",
    outcome="Fast and readable, user approved",
    valence=0.9,
)

# Query past experiences
result = forge.query("data transformation approach")
print(result["best"])   # 正面经验
print(result["avoid"])  # 负面经验

# Crystallize patterns into skills
skills = forge.crystallize()

# Evolve agent config with learned skills
forge.evolve(config_path="./CLAUDE.md")
```

### 与 Claude Code 配合使用（推荐）

一条命令即可完成自动经验记录的配置：

```bash
# Install and configure
pip install engram-ai
engram-ai setup

# That's it! Engram-AI now:
# 1. Records experiences via hooks (PostToolUse, UserPromptSubmit)
# 2. Exposes tools via MCP server (query, crystallize, evolve)
# 3. Detects outcome valence from your reactions (keyword + LLM)
```

完成配置后，你的 Claude Code 智能体会自动：
- **记录** 每次工具使用作为待处理经验
- **检测** 你的回应是正面还是负面
- **学习** 从积累的经验中提炼规律
- **演化** 自身的 CLAUDE.md，写入习得技能

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    Forge (Facade)                     │
├──────────┬──────────┬──────────────┬────────────────┤
│ Recorder │ Querier  │ Crystallizer │    Evolver     │
├──────────┴──────────┴──────────────┴────────────────┤
│                    EventBus                          │
├─────────────────┬───────────────────────────────────┤
│  Storage Layer  │          LLM Layer                │
│  (ChromaDB)     │     (Claude API)                  │
├─────────────────┴───────────────────────────────────┤
│              Adapters (Claude Code)                  │
└─────────────────────────────────────────────────────┘
```

**核心操作：**

| 操作 | 功能说明 |
|------|---------|
| **Record（记录）** | 存储一条经验（行为 + 上下文 + 结果 + 效价） |
| **Query（查询）** | 查找相关历史经验，分为"最佳"与"规避"两类 |
| **Crystallize（结晶）** | 聚类相似经验，通过 LLM 提取技能规律 |
| **Evolve（演化）** | 将习得技能写入智能体配置（CLAUDE.md） |

## CLI 参考

```bash
engram-ai setup          # Auto-configure for Claude Code
engram-ai status         # Show experience/skill counts
engram-ai query "topic"  # Search past experiences
engram-ai crystallize    # Extract skills from experiences
engram-ai evolve         # Write skills to CLAUDE.md
engram-ai serve          # Start MCP server
engram-ai dashboard      # Launch web dashboard (default: http://127.0.0.1:3333)
```

## MCP 工具

作为 MCP 服务器运行时，Engram-AI 暴露以下工具：

| 工具 | 说明 |
|------|------|
| `engram_record` | 记录一条带效价的经验 |
| `engram_query` | 搜索历史经验 |
| `engram_crystallize` | 从规律中提取技能 |
| `engram_evolve` | 将技能写入配置文件 |
| `engram_status` | 显示统计信息 |

## 工作原理

### 两阶段记录

```
PostToolUse Hook          UserPromptSubmit Hook
     │                           │
     ▼                           ▼
Record Pending ──────────► Complete with Valence
(action + context)         (outcome + valence detection)
     │                           │
     ▼                           ▼
pending.jsonl              ChromaDB Storage
```

### 效价检测（分级策略）

1. **关键词匹配**（免费）——检测日语与英语中的正负面模式
2. **LLM 回退**（调用 API）——关键词未匹配时使用
3. **默认 0.3**——两者均失败时采用的温和正面假设

### 结晶流水线

```
Experiences ──► Cluster by similarity ──► LLM extracts pattern ──► Skill
                (ChromaDB cosine)         (per cluster)            (rule + confidence)
```

## Web 看板

Engram-AI 内置实时 Web 看板，用于可视化经验、技能与神经图谱。

```bash
engram-ai dashboard --port 3333
```

**共 4 个页面：**

| 页面 | 说明 |
|------|------|
| **概览** | 统计卡片、效价趋势图、迷你神经图谱、最近经验 |
| **经验** | 可搜索、可筛选、可排序的表格，行可展开查看详情 |
| **技能** | 带置信度进度条的卡片网格，支持结晶与演化操作按钮 |
| **图谱** | 力导向神经图谱，技能节点为六边形，点击可高亮关联 |

**功能特性：**
- 通过 WebSocket 实时更新（新经验与技能即时显示）
- 深色主题，配备自定义调色板
- 零依赖服务（静态 Next.js 导出，随包一起分发）
- 用户无需安装 Node.js

## 路线图

Engram-AI v0.1 是基础版本，其架构支持以下计划功能：

- [x] **看板** — 经验与技能可视化 Web 界面
- [ ] **情感标注** — 超越效价的更丰富情感描述
- [ ] **经验链** — 相关经验的链式序列
- [ ] **遗忘曲线** — 基于时间权重的相关性衰减
- [ ] **技能市场** — 在不同智能体间共享习得技能
- [ ] **跨智能体迁移** — 智能体实例间的迁移学习
- [ ] **多 LLM 支持** — OpenAI、本地模型等
- [ ] **奖励塑造策略** — 自定义效价策略
- [ ] **分层记忆** — 情节 → 技能 → 元技能层级
- [ ] **隐私控制** — 选择性记忆，用户可控删除

完整规划请参见[完整路线图](../specs/2026-03-17-engram-ai-v0.1-design.md)（共 20 项计划功能）。

## 贡献

我们欢迎所有人参与贡献！详情请参阅[贡献指南](../../CONTRIBUTING.md)。

**贡献者快速开始：**

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest
```

欢迎查看我们的 [good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 入门参与！

## 社区

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — 提问、分享想法、展示成果
- [Discord](https://discord.gg/hGAcEfKqgq) — 实时聊天
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — 报告 Bug 与功能请求

## Star 历史

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=kajaha06251020/Engram-AI&type=Date)](https://star-history.com/#kajaha06251020/Engram-AI&Date)

</div>

## 许可证

Apache License 2.0 — 详情请参阅 [LICENSE](../../LICENSE)。

---

<div align="center">

**如果 Engram-AI 帮助你的 AI 智能体从经验中学习，请给它一颗 Star！**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
