# ARCHITECTURE.md — `shellarc_core` 内部設計ドキュメント

> このドキュメントは `shellarc_core` の内部アーキテクチャ、レイヤー構造、データモデル、主要フローを説明します。利用方法（インストール・クイックスタート）は [README_jpn.md](../README_jpn.md) を参照してください。

---

## 目次

- [ARCHITECTURE.md — `shellarc_core` 内部設計ドキュメント](#architecturemd--shellarc_core-内部設計ドキュメント)
  - [目次](#目次)
  - [1. 設計思想](#1-設計思想)
  - [2. レイヤードアーキテクチャ](#2-レイヤードアーキテクチャ)
  - [3. ドメインモデル](#3-ドメインモデル)
  - [4. 外部サービスとの対応関係](#4-外部サービスとの対応関係)
  - [5. 設定ファイルとデータフロー](#5-設定ファイルとデータフロー)
  - [6. Gitリポジトリのデータモデル](#6-gitリポジトリのデータモデル)
  - [7. 並行性制御](#7-並行性制御)
  - [8. 例外設計](#8-例外設計)
    - [8-1. ユーザー起因の例外（`user_exception.py`）](#8-1-ユーザー起因の例外user_exceptionpy)
    - [8-2. システム起因の例外（`structure_error.py`）](#8-2-システム起因の例外structure_errorpy)
  - [9. 主要な処理フロー](#9-主要な処理フロー)
    - [9-1. 素材提出（アップロード）フロー](#9-1-素材提出アップロードフロー)
    - [9-2. レビュー（承認／却下）フロー](#9-2-レビュー承認却下フロー)
    - [9-3. ダウンロードフロー](#9-3-ダウンロードフロー)
    - [9-4. リポイント（参照付け替え） vs アブソープション（実体コピー）](#9-4-リポイント参照付け替え-vs-アブソープション実体コピー)
  - [10. Gitコミットメッセージ仕様](#10-gitコミットメッセージ仕様)
  - [11. 拡張・実装時の指針](#11-拡張実装時の指針)

---

## 1. 設計思想

`shellarc_core` は、アニメ・映像制作における「カット単位の素材提出 → レビュー → 承認」というワークフローを、複数のクラウドサービス（Cloudflare R2 / Google Spreadsheet / Git / Notion / Firebase Firestore）を横断して自動化するためのパイプラインバックエンドフレームワークです。

設計上の主なポイントは以下の3つです。

- **単一の真実の情報源（source of truth）としてのGit**：カットの提出履歴・承認状態・バージョン管理はすべてGitリポジトリのコミット履歴とブランチ構造で表現されます。スプレッドシートやNotionは「人間が見るための表示レイヤー」であり、Gitの状態を反映するだけの副次的なストアという位置づけです。
- **レイヤーの分離**：「設定の読み込み（cfg）」「外部サービスへの認証（auth）」「外部サービスへの実際のIO（cloudio）」「業務ロジック（operations）」を明確に分離しており、上位レイヤーは下位レイヤーの実装詳細（APIクライアントの生成方法など）を意識せずに済むようになっています。
- **例外の二分類**：「ユーザーの操作が原因のエラー」と「システム・設定・外部サービス起因のエラー」を型レベルで分離し、アプリ側がそれぞれ異なる方法でハンドリングできるようにしています（後述）。

---

## 2. レイヤードアーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│  operations/           ビジネスロジック層（利用側の実装例）  │
│  uploader / requesting / reviewing / register /          │
│  storyboard / query                                       │
└───────────────────────┬─────────────────────────────────┘
                          │ 呼び出し
┌───────────────────────▼─────────────────────────────────┐
│  cloudio/              クラウドIO層                        │
│  io_git / io_spreadsheet / io_r2 / io_notion              │
└───────────────────────┬─────────────────────────────────┘
                          │ 認証情報を要求
┌───────────────────────▼─────────────────────────────────┐
│  auth/                 認証層                              │
│  access_r2 / access_spread_sheet / access_database /      │
│  access_notion                                             │
└───────────────────────┬─────────────────────────────────┘
                          │ .env を読み込み
┌───────────────────────▼─────────────────────────────────┐
│  cfg/                  設定層                              │
│  cfg_io (project_settings.json) /                          │
│  spreadsheet_map_io (spreadsheet_map.json)                │
└─────────────────────────────────────────────────────────┘

  横断的関心事:
  ┌─────────────────┐   ┌─────────────────────────┐
  │ utils/           │   │ exception/               │
  │ file_operation   │   │ user_exception /         │
  │ (命名規則, ZIP化) │   │ structure_error          │
  └─────────────────┘   └─────────────────────────┘
```

**依存の方向は常に上から下の一方向**です。`operations` は `cloudio` を、`cloudio` は `auth` と `cfg` を利用しますが、逆方向の依存はありません。`utils` と `exception` は全レイヤーから参照される横断的なモジュール群です。

| レイヤー | 責務 | 主なクラス |
|---|---|---|
| cfg | プロジェクト設定・スプレッドシートマッピングのJSON読み込み | `Cfg_IO`, `SpreadsheetMap_IO` |
| auth | `.env` から認証情報を読み取り、各サービスのSDKクライアントを初期化 | `Cloudflare_R2_service_Access`, `AccessSpreadSheet`, `AccessDB`, `Notion_Access` |
| cloudio | 各外部サービスへの実際の読み書き操作（CRUD） | `Git_IO`, `GCP_IO`, `R2_IO`, `Notion_IO` |
| utils | ローカルファイル操作・命名規則・ZIP圧縮などの補助機能 | `FileOperation` |
| exception | ユーザー起因／システム起因の例外階層 | `ShellArcException` 系, `ShellArcError` 系 |
| operations | 上記を組み合わせたユースケース実装（参考実装） | `ShellArc_Upload`, `ShellArc_Request`, `ShellArc_Review`, `ShellArc_Register`, `ShellArc_Storyboard`, `ShellArc_Query` |

---

## 3. ドメインモデル

| 概念 | 識別子 | 説明 |
|---|---|---|
| カット (cut) | `cut_num: int` | 映像制作の最小作業単位 |
| コンポーネント (component) | `str`（例: `modeling`, `texturing`） | カットを構成する作業種別 |
| テイク (take) | Gitコミットに対応 | コンポーネントの提出バージョン |
| ペンディング (pending) | Gitの `pending` ブランチ + `.sa_pending_{component}` ファイル | レビュー待ちの提出状態 |

**関係性**：1つのカットは複数のコンポーネントを持ち、1つのコンポーネントは複数回のテイク（提出）を持つことができます。各テイクはGitコミットとして記録され、承認されると `pending` ブランチから `main` ブランチへ反映されます。

---

## 4. 外部サービスとの対応関係

| サービス | 役割 | 対応するIOクラス |
|---|---|---|
| Cloudflare R2 (S3互換) | 素材ファイルの実体ストレージ | `R2_IO` |
| Google Spreadsheet | 進捗・担当者管理台帳（人間向け表示） | `GCP_IO` |
| Git（ローカル＋リモート） | カットごとのバージョン管理・承認フローの真実の情報源 | `Git_IO` |
| Notion | レイアウト画像（絵コンテ）の管理 | `Notion_IO` |
| Firebase Firestore | 汎用データベース（認証情報管理など） | `AccessDB`（`auth`層のみで、対応する`cloudio`クラスはドキュメント記載なし） |

**重要な設計上の帰結**：素材ファイル本体はR2に、提出・承認の「状態」はGitに、人間向けの進捗表示はSpreadsheetに、というように**責務ごとにストレージが完全に分離**されています。1回の提出処理（`upload_file`）では、この3つ（Git → R2 → Spreadsheet）に順番に書き込みが行われます。

---

## 5. 設定ファイルとデータフロー

すべての設定は環境変数 `SHELLARC_PROJECT_CTX` が指すディレクトリに集約されます。

```
$SHELLARC_PROJECT_CTX/
├── project_settings.json   # プロジェクト基本設定・コンポーネント定義 → Cfg_IO が読む
├── spreadsheet_map.json    # スプレッドシートのセル座標マッピング → SpreadsheetMap_IO が読む
└── .env                    # 各サービスの認証情報 → auth/ 配下の各Accessクラスが読む
```

`Cfg_IO` と `SpreadsheetMap_IO` は**コンストラクタでJSONを一度だけ読み込む**設計であり、`cloudio` 層のクラス（`GCP_IO`, `R2_IO`, `Git_IO` 等）は内部でこれらを利用して、バケット名・スプレッドシートキー・Gitリポジトリパスなどのデフォルト値を解決します。これにより、`operations` 層のクラスは通常これらのパスや鍵を明示的に渡す必要がありません。

---

## 6. Gitリポジトリのデータモデル

```
{git_repo_local}/
├── project_main.json        # カット別コンポーネント定義（"common" + カット固有の上書き）
└── stage/
    ├── cut1/
    │   ├── modeling.json          # {"creator": ..., "fileindex": ...} または {"repointer": N}
    │   ├── .sa_pending_modeling   # 存在する場合のみ：ペンディング中を示すマーカーファイル
    │   └── texturing.json
    └── cut2/ ...
```

- **`project_main.json`**：`common` キーが全カットのデフォルトのコンポーネント構成を定義し、`cut{N}` キーが存在する場合はそのカットのみ上書きされます。
- **コンポーネントJSON（通常提出）**：`{"creator": "提出者名", "fileindex": "cut1_modeling_abc123_20240101120000"}` の形式。`fileindex` はR2上のファイルを一意に特定するキーです。
- **コンポーネントJSON（リポイント）**：`{"repointer": 3}` の形式。このカットのデータは指定カット番号（例では `3`）のデータを**参照**します（実体コピーではない）。`get_component_info()` はこのキーを検出すると自動的に再帰的に参照先を解決します。
- **`.sa_pending_{component}`**：空ファイル。存在すればそのコンポーネントがレビュー待ち状態であることを示す、Gitの管理外の「フラグファイル」です。`git status --porcelain` の出力を見て判定されます。

2つのブランチが常に存在します。

| ブランチ | 意味 |
|---|---|
| `pending` | 作業中・レビュー待ちのデータ。すべての提出（SUBMIT）はまずここにコミットされる |
| `main` | 承認済みの確定データ。`pend_data()` で承認された内容のみが反映される |

---

## 7. 並行性制御

`Git_IO` はクラス変数 `_git_lock = asyncio.Lock()` を持ち、以下の書き込み系メソッドはこのロックにより**クラス全体で排他制御**されます。

- `update_data`（新規提出）
- `pend_data`（承認・却下）
- `repoint_data`（参照付け替え）

一方、**`absorb_data`（データの実体コピー）はロックを取得しません**。これは元ドキュメントに明記されている仕様上の非対称性であり、複数の `absorb_data` 呼び出しを他の書き込み操作と並行実行する場合は、呼び出し側で追加の排他制御を検討する必要がある点に注意してください。

このロックはGitのローカル作業ディレクトリ（ワーキングツリー）が単一であることに起因します。非同期環境で複数の提出・承認処理が同時に走ると `git checkout` の競合が発生するため、この排他制御が必要とされています。

---

## 8. 例外設計

例外は「原因がユーザーにあるか、システムにあるか」で2系統に分かれます。共通の分類として `SA_ExceptionType` (Enum) が内部的に使われます。

### 8-1. ユーザー起因の例外（`user_exception.py`）

基底クラス `ShellArcException` を継承し、`frontend_msg` プロパティにそのままUIへ表示できるメッセージを持ちます。

| クラス | 用途 |
|---|---|
| `SA_DataNotExist` | データが存在しない |
| `SA_InvalidUserQuery` | 不正なリクエスト（許可されていないファイル形式など） |
| `SA_InvalidRequestObj` | 存在しないオブジェクトへの参照（未提出のカットなど） |
| `SA_EditingRejection` | 意図しない上書きの防止（担当者が既に登録済みなど） |
| `SA_SapycSyntaxError` | 独自構文エラー |

### 8-2. システム起因の例外（`structure_error.py`）

基底クラス `ShellArcError` を継承し、`frontend_msg` は常に固定文言 `"技術班にご連絡ください : {error_code.name}"` です。`error_code` は `SA_ErrorCode` (Enum) で細分化され、`is_fatal` フラグでログの重大度が制御されます。

| クラス | 主なエラーコード | `is_fatal` |
|---|---|---|
| `SA_ProjStructError` | SA_4001, SA_4002, SA_6001, SA_6002 | True |
| `SA_RequestItemError` | SA_5001, SA_5002 | False |
| `SA_CommunicationError` | SA_3000, SA_8001 | True |
| `SA_AuthError` | SA_9000, SA_9001 | True |
| `SA_LocalIOError` | SA_8000, SA_8002 | True |
| `SA_InternalSyntaxError` | SA_7000 | True |

**設計意図**：この二分類により、呼び出し側アプリケーションは「ユーザーに操作をやり直させるべきエラー（`ShellArcException` 系）」と「開発者・運用担当に連絡すべき致命的なエラー（`ShellArcError` 系）」を、例外の型だけで機械的に切り分けられます。

---

## 9. 主要な処理フロー

### 9-1. 素材提出（アップロード）フロー

```
ShellArc_Upload.upload_file()
  1. コンポーネントの許可フォーマットを確認
  2. 複数ファイル & zip許可 の場合 → FileOperation.make_zip() でPNGをZIP化
  3. Git_IO.update_data()
       → pending ブランチへ checkout
       → stage/cut{N}/{component}.json 書き込み（SUBMITコミット）
       → .sa_pending_{component} を作成
       → file_index_name を返す
  4. R2_IO.upload_file()
       → {collection_name}/stage/{file_index_name}.{format} へアップロード
  5. GCP_IO.update_info()  → {component}_PIC = submitter_name
  6. GCP_IO.update_info()  → {component}_progress = "作業中"
  7. GCP_IO.color_cell()   → {component}_PIC セルを黄色 (1,1,0)
```

### 9-2. レビュー（承認／却下）フロー

```
ShellArc_Review.pending_action()
  1. .sa_pending_{component} の存在確認（なければ SA_InvalidRequestObj）
  2. Git_IO.pend_data()
     承認の場合:
       → .sa_pending_{component} 削除
       → pending ブランチで APPROVEコミット
       → main ブランチへ checkout
       → pendingのJSONを main に取り込み、main側でも APPROVEコミット
     却下の場合:
       → .sa_pending_{component} 削除
       → pending ブランチのみで DECLINEコミット（main には反映しない）
  3. (承認時のみ) GCP_IO.update_info() → {component}_progress = "完了"
  4. (承認時のみ) GCP_IO.color_cell()  → {component}_PIC セルを緑色 (0,1,0)
```

ロールバック：ステップ2でGitコマンドが失敗した場合、`.sa_pending_{component}` を再生成した上で `SA_LocalIOError(SA_8002)` を送出します。

### 9-3. ダウンロードフロー

```
ShellArc_Request.download_material(requesting_take)
  requesting_take:
    "0"  → main ブランチ（最新確定版）
    "-1" → pending ブランチ（作業中の最新）
    その他 → 特定コミットID
  1. Git_IO.get_component_info() でコンポーネントJSON取得（repointer は自動解決）
  2. fileindex から R2 上のファイルパスを解決
  3. ファイルサイズを確認
       10MB超 → R2_IO.issue_presigned_url() で署名付きURLを返す
       10MB以下 → R2_IO.download_file() でローカル一時ファイルに保存しそのパスを返す
```

### 9-4. リポイント（参照付け替え） vs アブソープション（実体コピー）

| | `repoint_data` | `absorb_data` |
|---|---|---|
| 意味 | 別カットのデータへの**参照** | 別カットのデータの**実体コピー** |
| ロック取得 | あり | **なし** |
| コミットタイプ | `REPOINT` | `ABSORPTION` |
| 参照先が更新された場合 | 自動的に反映される（都度解決） | 反映されない（コピー時点で固定） |

両者ともレビュー承認（`pend_data`）を経て `main` ブランチに反映される点は共通です。

---

## 10. Gitコミットメッセージ仕様

すべてのコミットは `*` 区切りの固定フォーマットで記録され、`get_log()` がこれをパースします。

```
{commit_type} * {cut_num} * {component} * {creator_name} * {message} * {timemark} * {file_index_name}
```

| インデックス | フィールド | 例 |
|---|---|---|
| 0 | `commit_type` | `SUBMIT` / `APPROVE` / `DECLINE` / `REPOINT` / `ABSORPTION` |
| 1 | `cut_num` | `5` |
| 2 | `component` | `modeling` |
| 3 | `creator_name` | `YamadaTaro`（REPOINT/ABSORPTIONは固定文字列） |
| 4 | `message` | `No message` |
| 5 | `timemark` | `20240101120000`（JST） |
| 6 | `file_index_name` | `cut5_modeling_abc123_20240101120000`（REPOINT/ABSORPTIONは `5->3` 形式） |

**注意事項**：
- ユーザー入力の `message` 内の `*` は自動的に `+` に置換される（フィールド区切りとの衝突回避）。
- `output_format` で指定したインデックスがフィールド数を超える場合、そのログ行はスキップされる（初期化コミットなど）。

---

## 11. 拡張・実装時の指針

新しいアプリケーションを `shellarc_core` 上に実装する場合、以下の順序で理解・実装することを推奨します（元ドキュメントの構成に準拠）。

1. `$SHELLARC_PROJECT_CTX` 配下の3ファイル（`project_settings.json`, `spreadsheet_map.json`, `.env`）を用意する。
2. `Git_IO.make_proj_repo()` で新規プロジェクトのGitリポジトリを初期化する（初回のみ）。
3. `cloudio` 層のクラス（`Git_IO`, `R2_IO`, `GCP_IO`, `Notion_IO`）を直接使うのではなく、`operations` 層（`ShellArc_Upload` など）を参考にユースケース単位のクラスを組み立てる。
4. 例外は `ShellArcException` 系と `ShellArcError` 系を区別してハンドリングし、前者は `frontend_msg` をそのままユーザーに提示し、後者は固定の技術班連絡メッセージを提示する。

内部メソッド（`_` プレフィックス）は動作理解のために本ドキュメントおよび元の `shellarc_core_api_guide.md` に記載されていますが、外部から直接呼び出すことは推奨されません。