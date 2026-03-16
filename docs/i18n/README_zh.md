<div align="center">

# Engram-AI

### AI智能体的经验驱动记忆基础设施

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **中文** | **[한국어](README_ko.md)** | **[Español](README_es.md)**

---

*当前的AI记忆存储文本。Engram-AI创建**印记** — 让智能体从"做了什么"和"发生了什么"中学习的因果结构。*

</div>

## 什么是Engram-AI？

大多数AI记忆系统就像**日记** — 只存储文字事实：*"用户喜欢Python"*、*"API使用REST"*。但真正的学习不是来自记忆事实，而是来自**经验**。

Engram-AI赋予AI智能体**经验性记忆**。它不存储智能体*知道什么*，而是存储它*做了什么*、*发生了什么*，以及结果是*好还是坏*：

```
行为:     在API响应字段中使用Optional[str]
情境:     设计REST API响应模型
结果:     用户拒绝 — "响应中不要有null值"
效价:     -0.8（负面经验）
```

随着时间推移，这些经验会**结晶**成技能 — 智能体从自身历史模式中学到的通用规则：

```
技能:     "避免在API响应模型中使用Optional类型"
置信度:   0.85
证据:     5个经验（3个负面，2个正面）
```

## 快速开始

### 安装

```bash
pip install engram-ai
```

### 作为Python库使用

```python
from engram_ai import Forge

forge = Forge()

# 记录经验
forge.record(
    action="使用列表推导式进行数据转换",
    context="处理含1万行的CSV",
    outcome="快速且可读性高，用户认可",
    valence=0.9,
)

# 查询过去的经验
result = forge.query("数据转换方法")

# 将模式结晶为技能
skills = forge.crystallize()

# 用学到的技能进化智能体配置
forge.evolve(config_path="./CLAUDE.md")
```

### 与Claude Code集成（推荐）

```bash
pip install engram-ai
engram-ai setup
# 完成！现在会自动记录经验并开始学习
```

## 核心操作

| 操作 | 说明 |
|------|------|
| **Record（记录）** | 存储经验（行为 + 情境 + 结果 + 效价） |
| **Query（查询）** | 搜索相关的过去经验，分为"最佳"和"应避免" |
| **Crystallize（结晶）** | 聚类相似经验并通过LLM提取技能模式 |
| **Evolve（进化）** | 将学到的技能写入智能体配置（CLAUDE.md） |

## 贡献

我们欢迎所有人的贡献！请查看[贡献指南](../../CONTRIBUTING.md)。

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## 许可证

Apache License 2.0 — 详见[LICENSE](../../LICENSE)。
