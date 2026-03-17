# Engram-AI Discord Server Design Specification

**Date:** 2026-03-17
**Status:** Approved for Implementation
**Approach:** Discord.py Bot — 全機能を1つのカスタムBotで統合

---

## 1. Overview

Engram-AIプロジェクトのDiscordサーバー設計。内部開発チーム向けのコミュニケーション基盤と、外部OSSコミュニティ向けの公開チャンネルを1つのサーバーに統合する。

**要件:**
- 開発・報告・コミュニティなど用途別チャンネル構成
- GitHub連携（Issue/PR/コミット通知）
- CI/CD通知（テスト結果・デプロイ状況）
- Engram-AI自体のDiscord Bot化（経験検索・クエリをDiscord上で実行）
- 翻訳Bot（既存のTranslator Botを導入、リアクションフラグ方式）
- ロールベースの権限管理

**言語方針:** チャンネル名は英語、投稿は日英どちらもOK。翻訳はTranslator Botのリアクションフラグ（🇯🇵 / 🇺🇸）で対応。

---

## 2. Server Structure — Categories & Channels

**注:** 各チャンネルの「Type」はデフォルトの投稿可否を示す。ロールごとの実際の権限はセクション3の Permission Matrix を参照。

### 📋 WELCOME
| Channel | Type | Description |
|---------|------|-------------|
| #rules | 読み取り専用 | サーバールール・Code of Conduct |
| #welcome | 読み取り専用 | 自動挨拶・自己紹介案内 |
| #self-introduction | 投稿可 | 自己紹介用 |
| #role-select | 特殊 | リアクションでロール選択（BotがEmbed投稿、ユーザーはリアクションのみ） |

### 🔧 DEVELOPMENT
| Channel | Type | Description |
|---------|------|-------------|
| #dev-general | Contributor以上投稿可 | 開発全般の議論 |
| #dev-frontend | Contributor以上投稿可 | ダッシュボード/Next.js関連 |
| #dev-backend | Contributor以上投稿可 | コア/Python関連 |
| #dev-v02 | Contributor以上投稿可 | v0.2機能の議論 |
| #code-review | Contributor以上投稿可 | レビュー依頼・議論 |

### 🐛 REPORTS
| Channel | Format | Description |
|---------|--------|-------------|
| #bug-reports | Forum | バグ報告（タグ: severity, component, status） |
| #feature-requests | Forum | 機能要望（タグ: priority, area） |
| #issue-tracker | Bot専用 | GitHub Issueイベントのフィルタリング表示（github cogが #github-feed とは別にissueイベントのみ投稿） |

### 📢 ANNOUNCEMENTS
| Channel | Type | Description |
|---------|------|-------------|
| #announcements | 読み取り専用 | リリース・重要通知（Core Dev以上が投稿） |
| #changelog | 読み取り専用 | 自動バージョン更新通知 |

### 🤖 BOT & CI
| Channel | Type | Description |
|---------|------|-------------|
| #github-feed | Bot専用 | PR/Push/コミット通知 |
| #ci-cd | Bot専用 | テスト結果・デプロイ状況 |
| #bot-logs | Bot専用 | Bot自体のログ・ステータス（構造化Embed: INFO/WARN/ERROR レベル表示） |

### 💬 COMMUNITY
| Channel | Format | Description |
|---------|--------|-------------|
| #general | テキスト | 雑談 |
| #help | Forum | 使い方サポート・Q&A（タグ: resolved/unresolved） |
| #showcase | テキスト | ユーザーの活用事例共有 |

### 🔒 INTERNAL (Core Dev以上のみ)
| Channel | Type | Description |
|---------|------|-------------|
| #core-dev | 投稿可 | 内部開発議論 |
| #planning | 投稿可 | ロードマップ・スプリント計画 |
| #admin | 投稿可 | サーバー管理・監査ログ |

### 🎤 VOICE
| Channel | Type | Description |
|---------|------|-------------|
| #voice-dev | ボイス | ペアプロ・ミーティング用 |
| #voice-community | ボイス | コミュニティ雑談 |

---

## 3. Roles & Permissions

### Role Definitions

| Role | Color | Description |
|------|-------|-------------|
| **Admin** | 🔴 Red | サーバーオーナー。全権限・サーバー管理 |
| **Core Dev** | 🟠 Orange | コア開発メンバー。INTERNAL閲覧・チャンネル管理・メッセージ管理・Webhook管理 |
| **Contributor** | 🟡 Yellow | PR/Issueを出した貢献者。DEVELOPMENTへの投稿・画像添付・リアクション・スレッド作成 |
| **Tester** | 🟢 Green | テスター。REPORTS優先権・DEV閲覧可・バグレポートテンプレ使用 |
| **Community** | 🔵 Blue | 一般参加者（デフォルト）。COMMUNITY/WELCOME/ANNOUNCEMENTS閲覧・HELPへの投稿 |

### Permission Matrix

| Category | Admin | Core Dev | Contributor | Tester | Community |
|----------|-------|----------|-------------|--------|-----------|
| WELCOME | ✅ 管理 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 (#rules, #welcome は全員読み取り専用) |
| DEVELOPMENT | ✅ 管理 | ✅ 投稿 | ✅ 投稿 | 👁 閲覧のみ | 👁 閲覧のみ |
| REPORTS | ✅ 管理 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 |
| ANNOUNCEMENTS | ✅ 投稿 | ✅ 投稿 | 👁 閲覧 | 👁 閲覧 | 👁 閲覧 |
| BOT & CI | ✅ 管理 | 👁 閲覧 | 👁 閲覧 | 👁 閲覧 | 👁 閲覧 |
| COMMUNITY | ✅ 管理 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 | ✅ 投稿 |
| INTERNAL | ✅ 管理 | ✅ 投稿 | ❌ 不可視 | ❌ 不可視 | ❌ 不可視 |
| VOICE | ✅ 管理 | ✅ 接続 | ✅ 接続 | ✅ 接続 | ✅ 接続 |

---

## 4. Bot Architecture

### Required Discord Intents

Bot は以下の Privileged Gateway Intents を必要とする（Discord Developer Portal で有効化が必要）:

| Intent | Required By | Reason |
|--------|------------|--------|
| `Intents.members` (Privileged) | welcome cog, moderation cog | `on_member_join` イベント受信、リアクションロール付与 |
| `Intents.message_content` (Privileged) | 全スラッシュコマンド以外の機能 | プレフィックスコマンドのフォールバック（主要機能はスラッシュコマンド） |
| `Intents.guilds` | setup cog | カテゴリ・チャンネル・ロール管理 |
| `Intents.reactions` | moderation cog | リアクションロール検知 |
| `Intents.voice_states` | — | ボイスチャンネルはBot管理対象外（インフラのみ）。将来ボイスイベント監視が必要になった場合に有効化 |

### Command Strategy

**スラッシュコマンド（Application Commands）をメインとし、`!` プレフィックスコマンドは Admin 専用の管理機能のみに使用する。**

理由: Discord は未検証Bot（100サーバー未満）に対して `message_content` Intent の使用を制限している。スラッシュコマンドはこの制限を受けない。

| Command | Type | Description |
|---------|------|-------------|
| `/query <topic>` | Slash | Engram-AI 経験検索 |
| `/status` | Slash | Engram-AI ステータス確認 |
| `/crystallize` | Slash | スキル結晶化実行 |
| `!setup` | Prefix (Admin) | サーバー構成一括セットアップ |
| `!sync` | Prefix (Admin) | スラッシュコマンド同期 |

### Project Structure

```
engram-discord-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Bot起動・Cogロード・aiohttp起動統合
│   ├── config.py            # 設定（Token, Guild ID, チャンネルID）
│   ├── cogs/
│   │   ├── setup.py         # サーバー構成自動セットアップ（!setup）
│   │   ├── github.py        # GitHub Webhook受信 → #github-feed, #issue-tracker 投稿
│   │   ├── ci_cd.py         # GitHub Actions Webhook → テスト結果通知
│   │   ├── engram.py        # Engram-AI連携（/query, /status, /crystallize）
│   │   ├── moderation.py    # ロール管理・リアクションロール・AutoMod設定
│   │   └── welcome.py       # 入退室メッセージ・自動ロール付与
│   └── utils/
│       ├── embeds.py        # 統一Embed生成ヘルパー
│       ├── permissions.py   # 権限チェックデコレータ
│       ├── webhook.py       # GitHub Webhook HMAC-SHA256 署名検証
│       └── queue.py         # Webhook イベントキュー（レート制限対応）
├── .env.example             # テンプレート（秘密値なし、コミット対象）
├── .env                     # 実際の秘密値（.gitignore対象）
├── .gitignore               # .env を含む
├── requirements.txt         # discord.py, aiohttp, engram-ai
└── pyproject.toml
```

### Cog Responsibilities

| Cog | Functionality | Trigger |
|-----|---------------|---------|
| **setup** | カテゴリ・チャンネル・ロール一括作成。セクション2,3の構成をコードで定義し `!setup` で実行。作成した #role-select メッセージIDを `config.json` に永続化 | `!setup` コマンド（Admin限定） |
| **github** | GitHub Webhookイベントを受信し、PR/Pushを #github-feed に、Issueイベントを #issue-tracker にEmbed化して投稿。`utils/webhook.py` で署名検証、`utils/queue.py` でレート制限対応 | GitHub Webhook (aiohttp HTTPサーバーで受信) |
| **ci_cd** | GitHub Actions の `workflow_run` イベントを受信し、テスト結果（pass/fail/duration）を #ci-cd に投稿 | GitHub Actions Webhook |
| **engram** | Engram-AIのForge(`enable_policies=True`)をimportし、Discord上で経験検索・ステータス確認・結晶化を実行 | `/query`, `/status`, `/crystallize` スラッシュコマンド |
| **moderation** | #role-select にロール選択Embedを投稿。リアクション追加/削除でロールを付与/剥奪。Discord AutoMod ルール設定（スパム防止） | リアクションイベント |
| **welcome** | メンバー参加時に #welcome で挨拶メッセージを送信し、Communityロールを自動付与 | `on_member_join` イベント |

### asyncio Event Loop Integration

discord.py の `bot.run()` はイベントループをブロックするため、aiohttp Webhook サーバーとの共存には以下のパターンを使用:

```python
# bot/main.py
async def main():
    bot = EngramBot()

    # aiohttp webhook server
    app = web.Application()
    github_cog = bot.get_cog("GitHub")
    app.router.add_post("/webhook/github", github_cog.handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.WEBHOOK_PORT)

    # Both run in the same event loop
    await asyncio.gather(
        bot.start(config.DISCORD_TOKEN),
        site.start()
    )

asyncio.run(main())
```

### Webhook Event Queue

高頻度の GitHub イベントによる Discord API レート制限（5 messages / 5 seconds / channel）への対策:

```python
# bot/utils/queue.py
# asyncio.Queue + consumer task パターン
# - Webhook受信時にキューに追加
# - Consumer が 1.2秒間隔でキューからDequeue → Discord投稿
# - チャンネルごとに独立したキュー
```

### Error Handling & Resilience

| Scenario | Handling |
|----------|----------|
| Discord gateway disconnect | discord.py 内蔵の自動再接続（デフォルト有効） |
| aiohttp port conflict | 起動時にエラーログ → Bot は Discord 機能のみで起動 |
| Webhook 署名検証失敗 | 403 返却 + #bot-logs に WARNING Embed |
| Engram-AI Forge エラー | スラッシュコマンドの response でエラーメッセージ表示 |
| #role-select メッセージ消失 | 起動時に config.json のメッセージID を検証、不在なら #bot-logs に WARN |

### Bot Log Format

`#bot-logs` には構造化 Embed を投稿:
- **INFO** (🟢): 起動・Cogロード・コマンド実行
- **WARN** (🟡): 署名検証失敗・レート制限接近・設定不整合
- **ERROR** (🔴): 例外・接続失敗・Forge初期化エラー

### Technology Stack

- **discord.py** 2.x — Cog / スラッシュコマンド / Intents対応
- **aiohttp** — GitHub Webhook受信用の軽量HTTPサーバー（Botと同一イベントループで動作）
- **engram-ai** — ライブラリとして直接import（`Forge(enable_policies=True)` で初期化）

---

## 5. External Integrations

### GitHub Webhook
- GitHubリポジトリの Settings → Webhooks でBotのaiohttp HTTPエンドポイントを登録
- 対象イベント: `push`, `pull_request`, `issues`, `workflow_run`
- HMAC-SHA256 署名検証（`utils/webhook.py` で実装）
- GitHub の Webhook 送信元IP範囲でのフィルタリングは任意（プラットフォームデプロイ時はTLS終端がプラットフォーム側で処理される）

### Translation Bot
- [Translator Bot](https://top.gg/bot/translator) をサーバーに招待
- リアクションフラグ方式: 🇯🇵 で日本語、🇺🇸 で英語に翻訳
- 全チャンネルで有効
- **既知のリスク:** サードパーティBotのため、オフラインや仕様変更の可能性あり。翻訳が使えなくなった場合は代替Bot（Saki等）に差し替え、またはカスタム翻訳機能をengram cogに追加

---

## 6. Deployment

### Secrets Management

**`.env.example`（コミット対象）:**
```
DISCORD_TOKEN=              # Discord Bot Token (Developer Portal)
DISCORD_GUILD_ID=           # サーバーID
GITHUB_WEBHOOK_SECRET=      # GitHub Webhook署名検証用
ANTHROPIC_API_KEY=          # Engram-AI連携用（Claude API）
ENGRAM_STORAGE_PATH=        # ChromaDBストレージパス (default: ./data)
WEBHOOK_PORT=8080           # aiohttp Webhookリスナーポート
```

**重要:**
- `.env` は `.gitignore` に含め、絶対にコミットしない
- `DISCORD_TOKEN` と `ANTHROPIC_API_KEY` は高価値の秘密情報 — 漏洩時は即座にローテーション
- Railway/Render デプロイ時はプラットフォームのシークレット管理機能を使用（`.env` ファイルではなく環境変数設定画面）
- VPS デプロイ時は systemd の `EnvironmentFile` ディレクティブでファイル権限を制限（600）

### Bot State Persistence

Botの実行時状態は `config.json` に永続化:
- `role_select_message_id`: #role-select のリアクションロールメッセージID
- `channel_ids`: setup cog が作成したチャンネルIDのマッピング
- 起動時に検証し、不整合があれば #bot-logs に警告

### Deployment Options

| Option | Pros | Cons | HTTPS | Best For |
|--------|------|------|-------|----------|
| **Railway / Render** | 無料枠あり、Pythonデプロイ簡単 | 無料枠制限あり | プラットフォーム提供 | プロトタイプ・小規模運用 |
| **VPS (自前)** | 完全制御、systemdで管理 | サーバー管理必要 | nginx リバースプロキシ必要 | 本番運用 |
| **ローカル実行** | コストゼロ、即座に開始 | PC起動中のみ動作 | ngrok等でトンネル | 開発初期 |

### Monitoring

- `#bot-logs` チャンネルでBot自体のヘルスステータスを確認
- 起動時に INFO Embed（バージョン、ロード済みCog一覧、Webhook port）を投稿
- Webhook エンドポイントのヘルスチェック: `GET /health` → 200 OK
- 外部監視（任意）: UptimeRobot等でWebhookエンドポイントの死活監視
