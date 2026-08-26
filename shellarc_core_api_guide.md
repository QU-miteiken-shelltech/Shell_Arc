# shellarc_core ライブラリ リファレンスドキュメント

> **目的** : このドキュメントを読んだAIエージェントが `shellarc_core` をスタンドアロンライブラリとして利用し、新しいアプリケーションを独力で実装できることを目標としています。

---

## 目次

1. [ライブラリ概要](#1-ライブラリ概要)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [環境変数・設定ファイル](#3-環境変数設定ファイル)
4. [例外システム](#4-例外システム)
5. [設定レイヤー (cfg)](#5-設定レイヤー-cfg)
6. [認証レイヤー (auth)](#6-認証レイヤー-auth)
7. [クラウドIOレイヤー (cloudio)](#7-クラウドioレイヤー-cloudio)
8. [ユーティリティ (utils)](#8-ユーティリティ-utils)
9. [ビジネスロジックレイヤー (process)](#9-ビジネスロジックレイヤー-process)
10. [Gitコミットメッセージ仕様](#10-gitコミットメッセージ仕様)
11. [典型的なユースケースとフロー](#11-典型的なユースケースとフロー)

---

## 1. ライブラリ概要

`shellarc_core` は、アニメ・映像制作のカット管理を行うバックエンドライブラリです。以下のクラウドサービスを組み合わせて、カット素材のバージョン管理・レビューフロー・進捗管理を自動化します。

| サービス | 用途 |
|---|---|
| **Cloudflare R2** (S3互換) | 素材ファイルのストレージ |
| **Google Spreadsheet** | 進捗・担当者管理台帳 |
| **Git (ローカル+リモート)** | カットごとのバージョン管理・承認フロー |
| **Notion** | レイアウト画像(絵コンテ)の管理 |
| **Firebase Firestore** | 汎用データベース（認証情報管理など） |

**主なドメイン概念：**

- **カット (cut)** : 映像制作の最小作業単位。`cut_num` (int) で識別する。
- **コンポーネント (component)** : カットを構成する作業種別（例: `modeling`, `texturing`）。文字列で識別する。
- **テイク (take)** : コンポーネントの提出バージョン。Gitコミットに対応する。
- **ペンディング (pending)** : レビュー待ちの提出状態。Gitの `pending` ブランチで管理される。

---

## 2. ディレクトリ構成

```
shellarc_core/
├── cfg/
│   ├── cfg_io.py              # プロジェクト設定JSONの読み込み
│   └── spreadsheet_map_io.py  # スプレッドシートマッピングの読み込み
├── auth/
│   ├── access_database.py     # Firebase Firestore認証
│   ├── access_r2.py           # Cloudflare R2認証
│   ├── access_notion.py       # Notion API認証
│   └── access_spread_sheet.py # Google Sheets認証
├── cloudio/
│   ├── io_spreadsheet.py      # Google Spreadsheet CRUD操作
│   ├── io_git.py              # Gitリポジトリ操作（非同期）
│   ├── io_r2.py               # Cloudflare R2ファイル操作
│   └── io_notion.py           # Notion画像操作
├── utils/
│   └── file_operation.py      # ローカルファイル操作ユーティリティ
├── exception/
│   ├── exceptions.py          # 例外タイプ列挙
│   ├── user_exception.py      # ユーザー起因の例外クラス
│   └── structure_error.py     # システム起因の例外クラス
└── process/                # ※以下はライブラリ利用側のビジネスロジック例
    ├── uploader.py            # ファイルアップロード処理
    ├── requesting.py          # ファイルダウンロード処理
    ├── reviewing.py           # レビュー（承認/却下）処理
    ├── register.py            # 担当者登録処理
    ├── storyboard.py          # 絵コンテ操作処理
    └── query.py               # 情報照会処理
```

---

## 3. 環境変数・設定ファイル

### 3-1. 環境変数

`SHELLARC_PROJECT_CTX` (必須) : プロジェクトコンテキストディレクトリの絶対パスを指定する。このディレクトリ内に以下のファイルが必要。

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_context
```

### 3-2. プロジェクトコンテキストディレクトリの構成

```
$SHELLARC_PROJECT_CTX/
├── project_settings.json   # プロジェクト設定
├── spreadsheet_map.json    # スプレッドシートセルマッピング
└── .env                    # 各サービスの認証情報
```

### 3-3. `project_settings.json` のスキーマ

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

**フィールド説明：**

| フィールド | 型 | 説明 |
|---|---|---|
| `project_name` | string | プロジェクト名 |
| `bucket_name` | string | Cloudflare R2バケット名 |
| `collection_name` | string | R2内のコレクション（フォルダ）名。ファイルパスの先頭に使用される |
| `spreadsheet_key` | string | Google SpreadsheetのキーID |
| `cut_num` | int | プロジェクトの総カット数 |
| `git_repo_local` | string | Gitローカルリポジトリの絶対パス |
| `local_backup_dir` | string | ローカルバックアップディレクトリのパス |
| `notion_dbid` | string | NotionデータベースのID |
| `components` | object | コンポーネント定義のマップ |
| `components.{name}.format` | string | 許可するファイル拡張子。複数の場合は`\|`区切り（例: `"png\|zip"`）|
| `components.{name}.naming_section` | int | ファイル命名規則のセクション数 |
| `components.{name}.name_component_N` | string | N番目の命名セクション。`-cut`はカット番号、`-take`はテイク番号に展開される |

### 3-4. `spreadsheet_map.json` のスキーマ

```json
{
  "vert_offset_0": 2,
  "items_0": {
    "modeling_PIC": 3,
    "modeling_progress": 4,
    "texturing_PIC": 5,
    "texturing_progress": 6,
    "layout_progress": 7
  },
  "vert_offset_1": 2,
  "items_1": {
    "some_item": 2
  }
}
```

**フィールド説明：**

| フィールド | 型 | 説明 |
|---|---|---|
| `vert_offset_{page_idx}` | int | ページ `page_idx` において、カット番号1が対応するスプレッドシートの行番号。`row = cut_num + vert_offset` で行を算出する |
| `items_{page_idx}` | object | ページ `page_idx` における、アイテム名から列番号(1-based)へのマッピング |

**慣習的なアイテム名：**
- `{component}_PIC` : そのコンポーネントの担当者名
- `{component}_progress` : 進捗状態（`"作業中"`, `"完了"` 等）
- `layout_progress` : レイアウト（絵コンテ）の進捗

### 3-5. `.env` のスキーマ

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

### 3-6. Gitリポジトリのディレクトリ構造

`git_repo_local` が指すGitリポジトリは以下の構造を持つ。`Git_IO.make_proj_repo()` で初期化される。

```
{git_repo_local}/
├── project_main.json        # カット別コンポーネント定義
└── stage/
    ├── cut1/
    │   ├── modeling.json    # modelingコンポーネントの現在のステート
    │   ├── .sa_pending_modeling   # ペンディング状態を示すファイル（存在する場合のみ）
    │   └── texturing.json
    ├── cut2/
    │   └── ...
    └── ...
```

**`project_main.json` のスキーマ：**

```json
{
  "cut_num": 100,
  "common": {
    "modeling": ["blend"],
    "texturing": ["png", "zip"]
  },
  "cut5": {
    "modeling": ["blend"]
  }
}
```

`common` は全カットのデフォルトコンポーネント定義。特定カット番号のキーが存在する場合はそちらが優先される。

**コンポーネントJSONのスキーマ（通常の提出）：**

```json
{
  "creator": "YamadaTaro",
  "fileindex": "cut1_modeling_abc123_20240101120000"
}
```

**コンポーネントJSONのスキーマ（リポイント時）：**

```json
{
  "repointer": 3
}
```

`repointer` が存在する場合、そのカットのデータは指定カット番号のデータを参照する（別カットの素材を流用する機能）。

---

## 4. 例外システム

### 4-1. `exceptions.py` — `SA_ExceptionType`

全例外の分類を表す `Enum`。直接使用することは少なく、各例外クラスの内部で参照される。

| 値 | 意味 |
|---|---|
| `DATA_NOTEXIST_ERROR` | 参照しようとしたデータが存在しない |
| `INVALID_USER_QUERY` | ユーザーからの不正なリクエスト |
| `INVALID_REQUEST_OBJ` | 存在しないオブジェクトへのリクエスト |
| `EDIT_REJECT` | 意図しない上書きを防ぐための拒否 |
| `SAPYC_SYNTAX_ERROR` | 独自構文エラー |
| `STRUCT_ERROR` | プロジェクト設定の致命的な構造エラー |
| `SYS_REQUEST_ITEM_NOTEXIST` | システムが存在しないアイテムを要求 |
| `COMMUN_ERROR` | 外部サービスとの通信エラー |
| `AUTH_ERROR` | 外部サービスへの認証エラー |
| `LOCAL_IO_ERROR` | サーバーローカルのファイルIOエラー |
| `INT_SYNTAX_EREOR` | 内部システムの構文エラー |

### 4-2. `user_exception.py` — ユーザー起因の例外

これらの例外は **ユーザーの操作が原因** で発生する。`frontend_msg` フィールドにユーザーへ表示するメッセージが入っており、アプリはこれをそのままUIに返すことを想定している。

#### `ShellArcException` (基底クラス)

```python
ShellArcException(
    error_log: str,           # ログに記録するエラー詳細（タイムスタンプが自動付与される）
    error_type: SA_ExceptionType,
    frontend_msg: str | None  # ユーザー向けメッセージ。Noneの場合はerror_logと同一
)
```

プロパティ：
- `frontend_msg` (str) : ユーザーへ返すメッセージ

#### `SA_DataNotExist`

データが存在しない場合に送出。

```python
SA_DataNotExist(error_log: str, frontend_msg: str | None = None)
```

#### `SA_InvalidUserQuery`

ユーザーが不正なリクエスト（不正なファイル形式など）を送信した場合に送出。

```python
SA_InvalidUserQuery(error_log: str, frontend_msg: str | None = None)
```

#### `SA_InvalidRequestObj`

存在しないオブジェクト（未提出のカットなど）を参照した場合に送出。

```python
SA_InvalidRequestObj(error_log: str, frontend_msg: str | None = None)
```

#### `SA_EditingRejection`

意図しないデータ上書きを防ぐために送出（担当者が既に登録済みの場合など）。

```python
SA_EditingRejection(error_log: str, frontend_msg: str | None = None)
```

#### `SA_SapycSyntaxError`

独自構文エラー。

```python
SA_SapycSyntaxError(error_log: str, frontend_msg: str | None = None)
```

### 4-3. `structure_error.py` — システム起因の例外

これらの例外は **設定ミス・サービス障害など、システム側の問題** で発生する。`frontend_msg` は常に `"技術班にご連絡ください : {error_code.name}"` となる。

#### `SA_ErrorCode`

エラーコードの `Enum`。

| コード | 意味 |
|---|---|
| `SA_3000` | HTTPリクエストエラー |
| `SA_4001` | 設定ファイルパスが存在しない |
| `SA_4002` | 設定ファイルの要求キーが存在しない |
| `SA_4101` | スプレッドシートマップパスが存在しない |
| `SA_4102` | スプレッドシートマップの座標が未設定 |
| `SA_5001` | DBに情報が見つからない |
| `SA_5101` | アップロードファイルがNone |
| `SA_6000` | Gitリモート通信エラー |
| `SA_6001` | project_main.jsonに必須データが欠如 |
| `SA_6002` | コンポーネントJSONのキーエラー |
| `SA_7000` | 不正なパラメータ |
| `SA_8000` | サーバーローカルIOエラー |
| `SA_8001` | 外部サービスとの通信エラー |
| `SA_8002` | Gitエラー |
| `SA_9000` | 認証エラー |
| `SA_9001` | `.env`ファイルが存在しない |

#### `ShellArcError` (基底クラス)

```python
ShellArcError(
    error_log: str,
    error_type: SA_ExceptionType,
    error_code: SA_ErrorCode,
    is_fatal: bool   # Trueの場合ログに"FATAL"が付与される
)
```

#### サブクラス一覧

| クラス名 | 対応エラーコード例 | `is_fatal` |
|---|---|---|
| `SA_ProjStructError` | SA_4001, SA_4002, SA_6001, SA_6002 | True |
| `SA_RequestItemError` | SA_5001, SA_5002 | False |
| `SA_CommunicationError` | SA_3000, SA_8001 | True |
| `SA_AuthError` | SA_9000, SA_9001 | True |
| `SA_LocalIOError` | SA_8000, SA_8002 | True |
| `SA_InternalSyntaxError` | SA_7000 | True |

---

## 5. 設定レイヤー (cfg)

### 5-1. `cfg_io.py`

#### `Cfg_item` (Enum)

`get_cfg_setting()` の引数として使用する列挙型。

| 値 | JSONキー | 説明 |
|---|---|---|
| `PROJ_NAME` | `"project_name"` | プロジェクト名 |
| `BUCKET_NAME` | `"bucket_name"` | R2バケット名 |
| `COLL_NAME` | `"collection_name"` | コレクション名 |
| `SPREADSHEET_KEY` | `"spreadsheet_key"` | スプレッドシートキー |
| `CUTNUM` | `"cut_num"` | 総カット数 |
| `COMPONENT` | `"components"` | コンポーネント定義 |
| `GIT_LREPO` | `"git_repo_local"` | Gitリポジトリのパス |
| `LOCAL_BACKUP` | `"local_backup_dir"` | バックアップディレクトリ |
| `NOTION_DBID` | `"notion_dbid"` | NotionデータベースID |

#### `Cfg_IO`

```python
Cfg_IO()
```

コンストラクタで `$SHELLARC_PROJECT_CTX/project_settings.json` を読み込む。

---

##### `get_cfg_setting(*args) -> Any`

JSONの階層を可変長引数でたどって値を取得する。

| 引数 | 型 | 説明 |
|---|---|---|
| `*args` | `Cfg_item \| str` (可変長) | JSONのキーパス。`Cfg_item` を渡すとそのvalueに変換される |

**返り値** : `Any` — 指定されたパスのJSON値。キーが存在しない場合は `None`。

**例：**

```python
cfg = Cfg_IO()

# バケット名を取得
bucket = cfg.get_cfg_setting(Cfg_item.BUCKET_NAME)
# → "my-r2-bucket"

# modelingのフォーマットを取得
fmt = cfg.get_cfg_setting(Cfg_item.COMPONENT, "modeling", "format")
# → "blend"

# 生の文字列キーでもアクセス可能
key = cfg.get_cfg_setting("spreadsheet_key")
```

**送出例外：**
- `SA_ProjStructError(SA_4001)` : 設定ファイルが存在しない
- `SA_ProjStructError(SA_4002)` : 中間キーがdictでない（キーパスが誤っている）

---

### 5-2. `spreadsheet_map_io.py`

#### `SpreadsheetMap_IO`

```python
SpreadsheetMap_IO()
```

コンストラクタで `$SHELLARC_PROJECT_CTX/spreadsheet_map.json` を読み込む。

---

##### `get_cell_coord(cut_num, item, page_idx=0) -> tuple[int, int]`

カット番号とアイテム名から、スプレッドシート上のセル座標（行, 列）を返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `item` | `str` | アイテム名（例: `"modeling_PIC"`） |
| `page_idx` | `int` | スプレッドシートのページインデックス（デフォルト: `0`）|

**返り値** : `tuple[int, int]` — `(row_idx, col_idx)` の形式。いずれも1-based。

**送出例外：**
- `SA_ProjStructError(SA_4102)` : `vert_offset` または列インデックスが未設定

---

##### `get_vert_offset(page_idx=0) -> int`

ページの垂直オフセット値を返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）|

**返り値** : `int` — 垂直オフセット値。`row = cut_num + vert_offset` でスプレッドシートの行番号を計算できる。

---

## 6. 認証レイヤー (auth)

認証レイヤーの各クラスは、`.env` から認証情報を読み込み、サービスクライアントを生成する。通常、上位のIOクラスが内部で使用するため、直接呼び出す機会は少ない。

### 6-1. `access_r2.py` — `Cloudflare_R2_service_Access`

```python
Cloudflare_R2_service_Access()
```

`.env` から `CloudflareR2_*` 変数を読み込み、boto3 S3クライアントを初期化する。

**プロパティ：**

##### `s3_client -> boto3.client`

初期化済みの boto3 S3クライアントインスタンスを返す。

**送出例外：**
- `SA_AuthError(SA_9001)` : `.env` ファイルが存在しない
- `SA_AuthError(SA_9000)` : R2への接続に失敗

---

### 6-2. `access_spread_sheet.py` — `AccessSpreadSheet`

```python
AccessSpreadSheet(spreadsheet_key: str)
```

`.env` から `GCP_*` 変数を読み込み、gspread クライアントを初期化する。一時ファイルにサービスアカウントJSONを書き出し、認証後に削除するという方式を取っている。

| 引数 | 型 | 説明 |
|---|---|---|
| `spreadsheet_key` | `str` | Google SpreadsheetのキーID |

---

##### `spreadsheet_obj(page_idx: int) -> gspread.Worksheet`

指定したページのワークシートオブジェクトを返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `page_idx` | `int` | ワークシートのインデックス（0-based）|

**返り値** : `gspread.Worksheet` — gspreadのワークシートオブジェクト

**送出例外：**
- `SA_AuthError(SA_9001)` : `.env` ファイルが存在しない
- `SA_AuthError(SA_9000)` : Google Sheets APIへの認証に失敗

---

### 6-3. `access_database.py` — `AccessDB`

```python
AccessDB()
```

`.env` から `firebase_*` 変数を読み込み、Firebase Admin SDK で Firestore クライアントを初期化する。

**プロパティ：**

##### `database -> firestore.Client`

Firestore クライアントインスタンスを返す。

**送出例外：**
- `SA_AuthError(SA_9001)` : `.env` ファイルが存在しない
- `SA_AuthError(SA_9000)` : Firebase認証に失敗

---

### 6-4. `access_notion.py` — `Notion_Access`

```python
Notion_Access()
```

`.env` から `Notion_token` を読み込み、Notion クライアントを初期化する。

**プロパティ：**

##### `get_notion_client -> notion_client.Client`

Notion クライアントインスタンスを返す。

---

## 7. クラウドIOレイヤー (cloudio)

### 7-1. `io_spreadsheet.py` — `GCP_IO`

Google Spreadsheetへの読み書き・セル色変更を担当するクラス。内部で `AccessSpreadSheet` と `SpreadsheetMap_IO` を使用する。

```python
GCP_IO()
```

コンストラクタで `Cfg_IO` からスプレッドシートキーを取得し、`AccessSpreadSheet` を初期化する。

---

##### `get_info(info_type, cut_num, page_idx=0) -> str | None`

スプレッドシートの特定セルの値を取得する。

| 引数 | 型 | 説明 |
|---|---|---|
| `info_type` | `str` | アイテム名（例: `"modeling_PIC"`, `"modeling_progress"`）|
| `cut_num` | `int` | カット番号 |
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）|

**返り値** : `str | None` — セルの値。空セルは `None`。

---

##### `update_info(info_type, cut_num, new_value, page_idx=0) -> None`

スプレッドシートの特定セルを更新する。

| 引数 | 型 | 説明 |
|---|---|---|
| `info_type` | `str` | アイテム名 |
| `cut_num` | `int` | カット番号 |
| `new_value` | `str` | 書き込む値 |
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）|

**返り値** : `None`

---

##### `color_cell(info_type, cut_num, target_color, page_idx=0) -> None`

スプレッドシートの特定セルの背景色を変更する。

| 引数 | 型 | 説明 |
|---|---|---|
| `info_type` | `str` | アイテム名 |
| `cut_num` | `int` | カット番号 |
| `target_color` | `tuple[float, float, float]` | RGB各チャンネルの色値（0.0〜1.0の範囲）。例: `(1, 1, 0)` = 黄色、`(0, 1, 0)` = 緑 |
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）|

**返り値** : `None`

---

##### `spreadsheet_cache` (property) `-> list[list]`

スプレッドシート全体の値をキャッシュして返す。同一インスタンス内では初回アクセス時のみAPIを呼び出す。

| 引数 | 型 | 説明 |
|---|---|---|
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）※現在の実装ではプロパティのため引数渡し不可 |

**返り値** : `list[list]` — 全行・全列の値をネストしたリスト。インデックスは0-based。

---

### 7-2. `io_git.py` — `Git_IO` と関連クラス

Gitリポジトリを操作し、カットのバージョン管理・承認フローを実現するクラス。**クラス変数 `_git_lock = asyncio.Lock()`** によって、書き込み系メソッド (`update_data`, `pend_data`, `repoint_data`) はクラス全体で排他制御されており、非同期環境での同時実行が安全に行われる。`absorb_data` はロックを取得しない点に注意。

#### 関連 Enum / データクラス

##### `GitCommands` (StrEnum)

git コマンド文字列の定数。内部メソッドが `asyncio.create_subprocess_exec` に渡す引数として使用する。

| 値 | git コマンド |
|---|---|
| `SHOW` | `"show"` |
| `COMMIT` | `"commit"` |
| `CHECKOUT` | `"checkout"` |
| `MERGE` | `"merge"` |
| `PUSH` | `"push"` |
| `ADD` | `"add"` |
| `INIT` | `"init"` |
| `LOG` | `"log"` |
| `STATUS` | `"status"` |

##### `SA_CommitType` (StrEnum)

コミットメッセージの先頭フィールドに埋め込むアクションの種別。`get_log()` のフィルタリングキーとしても使用される。

| 値 | 意味 |
|---|---|
| `SUBMIT` | 素材の新規提出 |
| `APPROVE` | 提出の承認 |
| `DECLINE` | 提出の却下 |
| `REPOINT` | 別カットへの参照付け替え |
| `ABSORPTION` | 別カットのデータを取り込み |

##### `ShellArcGitBranch` (StrEnum)

Gitブランチ名の定数。

| 値 | 文字列 | 意味 |
|---|---|---|
| `PENDING` | `"pending"` | 作業中・レビュー待ちのデータが存在するブランチ |
| `MAIN` | `"main"` | 承認済みの確定データが存在するブランチ |

##### `SA_GitLogFilter` (dataclass)

`get_log()` に渡すフィルター条件。全フィールドのデフォルトは `None`（フィルタなし）。

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `commit_type` | `SA_CommitType \| str \| None` | `None` | フィルタするコミットタイプ。`None`はフィルタなし |
| `cut_num` | `int \| None` | `None` | フィルタするカット番号。`None`はフィルタなし |
| `component` | `str \| None` | `None` | フィルタするコンポーネント名。`None`はフィルタなし |
| `log_length` | `int \| None` | `None` | 返すログの最大件数。`None`は全件 |

---

#### `Git_IO`

```python
Git_IO(git_repo_local_dir: str | None = None)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `git_repo_local_dir` | `str \| None` | Gitリポジトリの絶対パス。`None` の場合は `project_settings.json` の `git_repo_local` を使用（デフォルト: `None`）|

全gitコマンドは `self.git_repo_local_dir` を `cwd` として `asyncio.create_subprocess_exec` で実行される。

---

#### 内部メソッド（動作理解のために記載）

##### `_get_timemark` (property) `-> str`

現在時刻をJST（UTC+9）で `YYYYMMDDHHMMSS` 形式の文字列として返す。コミットメッセージおよびファイルインデックス名の生成に使用される。

---

##### `_make_index_name(cut_num, component, creator_name) -> str`

R2アップロード先のファイルインデックス名を生成する。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `creator_name` | `str` | 提出者名 |

**返り値** : `str` — `cut{N}_{component}_{creator_id}_{timemark}` 形式の文字列

**生成ルール：**
- `component` 内の `_` はすべて `-` に置換される（例: `some_comp` → `some-comp`）
- `creator_id` は `creator_name` を UTF-8 エンコードして `hashlib.shake_128` にかけた **6文字の16進ダイジェスト**（`hexdigest(3)`）
- `timemark` は `_get_timemark` の値（JST, `YYYYMMDDHHMMSS`）

**例：** `cut5_modeling_a1b2c3_20240101120000`

---

##### `async _git_command(*git_cmds_param) -> asyncio.subprocess.Process`

単一のgitコマンドを非同期で実行し、プロセスオブジェクトを返す。`stdout` と `stderr` は PIPE で取得できる状態になっているが、`communicate()` の呼び出しは呼び出し元が行う。

| 引数 | 型 | 説明 |
|---|---|---|
| `*git_cmds_param` | 可変長 | gitコマンドとそのパラメータ（例: `"checkout"`, `"main"`）|

**返り値** : `asyncio.subprocess.Process`

---

##### `async _continuous_git_command(git_commands) -> None`

複数のgitコマンドを順番に実行する。いずれかのコマンドが非ゼロの終了コードを返した場合は直ちに例外を送出する。

| 引数 | 型 | 説明 |
|---|---|---|
| `git_commands` | `list[list[str]]` | 実行するgitコマンドのリスト。各要素はコマンドとパラメータのリスト（例: `[["checkout", "main"], ["add", "."]]`）|

**返り値** : `None`

**送出例外：**
- `SA_LocalIOError(SA_8002)` : いずれかのgitコマンドが失敗した場合

---

#### 公開メソッド

##### `get_components(cut_num) -> list[str]`

`project_main.json` から指定カットのコンポーネント名リストを取得する（同期メソッド）。

カット固有のキー（例: `"cut5"`）が存在する場合はそちらを、なければ `"common"` をデフォルトとして使用する。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |

**返り値** : `list[str]` — コンポーネント名のリスト（例: `["modeling", "texturing"]`）

**送出例外：**
- `SA_ProjStructError(SA_6001)` : `project_main.json` に `common` キーが存在しない

---

##### `async make_proj_repo(proj_settings) -> None`

Gitリポジトリを新規初期化し、`main` と `pending` の2ブランチを作成する。**新規プロジェクト作成時に1度だけ呼び出す**。

**処理フロー：**
1. `git_repo_local_dir` と `stage/` ディレクトリを作成
2. `project_main.json` を生成（`"common"` キーにコンポーネント情報を格納）
3. `stage/cut1/` 〜 `stage/cut{N}/` ディレクトリを全カット分作成
4. `git init -b main` → `git add .` → 初期コミット
5. `git checkout -b pending` → `git add .` → 空コミット
6. `git checkout main` に戻る

| 引数 | 型 | 説明 |
|---|---|---|
| `proj_settings` | `dict` | プロジェクト設定辞書 |

**`proj_settings` のスキーマ：**

```python
{
    "cut_num": 50,                         # 総カット数 (int)
    "components": {
        "modeling": {"format": "blend"},   # コンポーネント名: {format: 拡張子}
        "texturing": {"format": "png|zip"}
    }
}
```

**返り値** : `None`

---

##### `async get_component_info(branch, cut_num, component, commit_id=None) -> dict[str, str]`

Gitリポジトリから指定ブランチ・カット・コンポーネントのJSONを取得する。`repointer` が設定されている場合は自動的に参照先カットの情報を再帰的に取得する。

**内部処理：**
1. 指定ブランチへ `checkout`
2. `git show {commit_id_or_branch}:stage/cut{N}/{component}.json` でJSONを取得
3. JSONに `"repointer"` キーがあれば、その値のカット番号で自身を再帰呼び出し

| 引数 | 型 | 説明 |
|---|---|---|
| `branch` | `ShellArcGitBranch \| str` | 取得元ブランチ（`"pending"` または `"main"`）|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `commit_id` | `str \| None` | 特定のコミットIDを指定する場合。`None` はブランチ名をそのまま `git show` に渡す（= ブランチの最新）（デフォルト: `None`）|

**返り値** : `dict[str, str]` — コンポーネントJSONの内容。コンポーネントJSONファイルが存在しない、または `git show` が失敗した場合は空の辞書 `{}`。

通常の返り値のキー：
- `"creator"` (str) : 提出者名
- `"fileindex"` (str) : R2ストレージ上のファイル識別子（拡張子なし）

---

##### `async get_log(output_format, log_filter=None, limit_scope=None, branch=ShellArcGitBranch.PENDING) -> dict[str, str]`

Gitログを取得し、フィルタリングと整形を行う。

**内部のログフォーマット：**  
`git log` は `--format=%h=&=%s` オプションで実行される。各行は `=&=` で区切られており、左側がショートハッシュ、右側がコミットメッセージ（`%s`）となる。コミットメッセージはさらに `*` で分割されてフィールドに展開される。`output_format` に指定したインデックスのフィールドのみが返り値に含まれる。

`output_format` に指定したインデックスの最大値がコミットメッセージのフィールド数以上の場合（フィールド数が足りない初期化コミットなど）、そのログ行は**スキップされる**。

| 引数 | 型 | 説明 |
|---|---|---|
| `output_format` | `list[int]` | 返すフィールドのインデックスリスト（下表参照）|
| `log_filter` | `SA_GitLogFilter \| None` | フィルター条件（デフォルト: `None` = フィルタなし）|
| `limit_scope` | `str \| None` | 特定ファイルパスのみに絞り込む（例: `"stage/cut1/modeling.json"`）。`None` は全体（デフォルト: `None`）|
| `branch` | `ShellArcGitBranch \| str` | 対象ブランチ（デフォルト: `ShellArcGitBranch.PENDING`）|

**コミットメッセージのフィールドインデックス（`*` で split 後）：**

| インデックス | フィールド名 | 説明 |
|---|---|---|
| 0 | `commit_type` | コミットタイプ（`SUBMIT`, `APPROVE`, `DECLINE`, `REPOINT`, `ABSORPTION`）|
| 1 | `cut_num` | カット番号（文字列）|
| 2 | `component` | コンポーネント名 |
| 3 | `creator_name` | 作成者名（REPOINTとABSORPTIONは `"REPOINT"` / `"ABSORB"` 固定）|
| 4 | `commit_message` | 任意メッセージ（空の場合は `"No message"`）|
| 5 | `timemark` | タイムスタンプ（JST, `YYYYMMDDHHMMSS`）|
| 6 | `file_index_name` | SUBMITは実際のインデックス名。APPROVE/DECLINEは `'na'`。REPOINT/ABSORPTIONは `"{元カット}->{先カット}"` 形式 |

**返り値** : `dict[str, str]` — `{ショートコミットハッシュ: "フィールド1 フィールド2 ..."}` の形式。フィールドはスペース区切り。新しいコミットが先頭に来る順序。

**使用例：**

```python
# cut1/modelingのSUBMITコミットの タイムスタンプ・作成者・メッセージを最大5件取得
log_filter = SA_GitLogFilter(commit_type=SA_CommitType.SUBMIT, log_length=5)
hist = await git_io.get_log(
    output_format=[5, 3, 4],   # timemark, creator_name, commit_message
    log_filter=log_filter,
    limit_scope="stage/cut1/modeling.json",
    branch=ShellArcGitBranch.PENDING
)
# → {"abc1234": "20240101120000 YamadaTaro 初回提出", ...}

# file_index_name（インデックス6）を取得する場合はSUBMITコミットのみ対象にすること
# (APPROVE等はインデックス6が 'na' になるため)
hist2 = await git_io.get_log(
    output_format=[5, 6],
    log_filter=SA_GitLogFilter(commit_type=SA_CommitType.SUBMIT),
    limit_scope="stage/cut1/modeling.json"
)
# → {"abc1234": "20240101120000 cut1_modeling_a1b2c3_20240101120000", ...}
```

**送出例外：**
- `SA_LocalIOError(SA_8002)` : `git log` コマンドが失敗した場合

---

##### `async update_data(cut_num, component, creator_name, message="") -> str`

コンポーネントの新規提出（SUBMIT）を行う。`_git_lock` で排他制御される。

**処理フロー：**
1. `message` 内の `*` を `+` に置換
2. `_make_index_name()` で `file_index_name` を生成
3. `pending` ブランチへ `checkout`
4. `stage/cut{N}/{component}.json` に `{"creator": ..., "fileindex": ...}` を書き込み
5. `git add` → `git commit` (SUBMITコミット)
6. `stage/cut{N}/.sa_pending_{component}` を空ファイルとして作成（ペンディング状態を示す）

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `creator_name` | `str` | 提出者名 |
| `message` | `str` | コミットメッセージ。空の場合は `"No message"` になる（デフォルト: `""`）|

**返り値** : `str` — 生成された `file_index_name`。R2アップロードパスの構築に使用する。  
形式: `cut{N}_{component(アンダースコアはハイフン変換済み)}_{creator_id(6文字hex)}_{YYYYMMDDHHMMSS}`

---

##### `async pend_data(cut_num, component, processing_person, is_approve, message="") -> None`

レビュー担当者による承認または却下を行う。`_git_lock` で排他制御される。

**ペンディング状態の確認方法：**  
`git status --porcelain stage/cut{N}` の出力に `.sa_pending_{component}` が含まれるかどうかで判定する。含まれない場合は `SA_InvalidRequestObj` を送出する（`frontend_msg`: `"承認待ちの提出はありません"`）。

**承認（`is_approve=True`）の処理フロー：**
1. `git status --porcelain` でペンディングファイルの存在確認
2. `os.unlink()` で `.sa_pending_{component}` を削除
3. `pending` ブランチへ `checkout`
4. `git add stage/cut{N}` → APPROVEコミット (pending ブランチ)
5. `main` ブランチへ `checkout`
6. `git checkout pending -- stage/cut{N}/{component}.json` (pendingのJSONをmainに持ってくる)
7. `git add stage/cut{N}/{component}.json` → APPROVEコミット (main ブランチ)

**却下（`is_approve=False`）の処理フロー：**
1. `git status --porcelain` でペンディングファイルの存在確認
2. `os.unlink()` で `.sa_pending_{component}` を削除
3. `pending` ブランチへ `checkout`
4. `git add stage/cut{N}` → DECLINEコミット (pending ブランチのみ。mainへの反映なし)

**ロールバック：** `_continuous_git_command` が例外を送出した場合、`.sa_pending_{component}` を空ファイルとして再生成してから `SA_LocalIOError(SA_8002)` を送出する。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `processing_person` | `str` | 処理者名（レビュアー）|
| `is_approve` | `bool` | `True` = 承認, `False` = 却下 |
| `message` | `str` | コメント。空の場合は `"No message"` になる（デフォルト: `""`）|

**返り値** : `None`

**送出例外：**
- `SA_InvalidRequestObj` : `.sa_pending_{component}` が存在しない。`frontend_msg` = `"承認待ちの提出はありません"`
- `SA_LocalIOError(SA_8002)` : gitコマンドが失敗した場合（`.sa_pending_{component}` を再生成してロールバック）

---

##### `async repoint_data(be_repointed_cut, repoint_target_cut, component) -> None`

カットのコンポーネントデータを別カットへの参照に付け替えする。`_git_lock` で排他制御される。例えばカット5がカット3と同じ素材を使う場合に使用する。

**処理フロー：**
1. `pending` ブランチへ `checkout`
2. `stage/cut{be_repointed_cut}/{component}.json` に `{"repointer": repoint_target_cut}` を書き込み
3. `git add` → REPOINTコミット（メッセージに `"{be_repointed_cut}->{repoint_target_cut}"` が含まれる）
4. `stage/cut{be_repointed_cut}/.sa_pending_{component}` を空ファイルとして作成

**注意：** `repoint_data` 後のカットは `get_component_info()` を呼ぶと自動的に参照先カットのデータにリダイレクトされる。レビュー承認後に `main` ブランチに反映される。

| 引数 | 型 | 説明 |
|---|---|---|
| `be_repointed_cut` | `int` | 参照付け替えされる側のカット番号 |
| `repoint_target_cut` | `int` | 参照先となるカット番号 |
| `component` | `str` | コンポーネント名 |

**返り値** : `None`

---

##### `async absorb_data(absorbing_cut, absorb_target_cut, component, commit_id=None, branch=ShellArcGitBranch.PENDING) -> None`

あるカットのコンポーネントJSONを別カットにコピーして取り込む。`repoint_data` とは異なり、参照ではなく **データの実体コピー** を行う。**このメソッドは `_git_lock` を取得しない**。

**処理フロー：**
1. 指定 `branch` へ `checkout`
2. `git show {commit_id_or_branch}:stage/cut{absorb_target_cut}/{component}.json` で取り込み元のJSONを取得（取得失敗または存在しない場合は `{}`）
3. `pending` ブランチへ `checkout`
4. `stage/cut{absorbing_cut}/{component}.json` に取得したJSONを書き込み
5. `git add` → ABSORPTIONコミット（メッセージに `"{absorb_target_cut}->{absorbing_cut}"` が含まれる）
6. `stage/cut{absorbing_cut}/.sa_pending_{component}` を空ファイルとして作成

| 引数 | 型 | 説明 |
|---|---|---|
| `absorbing_cut` | `int` | 取り込む側のカット番号 |
| `absorb_target_cut` | `int` | 取り込まれる側のカット番号（コピー元）|
| `component` | `str` | コンポーネント名 |
| `commit_id` | `str \| None` | コピー元の特定コミットIDを指定する場合。`None` は `branch` の最新（デフォルト: `None`）|
| `branch` | `ShellArcGitBranch` | コピー元のブランチ（デフォルト: `ShellArcGitBranch.PENDING`）|

**返り値** : `None`

---

##### `async sync_remote() -> None`

ローカルGitリポジトリの `main` と `pending` ブランチをリモートの `origin` へプッシュする。

**処理フロー：**
1. `git push origin main`
2. `git checkout pending`
3. `git push origin pending`

**返り値** : `None`

---

### 7-3. `io_r2.py` — `R2_IO`

Cloudflare R2（S3互換）へのファイル操作を担当するクラス。

```python
R2_IO(bucket_name: str | None = None)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `bucket_name` | `str \| None` | バケット名。`None` の場合は `project_settings.json` の `bucket_name` を使用 |

---

##### `get_s3obj_size(target_s3_file) -> int`

S3オブジェクトのサイズをMB単位で取得する。

| 引数 | 型 | 説明 |
|---|---|---|
| `target_s3_file` | `str` | S3内のファイルパス（キー）|

**返り値** : `int` — ファイルサイズ（MB単位、切り捨て）

---

##### `issue_presigned_url(target_s3_file, url_client_method, http_method, time_limit=180) -> str`

S3オブジェクトへの一時アクセスURLを発行する。

| 引数 | 型 | 説明 |
|---|---|---|
| `target_s3_file` | `str` | S3内のファイルパス |
| `url_client_method` | `str` | boto3のメソッド名（例: `"get_object"`, `"put_object"`）|
| `http_method` | `str` | HTTPメソッド（例: `"GET"`, `"PUT"`）|
| `time_limit` | `int` | URL有効期限（秒）（デフォルト: `180`）|

**返り値** : `str` — 署名付きURL文字列

---

##### `get_path_with_ext(path_without_ext) -> str`

拡張子なしのパスプレフィックスをS3でリスト検索し、マッチした最初のフルパスを返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `path_without_ext` | `str` | 拡張子を含まないS3パス（プレフィックス）|

**返り値** : `str` — 拡張子を含む完全なS3パス

---

##### `upload_file(uploading_file, file_path, url_prefix=None) -> str | None`

ファイルをR2にアップロードする。`url_prefix` を渡すと公開URLを返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `uploading_file` | `bytes \| str \| Path` | アップロードするファイル。バイト列・ローカルパス文字列・Pathオブジェクトのいずれか |
| `file_path` | `str \| Path` | R2上の保存先パス |
| `url_prefix` | `str \| None` | 公開URLのプレフィックス（例: `"https://pub-xxx.r2.dev"`）。`None` の場合は `None` を返す |

**返り値** : `str | None` — `url_prefix` が指定された場合は `"{url_prefix}/{file_path}"` 形式の公開URL。それ以外は `None`。

**バイト列を渡した場合** : 一時ファイルに書き出してアップロード後、自動で削除する。

**送出例外：**
- `SA_ProjStructError(SA_5101)` : `uploading_file` が `None`
- `SA_CommunicationError(SA_8001)` : アップロード失敗

---

##### `download_file(to_download_file, download_destination, file_naming) -> None`

R2からファイルをローカルにダウンロードする。

| 引数 | 型 | 説明 |
|---|---|---|
| `to_download_file` | `str` | R2上のファイルパス |
| `download_destination` | `str` | ローカルの保存先ディレクトリパス |
| `file_naming` | `str` | 保存ファイル名 |

**返り値** : `None`。ダウンロード後 1秒のスリープが入る（ファイルの書き込み完了待ち）。

**送出例外：**
- `SA_CommunicationError(SA_8001)` : ダウンロード失敗

---

### 7-4. `io_notion.py` — `Notion_IO`

Notionデータベースの画像プロパティを操作するクラス。絵コンテ画像の取得・更新に使用する。

```python
Notion_IO(cut_num: int)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | 対象のカット番号 |

コンストラクタでNotionデータベースの全レコードを取得する。レコードは逆順（最新のカットが先頭）でアクセスされる（`results[cut_num * -1]`）。

---

##### `get_image_file(download_destination, attr_name="画像") -> None`

Notionデータベースの画像プロパティからファイルをダウンロードする。

| 引数 | 型 | 説明 |
|---|---|---|
| `download_destination` | `str \| Path` | ローカルの保存先パス（ファイル名を含む）|
| `attr_name` | `str` | Notionプロパティ名（デフォルト: `"画像"`）|

**返り値** : `None`

**送出例外：**
- `SA_InvalidRequestObj` : 指定カット番号のレコードが存在しない
- `SA_CommunicationError(SA_3000)` : 画像URLのフォーマットが不正、または画像のダウンロードに失敗

---

##### `put_image_url(img_url, attr_name="画像") -> None`

NotionデータベースのレコードにExternal画像URLをセットする。

| 引数 | 型 | 説明 |
|---|---|---|
| `img_url` | `str` | セットする画像のURL |
| `attr_name` | `str` | Notionプロパティ名（デフォルト: `"画像"`）|

**返り値** : `None`

**送出例外：**
- `SA_InvalidRequestObj` : 指定カット番号のレコードが存在しない
- `SA_CommunicationError(SA_3000)` : Notion APIへのリクエストが失敗

---

## 8. ユーティリティ (utils)

### 8-1. `file_operation.py` — `FileOperation`

ローカルファイル操作のユーティリティ静的メソッド集。

#### `FileOperation.renamed(cut_num, take, component) -> str`

プロジェクト設定の命名規則に従い、ファイル名（拡張子なし）を生成する。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `take` | `int` | テイク番号 |
| `component` | `str` | コンポーネント名 |

**返り値** : `str` — 生成されたファイル名文字列。各セクションは `_` で結合される。

`project_settings.json` の命名規則：
- `-cut` → `cut{cut_num}` に展開
- `-take` → `take{take}` に展開
- それ以外の文字列 → 先頭の `-` とスペースを除去してそのまま使用

**例：** `naming_section=3`, `name_component_1="-cut"`, `name_component_2="modeling"`, `name_component_3="-take"` の場合、`cut_num=5, take=3` → `"cut5_modeling_take3"`

---

#### `async FileOperation.make_zip(files, required_format) -> str`

複数のPNGファイルを受け取り、ZIPに圧縮してローカルの一時ファイルに保存する。

| 引数 | 型 | 説明 |
|---|---|---|
| `files` | `dict[str, bytes]` | `{ファイル名: バイト列}` の辞書。ファイル名は `.png` 拡張子を持つ必要がある |
| `required_format` | `list[str]` | 許可する拡張子リスト（現在は検証のみに使用）|

**返り値** : `str` — 生成されたZIP一時ファイルの絶対パス。使用後は `os.unlink()` で削除すること。

**注意：** 圧縮対象は **PNG形式のみ**。他の拡張子が含まれると `SA_InvalidUserQuery` が送出される。

**送出例外：**
- `SA_InvalidUserQuery` : PNG以外のファイルが含まれている
- `SA_LocalIOError(SA_8000)` : ZIP作成中に予期せぬエラーが発生（一時ファイルは自動削除）

---

## 9. ビジネスロジックレイヤー (process)

このレイヤーのクラスは `shellarc_core` の各IOクラスを組み合わせて、アプリケーションのユースケースを実装する。新しいアプリを構築する際の参考実装として読むこと。

### 9-1. `uploader.py` — `ShellArc_Upload`

素材ファイルのアップロード処理を担当する。

```python
ShellArc_Upload(cut_num: int, working_component: str)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | 対象カット番号 |
| `working_component` | `str` | 対象コンポーネント名 |

---

##### `async upload_file(file, submitter_name, message="") -> None`

ファイルをR2にアップロードし、Gitにコミット、スプレッドシートを更新する。

**処理フロー：**
1. コンポーネントの許可フォーマット確認
2. 複数ファイルの場合はZIPに圧縮（`format` に `zip` が含まれる場合のみ）
3. `Git_IO.update_data()` でGitコミット、`file_index_name` を取得
4. `R2_IO.upload_file()` で R2 にアップロード（パス: `{collection_name}/stage/{file_index_name}.{format}`）
5. スプレッドシートの `{component}_PIC` を `submitter_name` に更新
6. スプレッドシートの `{component}_progress` を `"作業中"` に更新
7. `{component}_PIC` セルを黄色 `(1, 1, 0)` に着色

| 引数 | 型 | 説明 |
|---|---|---|
| `file` | `dict[str, bytes]` | `{ファイル名: バイト列}` の辞書。単一ファイルの場合は1エントリ |
| `submitter_name` | `str` | 提出者名 |
| `message` | `str` | コミットメッセージ（デフォルト: `""`）|

**返り値** : `None`

**送出例外：**
- `SA_InvalidUserQuery` : フォーマットが不正、または複数ファイルなのに `zip` が許可されていない

---

##### `async get_upload_page(submitter_name, message) -> tuple[str, str]`

R2への署名付きアップロードURLを埋め込んだHTMLページを生成する。ファイルサイズが大きい場合にブラウザから直接R2にアップロードさせるための機能。

**処理フロー：**
1. `Git_IO.update_data()` でGitコミット（ファイル本体はまだない）
2. R2への PUT 署名付きURL（有効期限300秒）を生成
3. `uploader_from_url.html.template` の `__S3_PRESIGNED_URL_PLACEHOLDER_XYZ__` を実際のURLに置換
4. 一時ディレクトリにHTMLファイルを書き出す

| 引数 | 型 | 説明 |
|---|---|---|
| `submitter_name` | `str` | 提出者名 |
| `message` | `str` | コミットメッセージ |

**返り値** : `tuple[str, str]` — `(html_file_path, temp_dir_path)`。HTMLファイルのパスと一時ディレクトリのパス。使用後は一時ディレクトリごと削除すること。

---

##### `async sync_vps_with_remote() -> None` (staticmethod)

`Git_IO.sync_remote()` を呼び出し、ローカルGitをリモートに同期する。

---

### 9-2. `requesting.py` — `ShellArc_Request`

素材ファイルのダウンロード処理を担当する。

```python
ShellArc_Request(cut_num: int, requesting_component: str)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | 対象カット番号 |
| `requesting_component` | `str` | 対象コンポーネント名 |

---

##### `async download_material(requesting_take) -> tuple[str, str, str]`

指定テイクの素材ファイルを取得する。ファイルサイズが10MB超の場合は署名付きURLを、10MB以下の場合は一時ファイルのパスを返す。

| 引数 | 型 | 説明 |
|---|---|---|
| `requesting_take` | `str` | 取得するテイクの指定。`"0"` = 最新確定版(mainブランチ)、`"-1"` = 作業中(pendingブランチの最新)、その他の文字列 = 特定のコミットID |

**返り値** : `tuple[str, str, str]` — `(path_or_url, filename_with_ext, type_indicator)`

| インデックス | 内容 |
|---|---|
| 0 | 署名付きURL または ローカル一時ファイルパス |
| 1 | ファイル名（拡張子付き）（例: `"cut1_modeling_abc123_20240101.blend"`）|
| 2 | `"url"` または `"path"` — インデックス0の種別を示す |

**送出例外：**
- `SA_DataNotExist` : 指定テイクのデータが存在しない
- `SA_ProjStructError(SA_6002)` : コンポーネントJSONに `fileindex` キーがない
- `SA_LocalIOError(SA_8000)` : 一時ファイルが生成されていない

---

### 9-3. `reviewing.py` — `ShellArc_Review`

レビュー（承認・却下）処理を担当する。

```python
ShellArc_Review(cut_num: int, reviewing_component: str)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | 対象カット番号 |
| `reviewing_component` | `str` | 対象コンポーネント名 |

---

##### `async pending_action(reviewer_name, is_approve, message="") -> None`

レビューアクション（承認または却下）を実行する。

**処理フロー（承認の場合）：**
1. ペンディングデータの存在確認（`_existence_check`）
2. `Git_IO.pend_data()` で承認コミット
3. スプレッドシートの `{component}_progress` を `"完了"` に更新
4. `{component}_PIC` セルを緑色 `(0, 1, 0)` に着色

**処理フロー（却下の場合）：**
1. ペンディングデータの存在確認
2. `Git_IO.pend_data()` で却下コミット（スプレッドシートの更新なし）

| 引数 | 型 | 説明 |
|---|---|---|
| `reviewer_name` | `str` | レビュアー名 |
| `is_approve` | `bool` | `True` = 承認, `False` = 却下 |
| `message` | `str` | コメント（デフォルト: `""`）|

**返り値** : `None`

**送出例外：**
- `SA_InvalidRequestObj` : ペンディングデータが存在しない

---

### 9-4. `register.py` — `ShellArc_Register`

コンポーネントへの担当者登録を担当する。

```python
ShellArc_Register()
```

---

##### `async register_work(registering_person, registering_component, registering_cut, force=False) -> None`

スプレッドシートにコンポーネントの担当者を登録する。担当者がすでに登録されている場合は `force=True` を渡さない限り拒否される。

| 引数 | 型 | 説明 |
|---|---|---|
| `registering_person` | `str` | 登録する担当者名 |
| `registering_component` | `str` | コンポーネント名 |
| `registering_cut` | `int` | カット番号 |
| `force` | `bool` | `True` にすると既存担当者を上書き（デフォルト: `False`）|

**返り値** : `None`

登録成功後：
- `{component}_PIC` を `registering_person` に更新
- `{component}_PIC` セルを青緑色 `(0.7, 0.85, 0.85)` に着色

**送出例外：**
- `SA_EditingRejection` : 既に別の担当者が登録されており、`force=False` の場合

---

### 9-5. `storyboard.py` — `ShellArc_Storyboard`

絵コンテ（レイアウト）画像の取得・アップロードを担当する。

```python
ShellArc_Storyboard(cut_num: int)
```

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | 対象カット番号 |

---

##### `async download_storyboard() -> str`

NotionからPNG画像をダウンロードし、一時ファイルパスを返す。

**返り値** : `str` — ダウンロードした画像の一時ファイル絶対パス（`{tempdir}/cut{N}_layout.png` 形式）

**送出例外：**
- `SA_LocalIOError(SA_8000)` : 一時ファイルが生成されていない

---

##### `async upload_storyboard(file_obj) -> None`

絵コンテ画像をR2にアップロードし、NotionのデータベースにURLをセットする。スプレッドシートの進捗も更新する。

**処理フロー：**
1. `R2_IO.upload_file()` でR2にアップロード（パス: `storyboard/cut{N}.png`、バケット: `shellarc-storyboard`）
2. `Notion_IO.put_image_url()` でNotionに公開URLをセット
3. スプレッドシートの `layout_progress` を `"完了"` に更新

| 引数 | 型 | 説明 |
|---|---|---|
| `file_obj` | `bytes` | アップロードするPNG画像のバイト列 |

**返り値** : `None`

---

### 9-6. `query.py` — `ShellArc_Query`

情報の照会に特化した静的メソッド集。

---

##### `async efficient_get_spreadsheet_info(target_index_value, index_info_types, target_info_types, search_range, output_key="index_info_type", page_idx=0) -> dict`

スプレッドシートのキャッシュを使用して、指定値に一致する行の情報を効率的に取得する。

| 引数 | 型 | 説明 |
|---|---|---|
| `target_index_value` | `str` | 検索する値 |
| `index_info_types` | `list[str]` | 検索対象のカラムに対応するアイテム名のリスト |
| `target_info_types` | `list[str]` | 取得対象のカラムに対応するアイテム名のリスト（`index_info_types` と同じ長さ）|
| `search_range` | `list[int]` | 検索するカット番号の範囲。`[開始カット番号, 終了カット番号]` の2要素リスト |
| `output_key` | `str` | 返り値辞書のキーとして使うフィールド。`"index_info_type"` または `"target_info_type"`（デフォルト: `"index_info_type"`）|
| `page_idx` | `int` | ページインデックス（デフォルト: `0`）|

**返り値** : `dict` — `output_key` の設定により、インデックスアイテム名またはターゲットアイテム名をキーとした辞書

**送出例外：**
- `SA_InternalSyntaxError(SA_7000)` : `search_range` が2要素でない、または開始 > 終了、または2リストの長さが一致しない

---

##### `get_components_enname(cut_num) -> list[str]` (staticmethod)

指定カットのコンポーネント名リストを取得する（`Git_IO.get_components()` のラッパー）。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |

**返り値** : `list[str]` — コンポーネント名のリスト

---

##### `async get_history(cut_num, component, max_length=None) -> dict[str, str]` (staticmethod)

指定カット・コンポーネントの提出履歴（SUBMITコミット）を取得する。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `max_length` | `int \| None` | 最大取得件数。`None` は全件（デフォルト: `None`）|

**返り値** : `dict[str, str]` — `{コミットハッシュ: "コミットメッセージ タイムスタンプ ファイルインデックス名"}` の形式（`output_format=[5, 3, 4]` = timemark, creator_name, commit_message）

---

##### `async get_approve_history(cut_num, component, max_length=None) -> dict[str, str]` (staticmethod)

指定カット・コンポーネントの承認履歴（APPROVEコミット）を取得する。`main` ブランチのログから取得する点に注意。

| 引数 | 型 | 説明 |
|---|---|---|
| `cut_num` | `int` | カット番号 |
| `component` | `str` | コンポーネント名 |
| `max_length` | `int \| None` | 最大取得件数。`None` は全件（デフォルト: `None`）|

**返り値** : `dict[str, str]` — `get_history()` と同じ形式

---

## 10. Gitコミットメッセージ仕様

`shellarc_core` は以下のフォーマットのコミットメッセージを使用する。`*` をデリミタとしたフィールド区切りになっており、`get_log()` でパースして利用される。

```
{commit_type} * {cut_num} * {component} * {creator_name} * {message} * {timemark} * {file_index_name}
```

**各フィールドのインデックス（split("*") 後）：**

| インデックス | フィールド | 例 |
|---|---|---|
| 0 | `commit_type` | `SUBMIT` |
| 1 | `cut_num` | `5` |
| 2 | `component` | `modeling` |
| 3 | `creator_name` | `YamadaTaro` |
| 4 | `message` | `No message` |
| 5 | `timemark` | `20240101120000` |
| 6 | `file_index_name` | `cut5_modeling_abc123_20240101120000` |

**注意事項：**
- ユーザーが入力する `message` 内の `*` は `+` に自動置換される
- `REPOINT` および `ABSORPTION` コミットは `file_index_name` の代わりに操作内容（例: `5->3`）が格納される
- `file_index_name` のフォーマット: `cut{N}_{component}_{creator_id_6char}_{YYYYMMDDHHMMSS}`

---

## 11. 典型的なユースケースとフロー

### ユースケース1: 素材の提出（アップロード）

```python
from shellarc_core.process.uploader import ShellArc_Upload

uploader = ShellArc_Upload(cut_num=5, working_component="modeling")

# file_bytes は bot や API から受け取ったバイト列
await uploader.upload_file(
    file={"cut5_model_v1.blend": file_bytes},
    submitter_name="YamadaTaro",
    message="初回提出"
)
```

### ユースケース2: 署名付きURLでの大容量ファイルアップロード

```python
from shellarc_core.process.uploader import ShellArc_Upload

uploader = ShellArc_Upload(cut_num=5, working_component="modeling")
html_path, temp_dir = await uploader.get_upload_page(
    submitter_name="YamadaTaro",
    message="大容量ファイル提出"
)
# html_path のHTMLをユーザーに送信する
# アップロード完了後、temp_dir を削除する
import shutil
shutil.rmtree(temp_dir)
```

### ユースケース3: 素材のダウンロード

```python
from shellarc_core.process.requesting import ShellArc_Request

req = ShellArc_Request(cut_num=5, requesting_component="modeling")

# 最新確定版を取得
path_or_url, filename, type_indicator = await req.download_material("0")

if type_indicator == "url":
    # ユーザーにURLを返す
    print(f"ダウンロードURL: {path_or_url}")
else:
    # ファイルをユーザーに送信する
    with open(path_or_url, "rb") as f:
        file_bytes = f.read()
    # 送信後に削除
    import os
    os.unlink(path_or_url)
```

### ユースケース4: レビュー（承認）

```python
from shellarc_core.process.reviewing import ShellArc_Review

review = ShellArc_Review(cut_num=5, reviewing_component="modeling")
await review.pending_action(
    reviewer_name="DirectorSato",
    is_approve=True,
    message="問題なし、OKです"
)
```

### ユースケース5: 担当者登録

```python
from shellarc_core.process.register import ShellArc_Register

register = ShellArc_Register()
await register.register_work(
    registering_person="YamadaTaro",
    registering_component="modeling",
    registering_cut=5
)
```

### ユースケース6: 新規プロジェクトの初期化

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

### ユースケース7: 提出履歴の照会

```python
from shellarc_core.process.query import ShellArc_Query
from shellarc_core.cloudio.io_git import SA_GitLogFilter, SA_CommitType

history = await ShellArc_Query.get_history(
    cut_num=5,
    component="modeling",
    max_length=10
)
# → {"abc1234": "20240101120000 YamadaTaro 初回提出", ...}
```

---

*このドキュメントは `shellarc_core` の全公開インターフェースを網羅しています。内部メソッド（`_` プレフィックス付き）は記述されていますが、外部から直接呼び出すことは推奨されません。*