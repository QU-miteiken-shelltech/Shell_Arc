# shellarc_core を始める

### *For the English version, see [HOW_TO_START.md](../DOCS/HOW_TO_START.md).*

このガイドでは、`shellarc_core` を実際にセットアップして動かすまでの手順を説明します。プロジェクトの概要や「何ができるか」については [README_jpn.md](../README_jpn.md) を参照してください。

---

## 🚀 クイックスタート：コード不要、Discordサーバーとしてすぐ使える

ShellArcには、標準のフロントエンドとしてDiscordボット一式が同梱されています。提出・レビュー・進捗管理といった機能はすべて、コマンドやボタンとして既にDiscord上に実装済みです。利用者側は設定とデプロイをするだけで、アプリケーションコードを書く必要はありません。

| docker-composeサービス | 使用するDockerfile | 追加されるDiscordコマンド |
|---|---|---|
| `bot`（メインの作業フローボット） | `Dockerfile.dc` | `..up` ファイル提出 ・ `..upbig` 大容量ファイルを一時アップロードリンクで提出 ・ `..appr` ボタンで承認/却下 ・ `..dl` テイクのダウンロード ・ `..check` レビュー待ち状況の確認 ・ `..reg` 担当者登録 ・ `..history` 提出・承認履歴の照会 ・ `..ask` 「自分の担当作業は？」 ・ `..sync` ローカルGitをリモートへ同期 |
| `itemi_action`（進行管理・リマインダーボット） | `Dockerfile.itemi` | `..lo` 絵コンテ画像のアップロード/ダウンロード/リポイント ・ `..remind` リマインダーの予約 ・ `..daiben` 誰かに代わってメッセージを中継 |
| `ai_chat`（AIチャットボット） | `Dockerfile.nullai` | `..nuru` AIアシスタントに質問（Dify経由） ・ `..summary` 返信先メッセージの要約 ・ `..weather` 天気の照会 |

### 1. プロジェクトコンテキストディレクトリを準備する

```
project_ctx/
├── project_settings.json     # コアライブラリの設定
├── spreadsheet_map.json      # コアライブラリの設定
├── discord_config.json       # コマンドプレフィックス・チャンネル/ロールのマッピングなど
└── .env                      # 各サービスの認証情報 + Discordボットのトークン
```

コアライブラリ自体の認証情報に加えて、`.env` には以下が必要です。

```dotenv
Discord_token=...              # メインの "bot" サービス用
Discord_pmmanager_token=...    # itemi_action サービス用
Discord_charbot_token=...      # ai_chat サービス用
Discord_server_id=...
Dify_token=...                 # ai_chat サービスでのみ必要
Dify_baseurl=...
```

`discord_config.json` はサーバーごとの挙動（コマンドプレフィックス、チャンネル/ロール名、カット番号の抽出方法など）を制御します。具体的な項目についてはボット側のソースコードを参照してください。

### 2. テンプレートを実際の `docker-compose.yml` にする

`docker-compose_yml.template` には、本番運用の前に埋める必要があるプレースホルダーが含まれています。

```bash
cp docker-compose_yml.template docker-compose.yml
```

`docker-compose.yml` 内で、以下の2種類のプレースホルダーを編集します。

**a. Gitのアイデンティティ - `###` のプレースホルダー（`bot`サービスのみ）**

すべての提出・承認はGitコミットとして記録されます。Gitがコミットを作成するにはauthor/committerのアイデンティティが必要です。これはコミットメッセージ内に格納される `submitter_name`（提出者名）や `reviewer_name`（レビュアー名）とは別物です。ボットのプロセス自体を表す固定のアイデンティティを設定してください。

```yaml
environment:
  - SHELLARC_PROJECT_CTX
  - GIT_AUTHOR_NAME=ShellArc Bot
  - GIT_AUTHOR_EMAIL=shellarc-bot@yourproject.local
  - GIT_COMMITTER_NAME=ShellArc Bot
  - GIT_COMMITTER_EMAIL=shellarc-bot@yourproject.local
```

**b. 永続化ボリューム - `〜_in_code:〜_in_server` のプレースホルダー**

これらはそれぞれ `<ホスト側のパスまたは名前付きボリューム>:<コンテナ側のパス>` のペアです。左側はデータが実際に存在する場所（コンテナを再ビルドしてもデータが消えないようにする）、右側はコンテナ側が期待するパスです。

| プレースホルダー | 使用サービス | 保存内容 | コンテナ側パスが一致すべき設定 |
|---|---|---|---|
| `version_management_dir_in_code:actual_version_management_dir_in_server` | `bot`, `itemi_action`, `ai_chat` | 提出・承認状態を保持するGitリポジトリ（`Git_IO`） | `project_settings.json` の `git_repo_local` |
| `itemi_action_dir_in_code:itemi_action_dir_in_server` | `itemi_action` のみ | リマインダースケジューラ（`ShellArc_ScheduleManager`）の永続化データ | `discord_config.json` の `schedule_path` |
| `.config_dir_in_code:.config_dir_in_server` | `itemi_action` のみ | コンテナ内のLinux標準の `~/.config` ディレクトリ。`platformdirs`/`keyring`（`pyproject.toml`参照）などのライブラリが認証情報やキャッシュの永続化に使用する | コンテナ内ユーザーの `~/.config`（rootで実行している場合は `/root/.config` など） |

例（`project_settings.json` で `"git_repo_local": "/data/git_repo"` と設定している場合）：

```yaml
services:
  bot:
    volumes:
      - ${SHELLARC_PROJECT_CTX}:${SHELLARC_PROJECT_CTX}
      - shellarc_git_data:/data/git_repo

  itemi_action:
    volumes:
      - ${SHELLARC_PROJECT_CTX}:${SHELLARC_PROJECT_CTX}
      - shellarc_git_data:/data/git_repo
      - shellarc_scheduler_data:/data/schedule
      - shellarc_config:/root/.config
# ...
volumes:
  shellarc_git_data:
  shellarc_scheduler_data:
  shellarc_config:
```

**重要**：Gitリポジトリ用のボリュームは、3つのサービスすべてで**同じボリューム・同じコンテナ側パス**をマウントする必要があります。`bot` / `itemi_action` / `ai_chat` がそれぞれ異なるボリュームやパスを使ってしまうと、各サービスが別々の（同期されていない）リポジトリのコピーを見てしまうことになります。

### 3. プロジェクトコンテキストを指定する

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_ctx
```

### 4. Docker Composeで3つのボットを起動する

```bash
docker compose up -d --build
```

これにより `bot` / `itemi_action` / `ai_chat` の3つのコンテナがビルド・起動されます。いずれもプロジェクトコンテキストディレクトリをマウントし、同一のGitバージョン管理用ボリュームを共有するため、3つのボットは常に同じパイプライン状態を参照します。

### 5. Discord上で使う

```
..up            # ファイルを添付し、ドロップダウンでコンポーネントを選び、確認するだけ
..appr          # コンポーネントを選び、「確定」または「要修正」を選択
..dl 0          # 最新の承認済みテイクをダウンロード
..history modeling 5    # 「modeling」の直近5件の提出履歴
```

これだけで、Pythonのコードを一切書かずに「提出 → レビュー → 進捗管理」の一連の流れが完結します。

---

## 🛠️ shellarc_devkit - 補助ツール群

Discordフロントエンドとは別に、`shellarc_devkit` にはプロジェクトのセットアップ・保守を助けるいくつかの単体スクリプトが含まれています。いずれもDiscordボットの稼働状態に依存せず利用できます。

| スクリプト | 内容 |
|---|---|
| `project_init_cli.py` | 新規プロジェクトのセットアップを対話式で行うウィザード。Gitリポジトリの初期化（`Git_IO.make_proj_repo`）、スプレッドシートへの疎通確認を行い、希望すれば新規スプレッドシートにヘッダー行とカット番号列も自動で書き込みます。 |
| `cloud_access_check.py` | Firebase・Cloudflare R2・Google Spreadsheetへの疎通を一度にチェックします。デプロイ前の確認や、パイプラインの一部が突然反応しなくなった際の一次切り分けに便利です。 |
| `backup_on_local.py` + `init_settings.sh` | チームメンバーが各自の端末（または共有端末）で実行し、R2に新しく提出されたカット素材をローカルフォルダに取り込むためのバックアップバッチです。メインパイプラインとは独立した、個人用の保険として機能します。 |

### ローカルバックアップバッチのセットアップ

これは中央で一括運用するものではなく、各メンバーに個別に配布して使うことを想定しています。

1. `backup_on_local.py`・`init_settings.sh`・`requirements.txt`・（R2の認証情報を含む）`.env` を同じフォルダにまとめて配置します（例：`~/shellarc_backup/`）。
2. セットアップスクリプトを一度だけ実行します。
   ```bash
   bash init_settings.sh
   ```
   これにより専用のvirtualenvが作成され、依存パッケージがインストールされ、シェルの設定ファイルに `SHELLARC_LOCAL_BACKUP`（そのフォルダの親ディレクトリ）が登録され、`nuru` というエイリアスが設定されます。
3. シェルを再読み込み（`source ~/.zshrc`）した後は、いつでも次のコマンドを実行するだけです。
   ```bash
   nuru
   ```
   前回のバックアップ以降に提出された分だけを取り込みます。最終バックアップ時刻は `backup_config.json` に記録されるため、毎回差分のみが取得されます。

---

## 自分でフロントエンドを作る場合

Discordを使いたくない場合、上記のクイックスタートは同じライブラリの上に作られたフロントエンドの一例に過ぎません。Slackボット・Webダッシュボード・CLIなど独自のフロントエンドを作る場合は、プロジェクト設定・スプレッドシートのマッピング・各サービスの認証情報をまとめたプロジェクトコンテキストディレクトリの用意と、初回のみのGitリポジトリ初期化が必要です--この初期化は、上記の `project_init_cli.py` を使えば対話式で進められます。それが済めば、日常的な利用は `operations` 配下の各クラスだけで完結します。

具体的な設定ファイルの形式・全APIの詳細仕様（引数・返り値・送出例外）については、設計ドキュメントおよびAPI仕様書を参照してください。

- [ARCHITECTURE_jpn.md](./ARCHITECTURE_jpn.md) - 内部設計・データモデル・処理フロー
- [shellarc_core_api_guide.md](../shellarc_core_api_guide.md) - 完全なAPI仕様書