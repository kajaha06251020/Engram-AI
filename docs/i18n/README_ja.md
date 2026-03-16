<div align="center">

# Engram-AI

### AIエージェントのための経験駆動型メモリインフラストラクチャ

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)

**[English](../../README.md)** | **日本語** | **[中文](README_zh.md)** | **[한국어](README_ko.md)** | **[Español](README_es.md)**

---

*現在のAIメモリはテキストを保存します。Engram-AIは**傷跡（エングラム）**を作ります — エージェントが「何をして」「何が起きたか」から学ぶための因果構造です。*

</div>

## Engram-AIとは？

ほとんどのAIメモリシステムは**日記**のように機能します — テキストの事実を保存するだけです：*「ユーザーはPythonが好き」*、*「APIはRESTを使用」*。しかし、本当の学習は事実の暗記からは生まれません。**経験**から生まれるのです。

Engram-AIはAIエージェントに**経験的記憶**を与えます。エージェントが*知っていること*ではなく、*何をしたか*、*何が起きたか*、そして結果が*良かったか悪かったか*を保存します：

```
行動:     APIレスポンスフィールドにOptional[str]を使用
状況:     REST APIレスポンスモデルの設計
結果:     ユーザーが却下 — 「レスポンスにnull値は不要」
感情価:   -0.8（ネガティブな経験）
```

時間の経過とともに、これらの経験は**スキル**に結晶化します — 自身の履歴のパターンからエージェントが学んだ一般化されたルールです：

```
スキル:     「APIレスポンスモデルでOptional型を避ける」
信頼度:     0.85
根拠:       5つの経験（ネガティブ3、ポジティブ2）
```

そしてスキルはエージェントの設定に**進化**し、エージェントを永続的に改善します。

## クイックスタート

### インストール

```bash
pip install engram-ai
```

### Pythonライブラリとして

```python
from engram_ai import Forge

forge = Forge()

# 経験を記録
forge.record(
    action="リスト内包表記でデータ変換",
    context="1万行のCSV処理",
    outcome="高速で可読性も高く、ユーザー承認",
    valence=0.9,
)

# 過去の経験をクエリ
result = forge.query("データ変換のアプローチ")

# パターンをスキルに結晶化
skills = forge.crystallize()

# 学習したスキルでエージェント設定を進化
forge.evolve(config_path="./CLAUDE.md")
```

### Claude Code連携（推奨）

```bash
pip install engram-ai
engram-ai setup
# これだけ！自動で経験を記録し、学習を開始します
```

## コア操作

| 操作 | 説明 |
|------|------|
| **Record（記録）** | 経験を保存（行動 + 状況 + 結果 + 感情価） |
| **Query（検索）** | 関連する過去の経験を「ベスト」と「避けるべき」に分類して検索 |
| **Crystallize（結晶化）** | 類似経験をクラスタリングし、LLMでスキルパターンを抽出 |
| **Evolve（進化）** | 学習したスキルをエージェント設定（CLAUDE.md）に書き込み |

## コントリビュート

コントリビュートを歓迎します！[Contributing Guide](../../CONTRIBUTING.md)をご覧ください。

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## ライセンス

Apache License 2.0 — 詳細は[LICENSE](../../LICENSE)を参照。
