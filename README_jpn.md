# shellarc_core

### For English version, please refer to [README.md](./README.md)

`shellarc_core` は、アニメ・映像制作の**カット管理**を行うパイプラインバックエンドフレームワークです。以下のクラウドサービスを組み合わせて、カット素材のバージョン管理・レビューフロー・進捗管理を自動化します。

| サービス | 用途 |
|---|---|
| **Cloudflare R2**（S3互換） | 素材ファイルのストレージ |
| **Google Spreadsheet** | 進捗・担当者管理台帳 |
| **Git**（ローカル＋リモート） | カットごとのバージョン管理・承認フロー |
| **Notion** | レイアウト画像（絵コンテ）の管理 |
| **Firebase Firestore** | 汎用データベース（認証情報管理など） |

内部設計・レイヤー構造・データフローの詳細は [ARCHITECTURE_jpn.md](./DOCS_jpn/ARCHITECTURE_jpn.md) を参照してください。このREADMEは「どう使うか」に焦点を当てています。

---

## 目次

- [基本概念](#基本概念)
- [セットアップ](#セットアップ)
- [クイックスタート](#クイックスタート)
- [ディレクトリ構成](#ディレクトリ構成)
- [例外処理](#例外処理)
- [参考: ユースケース一覧](#参考-ユースケース一覧)

---

## 基本概念

| 用語 | 説明 |
|---|---|
| カット (cut) | 映像制作の最小作業単位。`cut_num`（int）で識別 |
| コンポーネント (component) | カットを構成する作業種別（例: `modeling`, `texturing`） |
| テイク (take) | コンポーネントの提出バージョン。Gitコミットに対応 |
| ペンディング (pending) | レビュー待ちの提出状態。Gitの `pending` ブランチで管理 |

---

## セットアップ

### 1. 環境変数

`SHELLARC_PROJECT_CTX`（必須）にプロジェクトコンテキストディレクトリの絶対パスを設定します。

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_context
```

### 2. プロジェクトコンテキストディレクトリの用意

このディレクトリに以下の3ファイルを配置します。

```
$SHELLARC_PROJECT_CTX/
├── project_settings.json   # プロジェクト設定（バケット名・コンポーネント定義など）
├── spreadsheet_map.json    # スプレッドシートのセル座標マッピング
└── .env                    # 各サービスの認証情報
```

**`project_settings.json` の例：**

```json
{
  "project_name": "MyProject",
  "bucket_name": "my-r2-bucket",
  "collection_name": "my-collection",
  "spreadsheet_key": "GOOGLE_SPREADSHEET_KEY",
  "cut_num": 100,
  "git_repo_local": "/path/to/local/git/repo",
  "local_backup_dir": "/path/to/backup",
  "notion_dbid": "NOTION_DATABASE_ID",
  "components": {
    "modeling": {
      "format": "blend",
      "naming_section": 3,
      "name_component_1": "-cut",
      "name_component_2": "modeling",
      "name_component_3": "-take"
    },
    "texturing": {
      "format": "png|zip",
      "naming_section": 2,
      "name_component_1": "-cut",
      "name_component_2": "-take"
    }
  }
}
```

**`spreadsheet_map.json` の例：**

```json
{
  "vert_offset_0": 2,
  "items_0": {
    "modeling_PIC": 3,
    "modeling_progress": 4,
    "texturing_PIC": 5,
    "texturing_progress": 6,
    "layout_progress": 7
  }
}
```

**`.env` に必要な変数：**

```dotenv
# Google Cloud Platform (Spreadsheet)
GCP_type=service_account
GCP_project_id=...
GCP_private_key_id=...
GCP_private_key=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
GCP_client_email=...
GCP_client_id=...
GCP_auth_uri=https://accounts.google.com/o/oauth2/auth
GCP_token_uri=https://oauth2.googleapis.com/token
GCP_auth_provider_x509_cert_url=https://www.googleapis.com/oauth2/v1/certs
GCP_client_x509_cert_url=...
GCP_universe_domain=googleapis.com

# Cloudflare R2
CloudflareR2_access_key_id=...
CloudflareR2_secret_access_key=...
CloudflareR2_jurisdiction_specific_endpoints=https://...r2.cloudflarestorage.com

# Firebase Firestore
firebase_type=service_account
firebase_project_id=...
firebase_private_key_id=...
firebase_private_key=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
firebase_client_email=...
firebase_client_id=...
firebase_auth_uri=https://accounts.google.com/o/oauth2/auth
firebase_token_uri=https://oauth2.googleapis.com/token
firebase_auth_provider_x509_cert_url=https://www.googleapis.com/oauth2/v1/certs
firebase_client_x509_cert_url=...
firebase_universe_domain=googleapis.com

# Notion
Notion_token=secret_...
```

### 3. 新規プロジェクトのGitリポジトリ初期化（初回のみ）

```python
from shellarc_core.cloudio.io_git import Git_IO

git_io = Git_IO()
await git_io.make_proj_repo({
    "cut_num": 100,
    "components": {
        "modeling": {"format": "blend"},
        "texturing": {"format": "png|zip"}
    }
})
```

これにより `git_repo_local` に `main` / `pending` の2ブランチを持つリポジトリと、全カット分の `stage/cut{N}/` ディレクトリが作成されます。

---

## クイックスタート

### 素材の提出（アップロード）

```python
from shellarc_core.operations.uploader import ShellArc_Upload

uploader = ShellArc_Upload(cut_num=5, working_component="modeling")

await uploader.upload_file(
    file={"cut5_model_v1.blend": file_bytes},
    submitter_name="YamadaTaro",
    message="初回提出"
)
```

### 素材のダウンロード

```python
from shellarc_core.operations.requesting import ShellArc_Request

req = ShellArc_Request(cut_num=5, requesting_component="modeling")

# "0" = 最新確定版(main) / "-1" = 作業中(pending) / それ以外 = 特定コミットID
path_or_url, filename, type_indicator = await req.download_material("0")

if type_indicator == "url":
    print(f"ダウンロードURL: {path_or_url}")
else:
    with open(path_or_url, "rb") as f:
        file_bytes = f.read()
    import os
    os.unlink(path_or_url)  # 一時ファイルなので使用後に削除
```

### レビュー（承認・却下）

```python
from shellarc_core.operations.reviewing import ShellArc_Review

review = ShellArc_Review(cut_num=5, reviewing_component="modeling")
await review.pending_action(
    reviewer_name="DirectorSato",
    is_approve=True,
    message="問題なし、OKです"
)
```

### 担当者登録

```python
from shellarc_core.operations.register import ShellArc_Register

register = ShellArc_Register()
await register.register_work(
    registering_person="YamadaTaro",
    registering_component="modeling",
    registering_cut=5
)
```

### 提出履歴の照会

```python
from shellarc_core.operations.query import ShellArc_Query

history = await ShellArc_Query.get_history(
    cut_num=5,
    component="modeling",
    max_length=10
)
# → {"abc1234": "20240101120000 YamadaTaro 初回提出", ...}
```

その他のユースケース（署名付きURLでの大容量ファイルアップロード、絵コンテのアップロード/ダウンロードなど）は [ARCHITECTURE_jpn.md の主要な処理フロー](./DOCS_jpn/ARCHITECTURE_jpn.md#9-主要な処理フロー) を参照してください。

---

## ディレクトリ構成

```
shellarc_core/
├── cfg/          # 設定ファイル(JSON)の読み込み
├── auth/         # 各クラウドサービスへの認証
├── cloudio/      # 各クラウドサービスへの実際のCRUD操作
├── utils/        # ローカルファイル操作ユーティリティ
├── exception/    # 例外クラス群
└── operations/   # ビジネスロジック（ライブラリ利用側の実装例）
```

各モジュールの詳細な責務は [ARCHITECTURE_jpn.md](./DOCS_jpn/ARCHITECTURE_jpn.md#2-レイヤードアーキテクチャ) にまとめています。

---

## 例外処理

`shellarc_core` の例外は2系統に分かれます。

| 系統 | 基底クラス | 特徴 |
|---|---|---|
| ユーザー起因 | `ShellArcException`（`exception/user_exception.py`） | `frontend_msg` をそのままUIに表示できる |
| システム起因 | `ShellArcError`（`exception/structure_error.py`） | `frontend_msg` は固定文言（`"技術班にご連絡ください : {error_code.name}"`） |

代表的なユーザー起因の例外：`SA_DataNotExist`, `SA_InvalidUserQuery`, `SA_InvalidRequestObj`, `SA_EditingRejection`

詳細な例外一覧・エラーコード表は [ARCHITECTURE_jpn.md の例外設計](./DOCS_jpn/ARCHITECTURE_jpn.md#8-例外設計) を参照してください。

---

## 参考: ユースケース一覧

| ユースケース | 使用クラス |
|---|---|
| 素材の提出 | `operations.uploader.ShellArc_Upload` |
| 署名付きURLでの大容量アップロード | `operations.uploader.ShellArc_Upload.get_upload_page` |
| 素材のダウンロード | `operations.requesting.ShellArc_Request` |
| レビュー（承認・却下） | `operations.reviewing.ShellArc_Review` |
| 担当者登録 | `operations.register.ShellArc_Register` |
| 絵コンテのアップロード・ダウンロード | `operations.storyboard.ShellArc_Storyboard` |
| 提出・承認履歴の照会 | `operations.query.ShellArc_Query` |
| 新規プロジェクトの初期化 | `cloudio.io_git.Git_IO.make_proj_repo` |

---

*このREADMEおよび ARCHITECTURE.md は `shellarc_core_api_guide.md` の内容をもとに作成されています。全公開インターフェースの詳細な仕様（引数の型・送出例外・返り値の形式など）は元のAPIガイドを参照してください。*