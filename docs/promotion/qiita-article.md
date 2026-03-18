# Qiita 記事

## タイトル
```
【Python】AIエージェントが自分の失敗から学ぶメモリシステムを作った（Claude Code対応・APIキー不要）
```

## タグ
```
Python, AI, LLM, Claude, MachineLearning
```

---

## 記事本文

# AIエージェントが自分の失敗から学ぶ — Engram-AIの設計と実装

## TL;DR

- AIエージェント向けの「経験駆動型メモリ」ライブラリを作りました
- `pip install engram-forge` で使えます（APIキー不要でコア機能動作）
- Claude Codeのフックと連携して自動学習できます
- ChromaDB + Pydantic v2 + Click + MCP SDK構成

## きっかけ

Claude Codeを使っていて気になったのが、セッションをまたぐと過去の修正が全部リセットされること。「`Optional[str]`はやめて」と10回言っても、次のセッションでは同じことをする。

既存のAIメモリソリューション（Mem0など）は「事実」を保存するRAGベースです。`"ユーザーはOptional型を嫌う"` という事実を保存できても、**「なぜ嫌いなのか」「どの程度嫌いなのか」「何回そういう経験があったのか」** は保存できません。

そこで、因果構造を持つ経験を保存する仕組みを作りました。

## アーキテクチャ概要

```
Forge（ファサード）
├── Recorder     — 経験の記録・valence検知
├── Querier      — ChromaDB検索・valence分割
├── Crystallizer — クラスタリング・LLM抽出
├── Evolver      — 設定ファイルへの書き込み
├── EventBus     — 内部イベント管理
├── Storage層    — ChromaDB（BaseStorageで差し替え可）
└── LLM層        — Claude API（BaseLLMで差し替え可）
```

## データモデル

```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Experience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str           # エージェントが何をしたか
    context: str          # どういう状況で
    outcome: str          # 何が起きたか
    valence: float        # -1.0 (最悪) 〜 +1.0 (最高)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule: str             # 汎化されたルール
    context_pattern: str  # 適用コンテキスト
    confidence: float     # 0.0 〜 1.0
    evidence_count: int   # 根拠となった経験の数
    skill_type: str       # "positive" or "anti"
```

## Valence検知の3段階パイプライン

Claude Code のフックで使う場合、経験の記録は2フェーズになります：

**Phase 1 — PostToolUseフック（valenceなし）**
```python
forge.record_pending(
    action="Write on src/api.py",
    context="Write tool usage",
    metadata={"tool": "Write", "file": "src/api.py"},
)
```

**Phase 2 — UserPromptSubmitフック（valence検知）**
```python
# ユーザーの次のメッセージからvalenceを検知
valence = forge.detect_valence(user_message)
forge.complete_pending(outcome=user_message[:200], valence=valence)
```

`detect_valence()`の実装：

```python
def detect_valence(self, text: str) -> float:
    # Step 1: キーワードマッチング（日本語・英語）
    positive_keywords = ["perfect", "great", "approved", "いいね", "完璧", "承認"]
    negative_keywords = ["wrong", "no", "bad", "違う", "やり直し", "ダメ"]

    pos = sum(1 for k in positive_keywords if k in text.lower())
    neg = sum(1 for k in negative_keywords if k in text.lower())

    if pos > neg:
        return 0.7
    elif neg > pos:
        return -0.7

    # Step 2: LLMフォールバック
    if self._llm:
        try:
            return self._llm.detect_valence(text)
        except Exception:
            pass

    # Step 3: デフォルト（軽いポジティブ仮定）
    return 0.3
```

## Crystallizationのアルゴリズム

```python
def crystallize(self, min_experiences=3, min_confidence=0.7) -> list[Skill]:
    experiences = self._storage.get_all_experiences()

    # 1. ChromaDBで類似経験をクエリしてクラスタリング
    clusters = self._cluster_experiences(experiences)

    skills = []
    for cluster in clusters:
        if len(cluster) < min_experiences:
            continue

        avg_valence = sum(e.valence for e in cluster) / len(cluster)
        avg_abs_valence = sum(abs(e.valence) for e in cluster) / len(cluster)

        if avg_abs_valence < min_confidence:
            continue

        # 2. LLMでパターンを抽出（なければキーワードフォールバック）
        if self._llm:
            rule = self._llm.extract_pattern(cluster)
        else:
            rule = self._keyword_extract_pattern(cluster)

        skill = Skill(
            rule=rule,
            context_pattern=cluster[0].context,
            confidence=avg_abs_valence,
            evidence_count=len(cluster),
            skill_type="positive" if avg_valence > 0 else "anti",
        )
        self._storage.store_skill(skill)
        skills.append(skill)

    return skills
```

キーワードフォールバック（LLMなし）：

```python
def _keyword_extract_pattern(self, cluster: list[Experience]) -> str:
    from collections import Counter
    # 全経験のactionとcontextから高頻度単語を抽出
    words = []
    for exp in cluster:
        words.extend(exp.action.lower().split())
        words.extend(exp.context.lower().split())

    # ストップワード除去
    stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and"}
    freq = Counter(w for w in words if w not in stopwords and len(w) > 3)
    top_words = [w for w, _ in freq.most_common(3)]

    avg_valence = sum(e.valence for e in cluster) / len(cluster)
    prefix = "Prefer" if avg_valence > 0 else "Avoid"
    return f"{prefix} {' '.join(top_words)} in similar contexts"
```

## Quick Start

```python
from engram_ai import Forge

forge = Forge(storage_path="/tmp/my-agent-memory")

# 経験を記録
forge.record(
    action="f文字列でログメッセージをフォーマットした",
    context="APIサーバーにデバッグログを追加",
    outcome="レビュアーに承認 — 読みやすいと評価された",
    valence=0.9,
)

# 同種の経験をもう少し追加...

# 検索
result = forge.query("Pythonの文字列フォーマット", k=5)
for exp, score in result["best"]:
    print(f"推奨 [{score:.2f}]: {exp.action}")
for exp, score in result["avoid"]:
    print(f"回避 [{score:.2f}]: {exp.action}")

# スキルに結晶化
skills = forge.crystallize(min_experiences=2, min_confidence=0.5)

# CLAUDE.mdに反映
forge.evolve("./CLAUDE.md")
```

## Claude Code連携のセットアップ

```bash
pip install "engram-forge[full]"
engram-forge setup
```

`~/.claude/settings.json`に以下が追加されます：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [{"type": "command", "command": "engram-forge hook post-tool-use"}]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "engram-forge hook user-prompt-submit"}]
      }
    ]
  },
  "mcpServers": {
    "engram-forge": {
      "command": "engram-forge",
      "args": ["serve"]
    }
  }
}
```

## インストール

```bash
# コアのみ（APIキー不要）
pip install engram-forge

# Anthropic SDK追加
pip install "engram-forge[claude]"

# MCPサーバー追加
pip install "engram-forge[mcp]"

# Webダッシュボード追加
pip install "engram-forge[dashboard]"

# 全部入り（推奨）
pip install "engram-forge[full]"
```

## まとめ

| 機能 | 実装 |
|------|------|
| ストレージ | ChromaDB（BaseStorageで差し替え可） |
| LLM | Claude API（BaseLLMで差し替え可） |
| Valence検知 | キーワード → LLM → デフォルト（3段階） |
| 結晶化 | コサイン類似度クラスタリング + LLM抽出 |
| 統合 | MCP（10ツール） + CLI + Python API + Dashboard |

- **GitHub:** https://github.com/kajaha06251020/Engram-AI
- **PyPI:** https://pypi.org/project/engram-forge/
- **Discord:** https://discord.gg/hGAcEfKqgq

Apache 2.0 / Python 3.10+ / v0.4.0

フィードバック・Issue・PRお待ちしています。
