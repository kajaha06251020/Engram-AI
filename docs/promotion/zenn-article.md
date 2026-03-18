# Zenn 記事

## タイトル
```
AIエージェントに「日記」ではなく「傷跡」を与える — 経験駆動型メモリライブラリ Engram-AI を作った
```

## 絵文字
```
🧠
```

## トピック
```
python, ai, llm, claudeai, openai
```

---

## 記事本文

# AIエージェントに「日記」ではなく「傷跡」を与える

Claude Codeと一緒に開発していると、こういう経験はないでしょうか。

「同じ間違いを何度も繰り返す」
「先週直したパターンを今週また使う」
「セッションをまたぐと全てリセットされる」

このフラストレーションから、**Engram-AI** というライブラリを作りました。

## 問題：AIメモリは「日記」

多くのAIメモリシステムは、テキストの事実を保存します：

- 「ユーザーはPythonを好む」
- 「このプロジェクトはREST APIを使う」
- 「チームはconventional commitsに従う」

これらはセマンティック検索で取得できる「知識」です。

でも、これでは**学習**ができません。

エージェントが「`Optional[str]`をAPIレスポンスに使うたびにユーザーが却下する」というパターンに気づくには、知識だけでは不十分です。**因果関係** が必要です。

## 解決策：「傷跡」モデル

生物の脳における**エングラム**（engram）は、経験によって形成される物理的な記憶痕跡です。特に感情的な結果（良かった/悪かった）を伴う経験は、より強い痕跡を残します。

Engram-AIはこのモデルを採用しています。事実ではなく、**経験**を保存します：

```python
Experience(
    action  = "APIレスポンスモデルにOptional[str]を使った",
    context = "モバイルクライアント向けRESTエンドポイントの設計",
    outcome = "ユーザーに却下 — 「nullは不要です」",
    valence = -0.8,   # ← 学習シグナル (-1.0〜+1.0)
)
```

`valence`（感情価）が鍵です。これがあることで、エージェントは「良かった経験」と「悪かった経験」を区別して学習できます。

## 4つの操作

Engram-AIの核心は4つの操作です。

### 1. Record — 経験を記録

```python
from engram_ai import Forge

forge = Forge()

forge.record(
    action="リスト内包表記で10万行のCSVを変換した",
    context="pandasパイプラインでのデータ処理",
    outcome="高速で可読性が高く、ユーザーにすぐ承認された",
    valence=0.9,
)
```

### 2. Query — 過去の経験を検索

```python
result = forge.query("データ変換のアプローチ")

print("うまくいった方法:")
for exp, score in result["best"]:
    print(f"  [{score:.2f}] {exp.action}")

print("避けるべき方法:")
for exp, score in result["avoid"]:
    print(f"  [{score:.2f}] {exp.action}")
```

ChromaDBのコサイン類似度で検索し、valenceで`best`/`avoid`に分割します。

### 3. Crystallize — パターンをスキルに結晶化

```python
skills = forge.crystallize(min_experiences=3, min_confidence=0.7)

for skill in skills:
    print(f"習得: {skill.rule} (confidence={skill.confidence:.2f})")
# → 習得: "データ変換にはリスト内包表記を優先する" (confidence=0.87)
```

**仕組み:**
1. ChromaDBで類似経験をクラスタリング（コサイン類似度）
2. 十分な証拠があるクラスターに対してLLMが「このパターンから導き出せるルールは何か」を抽出
3. `Skill`オブジェクトとして保存（信頼度・証拠数付き）

APIキーがなくてもキーワード頻度クラスタリングにフォールバック。オフラインでも動作します。

### 4. Evolve — スキルを設定ファイルに反映

```python
forge.evolve(config_path="./CLAUDE.md")
```

CLAUDE.mdに習得したルールのブロックが書き込まれます：

```markdown
<!-- engram-forge:start -->
## Engram-AI: 学習済みスキル
- データ変換にはリスト内包表記を優先する (confidence: 0.87)
- APIレスポンスモデルでOptional型は避ける (confidence: 0.85)
- テストファイルでは説明的な変数名を使う (confidence: 0.92)
<!-- engram-forge:end -->
```

次のセッションから、エージェントはこのルールを最初から適用します。

## Claude Codeとの連携

Claude Codeユーザーにとって最も嬉しい使い方は、ワンコマンドのセットアップです：

```bash
pip install "engram-forge[full]"
engram-forge setup
# Claude Codeを再起動
```

これで2つのフックが`~/.claude/settings.json`に登録されます：

### PostToolUseフック

Claudeがツールを使うたびに発火し、**pending経験**として記録：
- 何のツールを使ったか → `action`
- どのファイル/コンテキストで → `context`

この時点ではまだvalenceは不明。結果を待ちます。

### UserPromptSubmitフック

あなたが次のメッセージを送ったときに発火し、**valenceを検知**して経験を完成：

- 「いいね！」「完璧」「承認」→ valence +0.8程度
- 「違います」「やり直して」「ダメ」→ valence -0.7程度

**Valence検知は3段階：**
1. キーワードマッチング（日本語・英語対応、無料・オフライン）
2. LLMフォールバック（曖昧な反応の場合）
3. デフォルト 0.3（両方失敗した場合の軽いポジティブ仮定）

明示的に評価を入力しなくても、自然な会話から自動で学習します。

## MCPサーバーとして10ツールを公開

`engram-forge serve`でMCPサーバーを起動すると、Claudeが会話中に直接メモリを参照できます：

| ツール | 説明 |
|--------|------|
| `engram_query` | 「REST APIの設計で気をつけることは？」 |
| `engram_record` | 重要な経験を手動で記録 |
| `engram_teach` | ルールを直接注入 |
| `engram_crystallize` | 結晶化を手動トリガー |
| `engram_status` | 学習の進捗を確認 |
| その他5ツール | conflicts, merge, decay, observe, evolve |

## APIキーなしでも動く

これは設計上の重要な決断でした：

| 機能 | APIキーあり | APIキーなし |
|------|------------|------------|
| Valence検知 | LLM感情分析 | キーワードマッチング |
| Query | ChromaDB検索 | 同じ（影響なし） |
| Crystallize | LLMがパターン抽出 | キーワード頻度クラスタリング |
| その他 | フル機能 | フル機能 |

```bash
pip install engram-forge   # コアのみ、APIキー不要
```

## ルールを直接教える

経験が溜まるのを待たなくても、既知のルールを直接注入できます：

```python
forge.teach(
    rule="APIバウンダリでは必ずユーザー入力を検証する",
    context_pattern="HTTPリクエストの処理",
    skill_type="positive",
    confidence=0.95,
)

forge.teach(
    rule="WHERE句なしのDELETEは絶対に実行しない",
    context_pattern="データベース操作",
    skill_type="anti",
    confidence=1.0,
)
```

アクション前に過去の失敗をチェック：

```python
warnings = forge.warn(
    action="本番DBで全レコードを削除するSQLを実行",
    context="データベースメンテナンス",
    threshold=0.5,
)
if warnings:
    for w in warnings:
        print(f"[{w.valence:.1f}] {w.outcome}")
```

## マルチプロジェクト対応

プロジェクトごとに独立したメモリを持てます：

```python
from engram_ai import ProjectManager
from pathlib import Path

pm = ProjectManager(base_path=Path("/tmp/projects"))

frontend = pm.get_forge("myapp/frontend")
backend  = pm.get_forge("myapp/backend")

# 完全に独立しているので混在しない
frontend.record(action="Tailwindでレスポンシブグリッドを実装", ...)
backend.record(action="SQLAlchemy ORMで5テーブル結合", ...)

print(pm.list_projects())  # ['myapp/frontend', 'myapp/backend']
```

CLIでも：

```bash
engram-forge -p myapp/frontend query "CSSレイアウトのパターン"
engram-forge -p myapp/backend  crystallize
```

## カスタムLLMへの対応

`BaseLLM`を実装すれば任意のLLMが使えます：

```python
from engram_ai.llm.base import BaseLLM
from engram_ai import Forge

class OllamaLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        import requests
        resp = requests.post("http://localhost:11434/api/generate",
                             json={"model": "llama3", "prompt": prompt})
        return resp.json()["response"]

    def extract_experience(self, messages):
        # 会話からaction/context/outcome/valenceを抽出
        ...

forge = Forge(llm=OllamaLLM())
```

OpenAIの例も[examplesディレクトリ](https://github.com/kajaha06251020/Engram-AI/blob/main/examples/06_custom_llm.py)にあります。

## Webダッシュボード

```bash
pip install "engram-forge[dashboard]"
engram-forge dashboard --port 3333
# → http://127.0.0.1:3333
```

- 経験の一覧・検索・フィルタリング
- スキルのカードグリッド（信頼度バー付き）
- 力学指向ニューラルグラフ（経験とスキルの関係を可視化）
- WebSocketリアルタイム更新

## インストール

```bash
pip install engram-forge                    # コア（APIキー不要）
pip install "engram-forge[claude]"          # + Anthropic SDK
pip install "engram-forge[mcp]"             # + MCPサーバー
pip install "engram-forge[dashboard]"       # + Webダッシュボード
pip install "engram-forge[full]"            # 全部入り（推奨）
pip install "engram-forge[full,dev]"        # + 開発ツール
```

## 正直な限界

- **結晶化の品質はLLMに依存します。** キーワードフォールバックは機能しますが、汎用的なルール名になりがちです。
- **Valenceはスカラーです。** より豊かな感情モデルはロードマップにあります。
- **フォーマルなベンチマークはまだありません。** 初期段階のインフラです。
- **クラスタリングはgreedy。** より良いアルゴリズムでスキル品質が向上します。

## 最後に

- **GitHub:** https://github.com/kajaha06251020/Engram-AI
- **PyPI:** https://pypi.org/project/engram-forge/
- **Discord:** https://discord.gg/hGAcEfKqgq

Apache 2.0 / Python 3.10+ / v0.4.0

フィードバック歓迎です。特に`crystallize()` → `evolve()`の2ステップ設計、valenceモデル、フックによる2フェーズ記録の使い勝手について意見をいただけると嬉しいです。
