# X (Twitter) — 日本語スレッド

## ツイート 1（フック）
```
今のAIメモリは「日記」です。

Engram-AIは「傷跡」を作ります。

なぜそれが重要なのか、説明します🧵
```

## ツイート 2
```
多くのAIメモリは事実を保存します：
「ユーザーはPythonが好き」
「このプロジェクトはRESTを使う」

でもそれは、エージェントが自分の行動から学ぶのには役立ちません。
```

## ツイート 3
```
Engram-AIが保存するのは「経験」です：

行動: APIレスポンスにOptional[str]を使った
文脈: RESTエンドポイントの設計
結果: ユーザーに却下 — "nullは不要"
Valence: -0.8 ← 学習シグナル

エージェントが何を知っているかではなく、
何をして、何が起きたか。
```

## ツイート 4
```
経験が積み重なると「スキル」に結晶化します：

"APIレスポンスモデルでOptional型は避ける"
信頼度: 0.85
根拠: 5件の経験

そしてスキルはエージェントの設定ファイルに進化します。
永続的に賢くなる仕組みです。
```

## ツイート 5
```
Claude Codeユーザーはワンコマンドで設定完了：

pip install "engram-forge[full]"
engram-forge setup

あとは自動です。
→ PostToolUse: Claudeの行動を記録
→ UserPromptSubmit: あなたの反応からValenceを検知

何も手動操作は不要。
```

## ツイート 6
```
Pythonライブラリとしても使えます：

from engram_ai import Forge

forge = Forge()
forge.record(action=..., context=..., outcome=..., valence=0.9)

result = forge.query("REST APIの設計パターン")
# → {"best": [...], "avoid": [...]}

forge.crystallize()
forge.evolve("./CLAUDE.md")
```

## ツイート 7
```
Anthropic APIキーなしでも動きます。

・Valence検知: キーワードマッチング（日本語・英語対応）
・結晶化: キーワード頻度クラスタリング

完全オフラインで動作。

[claude]オプションを追加するとLLMによる高品質な結晶化が有効になります。
```

## ツイート 8
```
MCPサーバーとして起動すると10ツールが使えます：

engram_record / engram_query / engram_crystallize
engram_evolve / engram_teach / engram_observe
engram_status / engram_conflicts / engram_merge / engram_decay

Claudeが会話中に自分のメモリを直接参照できます。
```

## ツイート 9（CTA）
```
pip install engram-forge

Apache 2.0 / Python 3.10+ / ChromaDB + Pydantic v2

GitHub: https://github.com/kajaha06251020/Engram-AI
PyPI:   https://pypi.org/project/engram-forge/
Discord: discord.gg/hGAcEfKqgq

もし役に立ちそうと思ったら⭐をもらえると嬉しいです🙏

#Python #AI #LLM #ClaudeAI #MCP #機械学習 #OSS #個人開発
```

## スタンドアロン投稿用ハッシュタグ
```
#Python #AI #LLM #Claude #MCP #機械学習 #OSS #個人開発 #BuildInPublic #AIエージェント
```
