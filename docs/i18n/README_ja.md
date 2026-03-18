<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### AIエージェントのための経験駆動型メモリインフラ

[![PyPI version](https://img.shields.io/pypi/v/engram-forge?style=flat-square&color=blue)](https://pypi.org/project/engram-forge/)
[![Python](https://img.shields.io/pypi/pyversions/engram-forge?style=flat-square)](https://pypi.org/project/engram-forge/)
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

---

## 目次

- [Engram-AIとは？](#engram-aiとは)
- [なぜEngram-AI？](#なぜengram-ai)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [サンプルプログラム](#サンプルプログラム)
- [API リファレンス](#api-リファレンス)
- [CLIリファレンス](#cliリファレンス)
- [MCPサーバー](#mcpサーバー)
- [APIキーなしで使う](#apiキーなしで使う)
- [マルチプロジェクト対応](#マルチプロジェクト対応)
- [アーキテクチャ](#アーキテクチャ)
- [Webダッシュボード](#webダッシュボード)
- [ロードマップ](#ロードマップ)

---

## Engram-AIとは？

多くのAIメモリシステムは**日記**のように機能します — テキストの事実を保存します：*「ユーザーはPythonを好む」*、*「APIはRESTを使用する」*。しかし、真の学習は事実の暗記からは生まれません。それは**経験**から生まれます。

Engram-AIはAIエージェントに**経験的メモリ**を与えます。エージェントが*知っている*ことを保存する代わりに、エージェントが*何をしたか*、*何が起きたか*、そして結果が*良かったか悪かったか*を保存します：

```
Action:   Optional[str]をAPIレスポンスフィールドに使った
Context:  REST APIレスポンスモデルの設計
Outcome:  ユーザーに却下された — "レスポンスにnullは不要"
Valence:  -0.8  ← ネガティブな経験
```

時間が経つにつれて、経験は**結晶化**してスキルになります — パターンから抽出した汎化ルールです：

```
Skill:      "APIレスポンスモデルでOptional型は避ける"
Confidence: 0.85
Evidence:   5件の経験 (ネガティブ4件、ポジティブ1件)
```

そしてスキルはエージェントの設定へと**進化**し、恒久的に改善します：

```markdown
<!-- engram-forge:start -->
## Engram-AI: 学習済みスキル
- APIレスポンスモデルでOptional型は避ける (confidence: 0.85)
- テストファイルでは説明的な変数名を使う (confidence: 0.92)
<!-- engram-forge:end -->
```

---

## なぜEngram-AI？

| 機能 | 従来のメモリ (Mem0 など) | Engram-AI |
|------|----------------------|-----------|
| **保存するもの** | テキストの事実 ("ユーザーはXが好き") | 因果構造 (行動 → 文脈 → 結果) |
| **学習方法** | 保存テキストの検索 | 経験からのパターン結晶化 |
| **学習信号** | なし | 経験ごとのValence (−1.0〜+1.0) |
| **エージェントの改善** | 手動プロンプト調整 | スキルの自動進化・設定反映 |
| **メモリモデル** | 日記エントリ | ニューラルエングラム (経験の傷跡) |
| **APIキー必須** | 通常は必要 | 不要 — コア機能はAPIキーなしで動作 |

---

## インストール

用途に合わせてextrasを選択してください：

| コマンド | 追加されるもの | 用途 |
|---------|-------------|------|
| `pip install engram-forge` | コア (ChromaDB + CLI) | LLMなしでアプリに組み込む |
| `pip install "engram-forge[claude]"` | + Anthropic SDK | LLMによる結晶化・感情検知 |
| `pip install "engram-forge[mcp]"` | + MCPサーバー | Claude Code / MCPクライアント統合 |
| `pip install "engram-forge[dashboard]"` | + FastAPI + Uvicorn | Web可視化UI |
| `pip install "engram-forge[full]"` | 上記すべて | ほとんどのユーザーに推奨 |
| `pip install "engram-forge[full,dev]"` | + pytest, ruff | 開発用 |

---

## クイックスタート

### Option A — Claude Codeと連携（設定不要）

```bash
pip install "engram-forge[full]"
engram-forge setup        # ~/.claude/settings.json にMCP設定とフックを書き込む
```

Claude Codeを再起動するだけで完了。Engram-AIが自動的に：

1. **記録** — すべてのツール使用をpending経験として記録 (PostToolUseフック)
2. **検知** — あなたのレスポンスがポジティブかネガティブかを判定 (UserPromptSubmitフック)
3. **結晶化** — セッションごとにパターンをスキルに変換
4. **進化** — CLAUDE.mdを学習済みルールで自動更新

### Option B — Pythonライブラリとして使う

```python
from engram_ai import Forge

# デフォルト: ChromaDB は ~/.engram-ai/data、LLMはANTHROPIC_API_KEY環境変数から
forge = Forge()

# 経験を記録
exp = forge.record(
    action="リスト内包表記でデータ変換を実装した",
    context="10万行のCSVをpandasパイプラインで処理",
    outcome="高速かつ可読性が高く、ユーザーに承認された",
    valence=0.9,
)

# 過去の経験を検索
result = forge.query("データ変換のアプローチ")
for exp, score in result["best"]:
    print(f"  推奨 [{score:.2f}]: {exp.action}")
for exp, score in result["avoid"]:
    print(f"  回避 [{score:.2f}]: {exp.action}")

# 経験パターンをスキルに結晶化
skills = forge.crystallize(min_experiences=3, min_confidence=0.7)
for skill in skills:
    print(f"  学習済み: {skill.rule}  (confidence={skill.confidence:.2f})")

# スキルをエージェント設定ファイルに反映
record = forge.evolve(config_path="./CLAUDE.md")
```

---

## サンプルプログラム

[`examples/`](../../examples/) ディレクトリに実行可能なスクリプトがあります。

### 1 · 基本的な record / query / crystallize / evolve

```python
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-demo")

# 経験を記録
forge.record(
    action="f文字列をログメッセージに使った",
    context="APIサーバーにデバッグログを追加",
    outcome="見やすい出力、レビュアーに承認された",
    valence=0.9,
)
forge.record(
    action="%フォーマットをログメッセージに使った",
    context="APIサーバーにデバッグログを追加",
    outcome="古いスタイルと指摘され書き直しを依頼された",
    valence=-0.6,
)

# 検索
result = forge.query("Pythonの文字列フォーマット")
for exp, score in result["best"]:
    print(f"  推奨 [{score:.2f}]: {exp.action}")

# スキルに結晶化
skills = forge.crystallize(min_experiences=2, min_confidence=0.5)
for s in skills:
    print(f"  [{s.confidence:.2f}] {s.rule}")
```

### 2 · ルールを直接教える (teach) と警告チェック (warn)

```python
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-teach")

# ルールを直接注入
forge.teach(
    rule="APIバウンダリでは必ずユーザー入力を検証する",
    context_pattern="HTTPリクエストやユーザー入力の処理",
    skill_type="positive",
    confidence=0.95,
)
forge.teach(
    rule="WHERE句なしのDELETEクエリは絶対に実行しない",
    context_pattern="データベース操作",
    skill_type="anti",
    confidence=1.0,
)

# 過去の失敗をシードとして記録
forge.record(
    action="WHERE句なしでDELETE FROMを実行",
    context="本番環境のデータベースクリーンアップ",
    outcome="テーブル全削除 — バックアップから3時間かけて復旧",
    valence=-1.0,
)

# 新しい操作の前に警告チェック
warnings = forge.warn(
    action="全レコードを削除するSQLを実行",
    context="データベースメンテナンス",
    threshold=0.4,
)
if warnings:
    print("警告 — 類似操作での過去の問題:")
    for w in warnings:
        print(f"  [{w.valence:.1f}] {w.outcome}")
```

### 3 · マルチプロジェクト

```python
from pathlib import Path
from engram_ai import ProjectManager

pm = ProjectManager(base_path=Path("/tmp/engram-projects"))

frontend = pm.get_forge("myapp/frontend")
backend  = pm.get_forge("myapp/backend")

frontend.record(
    action="TailwindのユーティリティクラスでレスポンシブGridを実装",
    context="ダッシュボードレイアウトコンポーネントの構築",
    outcome="高速な反復開発、デザイナーに承認",
    valence=0.9,
)
backend.record(
    action="5テーブル結合にSQLAlchemy ORMを使用",
    context="ダッシュボード分析エンドポイント",
    outcome="N+1問題で2秒のレスポンスタイム — 生SQLに書き直し",
    valence=-0.7,
)

print(pm.list_projects())  # ['myapp/backend', 'myapp/frontend']
```

全サンプルは [`examples/`](../../examples/) を参照してください。

---

## API リファレンス

### `Forge` — メインエントリーポイント

```python
from engram_ai import Forge

forge = Forge(
    storage_path="/path/to/data",   # デフォルト: ~/.engram-ai/data
    llm=my_llm,                     # BaseLLMインスタンス; None = キーワードのみモード
    anthropic_api_key="sk-...",     # llm=の代替
)
```

| メソッド | シグネチャ | 説明 |
|---------|-----------|------|
| `record` | `(action, context, outcome, valence) → Experience` | 完了した経験を保存 |
| `query` | `(context, k=5) → {"best": [...], "avoid": [...]}` | 上位k件の関連経験を取得 |
| `teach` | `(rule, context_pattern, skill_type, confidence) → Skill` | スキルを直接注入 |
| `warn` | `(action, context, threshold=0.6) → list[Experience]` | 類似操作の過去の失敗を取得 |
| `crystallize` | `(min_experiences=3, min_confidence=0.7) → list[Skill]` | スキルパターンを抽出 |
| `evolve` | `(config_path) → EvolutionRecord \| None` | スキルをエージェント設定に反映 |
| `observe` | `(messages, max_turns=3, crystallize_threshold=5) → dict` | 会話から自動記録 |
| `status` | `() → dict` | 統計情報を返す |
| `detect_conflicts` | `() → list[tuple[Skill, Skill]]` | 競合スキルペアを検出 |
| `merge_skills` | `(skill_a_id, skill_b_id) → Skill` | 競合スキルをマージ |
| `apply_decay` | `() → list[Skill]` | 時間ベースの信頼度減衰を適用 |

---

## CLIリファレンス

```bash
engram-forge setup [--uvx]    # Claude Codeの設定 (MCP + フック)
engram-forge setup-hooks       # フックのみ登録
engram-forge status            # 経験数・スキル数を表示
engram-forge query "トピック"  # 過去の経験を検索
engram-forge crystallize       # 経験からスキルを抽出
engram-forge evolve            # スキルをCLAUDE.mdに反映
engram-forge serve             # MCPサーバーを起動 (stdio)
engram-forge dashboard         # Web UIを起動 (デフォルト: http://127.0.0.1:3333)
engram-forge decay             # 時間ベースの信頼度減衰を適用
engram-forge conflicts         # 競合スキルペアを一覧表示
engram-forge merge <id_a> <id_b>  # 2つのスキルをマージ
```

**プロジェクトスコーピング:**

```bash
engram-forge -p frontend query "CSSレイアウト"
engram-forge -p backend crystallize
```

---

## MCPサーバー

`engram-forge serve` でMCPサーバーを起動すると、10個のツールが利用可能になります：

| ツール | 主な入力 | 出力 |
|-------|---------|------|
| `engram_record` | action, context, outcome, valence, project? | 経験ID |
| `engram_query` | context, k=5, project? | `{best: [...], avoid: [...]}` |
| `engram_crystallize` | min_experiences, min_confidence, project? | スキルリスト |
| `engram_evolve` | config_path, project? | 差分文字列 |
| `engram_teach` | rule, context_pattern, skill_type, confidence, project? | スキルオブジェクト |
| `engram_observe` | messages, max_turns, crystallize_threshold, project? | `{recorded, crystallized}` |
| `engram_status` | project? | 統計辞書 |
| `engram_conflicts` | project? | 競合スキルペア |
| `engram_merge` | skill_a_id, skill_b_id, project? | マージ済みスキル |
| `engram_decay` | project? | 更新済みスキルリスト |

**Claude Codeへの登録** (`engram-forge setup` で自動設定されます)：

```json
{
  "mcpServers": {
    "engram-forge": {
      "command": "engram-forge",
      "args": ["serve"]
    }
  }
}
```

---

## APIキーなしで使う

すべてのコア機能はAPIキーなしで動作します：

| 機能 | APIキーあり | APIキーなし |
|------|------------|------------|
| `record()` のValence検知 | LLM感情分析 | キーワードマッチング (日本語 + 英語) |
| `query()` | ChromaDBベクトル検索 | 同じ — 影響なし |
| `crystallize()` | LLMがパターン名を抽出 | キーワード頻度クラスタリング |
| `observe()` | 完全な抽出 | 無効 — エラーとインストールヒントを返す |
| その他すべてのツール | フル機能 | フル機能 |

---

## マルチプロジェクト対応

```python
from pathlib import Path
from engram_ai import ProjectManager

pm = ProjectManager(base_path=Path("~/.engram-ai/data"))

frontend_forge = pm.get_forge("my-app/frontend")
backend_forge  = pm.get_forge("my-app/backend")

print(pm.list_projects())  # ['my-app/frontend', 'my-app/backend']
```

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Forge (ファサード)                      │
├──────────┬──────────┬────────────────┬───────────────────────┤
│ Recorder │ Querier  │  Crystallizer  │        Evolver        │
├──────────┴──────────┴────────────────┴───────────────────────┤
│                         EventBus                             │
├────────────────────────┬────────────────────────────────────┤
│    ストレージ層          │         LLM層                      │
│    (ChromaDB)          │  (Claude API / カスタム BaseLLM)   │
├────────────────────────┴────────────────────────────────────┤
│        アダプター  (Claude Code · Cursor · Gemini …)         │
└─────────────────────────────────────────────────────────────┘
```

### 2フェーズ記録 (Claude Codeフック)

```
PostToolUseフック            UserPromptSubmitフック
       │                               │
       ▼                               ▼
 record_pending()  ──────────►  complete_pending()
 (action + context)              (outcome + valence検知)
       │                               │
       ▼                               ▼
  pending.jsonl                  ChromaDBストレージ
```

### Valence検知 (3段階)

1. **キーワードマッチング** — 無料・オフライン動作・日本語+英語対応
2. **LLMフォールバック** — キーワードが曖昧な場合にClaude API呼び出し
3. **デフォルト 0.3** — 両方失敗した場合の軽いポジティブ仮定

---

## Webダッシュボード

```bash
pip install "engram-forge[dashboard]"
engram-forge dashboard --port 3333
# → http://127.0.0.1:3333
```

| ページ | 表示内容 |
|--------|---------|
| **概要** | 統計カード、Valenceトレンドグラフ、ニューラルグラフプレビュー、最近の経験 |
| **経験** | 検索・フィルター可能なテーブル、詳細展開行 |
| **スキル** | 信頼度バー付きカードグリッド、ワンクリック結晶化・進化 |
| **グラフ** | 力学指向ニューラルグラフ — スキルノード(六角形)、経験ノード(円形) |

WebSocketによるリアルタイム更新 — 新しい経験・スキルが即座に反映されます。

---

## ロードマップ

- [x] コアの record / query / crystallize / evolve ループ
- [x] Claude Code向けの2フェーズフック記録
- [x] MCPサーバー (10ツール)
- [x] リアルタイムグラフ付きWebダッシュボード
- [x] マルチプロジェクト対応
- [x] pip + uvx 配布 (`engram-forge`)
- [x] Smithery MCPレジストリ
- [ ] マルチLLM対応 (OpenAI、Ollama、ローカルモデル)
- [ ] スキルマーケットプレイス — エージェント間でスキルを共有
- [ ] 感情タグ付け — スカラーValenceを超えた豊かな感情表現
- [ ] 経験チェーン — 関連する経験の連鎖
- [ ] 忘却曲線 — 時間加重の関連性減衰
- [ ] クロスエージェント転送 — エージェントインスタンス間でのメモリ共有
- [ ] 階層的メモリ — エピソード → スキル → メタスキル層

---

## コントリビューション

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate
pip install -e ".[full,dev]"
pytest
ruff check src/ tests/
```

[good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) から始めてみてください。

---

## ライセンス

Apache License 2.0 — 詳細は [LICENSE](../../LICENSE) を参照してください。

---

<div align="center">

**Engram-AIがあなたのAIエージェントの学習に役立ったら、スターをつけてください！**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
