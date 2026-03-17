<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### AIエージェントのための経験駆動型メモリインフラ

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![codecov](https://img.shields.io/codecov/c/github/kajaha06251020/Engram-AI?style=flat-square)](https://codecov.io/gh/kajaha06251020/Engram-AI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=flat-square)](https://github.com/kajaha06251020/Engram-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/engram-ai)

**[English](../../README.md)** | **日本語** | **[中文](README_zh.md)** | **[한국어](README_ko.md)** | **[Español](README_es.md)**

---

*現在のAIメモリはテキストを保存します。Engram-AIは**傷跡**を作ります — エージェントが自分の行動と結果から学ぶことができる因果構造です。*

</div>

## Engram-AIとは？

多くのAIメモリシステムは**日記**のように機能します — テキストの事実を保存します：*「ユーザーはPythonを好む」*、*「APIはRESTを使用する」*。しかし、真の学習は事実の暗記からは生まれません。それは**経験**から生まれます。

Engram-AIはAIエージェントに**経験的メモリ**を与えます。エージェントが*知っている*ことを保存する代わりに、エージェントが*何をしたか*、*何が起きたか*、そして結果が*良かったか悪かったか*を保存します：

```
Action:   Used Optional[str] for API response field
Context:  Designing REST API response model
Outcome:  User rejected it — "no null values in responses"
Valence:  -0.8 (negative experience)
```

時間が経つにつれて、これらの経験は**結晶化**してスキルになります — エージェントが自身の履歴のパターンから学ぶ汎化されたルールです：

```
Skill:    "Avoid Optional types in API response models"
Confidence: 0.85
Evidence: 5 experiences (3 negative, 2 positive)
```

そしてスキルはエージェントの設定へと**進化**し、エージェントを恒久的に改善します：

```markdown
<!-- engram-ai:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-ai:end -->
```

## なぜEngram-AIなのか？

| 機能 | 従来のメモリ（Mem0など） | Engram-AI |
|------|------------------------|-----------|
| **保存するもの** | テキストの事実（「ユーザーはXが好き」） | 因果構造（行動 → 文脈 → 結果） |
| **学習方法** | 保存されたテキストの検索 | 経験からのパターン結晶化 |
| **学習シグナル** | なし | 経験ごとの感情価（-1.0〜+1.0） |
| **エージェントの改善** | 手動でのプロンプト調整 | 設定への自動スキル進化 |
| **メモリモデル** | 日記エントリー | ニューラルエングラム（経験による傷跡） |

## クイックスタート

### インストール

```bash
pip install engram-ai
```

### Pythonライブラリとして

```python
from engram_ai import Forge

forge = Forge()

# 経験を記録する
forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows",
    outcome="Fast and readable, user approved",
    valence=0.9,
)

# 過去の経験を照会する
result = forge.query("data transformation approach")
print(result["best"])   # ポジティブな経験
print(result["avoid"])  # ネガティブな経験

# パターンをスキルへと結晶化する
skills = forge.crystallize()

# 学習したスキルでエージェント設定を進化させる
forge.evolve(config_path="./CLAUDE.md")
```

### Claude Codeと共に（推奨）

自動経験記録を設定するワンコマンド：

```bash
# インストールと設定
pip install engram-ai
engram-ai setup

# これだけです！Engram-AIはこれにより：
# 1. フック経由で経験を記録します（PostToolUse, UserPromptSubmit）
# 2. MCPサーバー経由でツールを公開します（query, crystallize, evolve）
# 3. あなたの反応から結果の感情価を検出します（キーワード + LLM）
```

セットアップ後、Claude Codeエージェントは自動的に：
- すべてのツール使用を保留中の経験として**記録**します
- あなたの反応がポジティブかネガティブかを**検出**します
- 蓄積された経験からパターンを**学習**します
- 学習したスキルで自身のCLAUDE.mdを**進化**させます

## アーキテクチャ

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

**コア操作：**

| 操作 | 内容 |
|------|------|
| **Record** | 経験を保存する（行動 + 文脈 + 結果 + 感情価） |
| **Query** | 関連する過去の経験を検索し、「best」と「avoid」に分類する |
| **Crystallize** | 類似した経験をクラスタリングし、LLMでスキルパターンを抽出する |
| **Evolve** | 学習したスキルをエージェント設定（CLAUDE.md）に書き込む |

## CLIリファレンス

```bash
engram-ai setup          # Claude Code用に自動設定する
engram-ai status         # 経験/スキルの件数を表示する
engram-ai query "topic"  # 過去の経験を検索する
engram-ai crystallize    # 経験からスキルを抽出する
engram-ai evolve         # CLAUDE.mdにスキルを書き込む
engram-ai serve          # MCPサーバーを起動する
engram-ai dashboard      # Webダッシュボードを起動する（デフォルト: http://127.0.0.1:3333）
```

## MCPツール

MCPサーバーとして実行すると、Engram-AIは以下のツールを公開します：

| ツール | 説明 |
|--------|------|
| `engram_record` | 感情価付きで経験を記録する |
| `engram_query` | 過去の経験を検索する |
| `engram_crystallize` | パターンからスキルを抽出する |
| `engram_evolve` | 設定にスキルを書き込む |
| `engram_status` | 統計情報を表示する |

## 仕組み

### 二段階記録

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

### 感情価検出（段階的）

1. **キーワードマッチング**（無料）— 日本語・英語のポジティブ/ネガティブパターンを検出
2. **LLMフォールバック**（APIコール）— キーワードがマッチしない場合
3. **デフォルト0.3**— 両方が失敗した場合の軽度ポジティブ仮定

### 結晶化パイプライン

```
Experiences ──► Cluster by similarity ──► LLM extracts pattern ──► Skill
                (ChromaDB cosine)         (per cluster)            (rule + confidence)
```

## Webダッシュボード

Engram-AIには、経験・スキル・ニューラルグラフを可視化するためのリアルタイムWebダッシュボードが内蔵されています。

```bash
engram-ai dashboard --port 3333
```

**4つのページ：**

| ページ | 説明 |
|--------|------|
| **Overview（概要）** | 統計カード、感情価トレンドチャート、ミニニューラルグラフ、最近の経験 |
| **Experiences（経験）** | 行展開可能な検索・フィルタリング・ソート対応テーブル |
| **Skills（スキル）** | 信頼度バー付きカードグリッド、結晶化/進化アクションボタン |
| **Graph（グラフ）** | 六角形スキルノード付きフォースダイレクテッドニューラルグラフ、クリックでハイライト |

**機能：**
- WebSocketによるリアルタイム更新（新しい経験/スキルが即時表示）
- カスタムカラーパレットのダークテーマ
- 依存関係なしのサーブ（静的Next.jsエクスポートをパッケージにバンドル）
- ユーザー側でNode.jsは不要

## ロードマップ

Engram-AI v0.1は基盤となるバージョンです。このアーキテクチャは以下の計画中の機能をサポートします：

- [x] **Dashboard（ダッシュボード）** — 経験/スキル可視化のためのWeb UI
- [ ] **Emotion tagging（感情タグ付け）** — 感情価を超えた豊かな情動表現
- [ ] **Experience chains（経験チェーン）** — 関連する経験のリンクされたシーケンス
- [ ] **Forgetting curves（忘却曲線）** — 時間重み付き関連度の減衰
- [ ] **Skill marketplace（スキルマーケットプレイス）** — エージェント間での学習スキルの共有
- [ ] **Cross-agent transfer（クロスエージェント転送）** — エージェントインスタンス間の転移学習
- [ ] **Multi-LLM support（マルチLLMサポート）** — OpenAI、ローカルモデルなど
- [ ] **Reward shaping policies（報酬形成ポリシー）** — カスタム感情価戦略
- [ ] **Hierarchical memory（階層的メモリ）** — エピソード → スキル → メタスキル層
- [ ] **Privacy controls（プライバシー制御）** — 選択的メモリ、ユーザー制御による削除

計画中の全20機能については[詳細ロードマップ](../specs/2026-03-17-engram-ai-v0.1-design.md)をご覧ください。

## コントリビューション

あらゆる方からのコントリビューションを歓迎します！詳細は[コントリビューションガイド](../../CONTRIBUTING.md)をご覧ください。

**コントリビューターのためのクイックスタート：**

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest
```

始めやすい[good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)をチェックしてみてください！

## コミュニティ

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — 質問、アイデア、作ったものの紹介
- [Discord](https://discord.gg/engram-ai) — リアルタイムチャット
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — バグ報告と機能リクエスト

## スター履歴

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=kajaha06251020/Engram-AI&type=Date)](https://star-history.com/#kajaha06251020/Engram-AI&Date)

</div>

## ライセンス

Apache License 2.0 — 詳細は[LICENSE](../../LICENSE)をご覧ください。

---

<div align="center">

**Engram-AIがあなたのAIエージェントの経験学習に役立てば、ぜひスターをお願いします！**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
