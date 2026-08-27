# ARCHITECTURE.md - `shellarc_core` Internal Design Document

> This document explains the internal architecture, layer structure, data model, and key workflows of `shellarc_core`. For usage instructions (installation, quick start), see [README.md](../README.md).

---

## Table of Contents

- [ARCHITECTURE.md - `shellarc_core` Internal Design Document](#architecturemd--shellarc_core-internal-design-document)
  - [Table of Contents](#table-of-contents)
  - [1. Design Philosophy](#1-design-philosophy)
  - [2. Layered Architecture](#2-layered-architecture)
  - [3. Domain Model](#3-domain-model)
  - [4. Mapping to External Services](#4-mapping-to-external-services)
  - [5. Configuration Files and Data Flow](#5-configuration-files-and-data-flow)
  - [6. Git Repository Data Model](#6-git-repository-data-model)
  - [7. Concurrency Control](#7-concurrency-control)
  - [8. Exception Design](#8-exception-design)
    - [8-1. User-Caused Exceptions (`user_exception.py`)](#8-1-user-caused-exceptions-user_exceptionpy)
    - [8-2. System-Caused Exceptions (`structure_error.py`)](#8-2-system-caused-exceptions-structure_errorpy)
  - [9. Key Processing Flows](#9-key-processing-flows)
    - [9-1. Material Submission (Upload) Flow](#9-1-material-submission-upload-flow)
    - [9-2. Review (Approval / Rejection) Flow](#9-2-review-approval--rejection-flow)
    - [9-3. Download Flow](#9-3-download-flow)
    - [9-4. Repoint (Reference) vs. Absorption (Copy)](#9-4-repoint-reference-vs-absorption-copy)
  - [10. Git Commit Message Specification](#10-git-commit-message-specification)
  - [11. Guidelines for Extension / Implementation](#11-guidelines-for-extension--implementation)

---

## 1. Design Philosophy

`shellarc_core` is a backend library that automates the "cut-level material submission → review → approval" workflow used in anime/video production, spanning multiple cloud services (Cloudflare R2 / Google Spreadsheet / Git / Notion / Firebase Firestore).

The design centers on three main points:

- **Git as the single source of truth**: A cut's submission history, approval state, and version history are all represented through Git commit history and branch structure. Spreadsheet and Notion are "display layers for humans" - secondary stores that merely reflect Git's state.
- **Separation of layers**: "Reading configuration (cfg)", "authenticating with external services (auth)", "actual I/O with external services (cloudio)", and "business logic (operations)" are clearly separated, so upper layers don't need to know implementation details of lower layers (e.g., how an API client is constructed).
- **Two-way split of exceptions**: Errors caused by "user actions" and errors caused by "system/configuration/external service issues" are separated at the type level, allowing the calling application to handle each differently (see below).

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│  operations/           Business logic layer (reference   │
│  uploader / requesting / reviewing / register /          │  implementations for consumers)
│  storyboard / query                                       │
└───────────────────────┬─────────────────────────────────┘
                          │ calls
┌───────────────────────▼─────────────────────────────────┐
│  cloudio/              Cloud I/O layer                     │
│  io_git / io_spreadsheet / io_r2 / io_notion              │
└───────────────────────┬─────────────────────────────────┘
                          │ requests credentials
┌───────────────────────▼─────────────────────────────────┐
│  auth/                 Authentication layer                │
│  access_r2 / access_spread_sheet / access_database /      │
│  access_notion                                             │
└───────────────────────┬─────────────────────────────────┘
                          │ reads .env
┌───────────────────────▼─────────────────────────────────┐
│  cfg/                  Configuration layer                 │
│  cfg_io (project_settings.json) /                          │
│  spreadsheet_map_io (spreadsheet_map.json)                │
└─────────────────────────────────────────────────────────┘

  Cross-cutting concerns:
  ┌─────────────────┐   ┌─────────────────────────┐
  │ utils/           │   │ exception/               │
  │ file_operation   │   │ user_exception /         │
  │ (naming, ZIP)    │   │ structure_error          │
  └─────────────────┘   └─────────────────────────┘
```

**Dependencies always flow in one direction, top to bottom.** `operations` uses `cloudio`, and `cloudio` uses `auth` and `cfg`, but there is never a dependency in the reverse direction. `utils` and `exception` are cross-cutting modules referenced from every layer.

| Layer | Responsibility | Main Classes |
|---|---|---|
| cfg | Loading project settings / spreadsheet mapping JSON | `Cfg_IO`, `SpreadsheetMap_IO` |
| auth | Reading credentials from `.env` and initializing each service's SDK client | `Cloudflare_R2_service_Access`, `AccessSpreadSheet`, `AccessDB`, `Notion_Access` |
| cloudio | Actual read/write operations (CRUD) against each external service | `Git_IO`, `GCP_IO`, `R2_IO`, `Notion_IO` |
| utils | Local file operations, naming rules, ZIP compression, and other helpers | `FileOperation` |
| exception | Exception hierarchy for user-caused vs. system-caused errors | `ShellArcException` family, `ShellArcError` family |
| operations | Use-case implementations combining the above (reference implementations) | `ShellArc_Upload`, `ShellArc_Request`, `ShellArc_Review`, `ShellArc_Register`, `ShellArc_Storyboard`, `ShellArc_Query` |

---

## 3. Domain Model

| Concept | Identifier | Description |
|---|---|---|
| Cut | `cut_num: int` | The smallest unit of work in video production |
| Component | `str` (e.g. `modeling`, `texturing`) | A type of work that makes up a cut |
| Take | Corresponds to a Git commit | A submitted version of a component |
| Pending | Git `pending` branch | A submission awaiting review |

**Relationships**: A cut has multiple components, and each component can have multiple takes (submissions). Each take is recorded as a Git commit, and once approved, is reflected from the `pending` branch to the `main` branch.

---

## 4. Mapping to External Services

| Service | Role | Corresponding I/O Class |
|---|---|---|
| Cloudflare R2 (S3-compatible) | Storage for the actual material files | `R2_IO` |
| Google Spreadsheet | Progress / assignee tracking ledger (human-facing display) | `GCP_IO` |
| Git (local + remote) | Source of truth for per-cut version control and approval flow | `Git_IO` |
| Notion | Management of layout images (storyboards) | `Notion_IO` |
| Firebase Firestore | General-purpose database (e.g. credential management) | `AccessDB` (only documented at the `auth` layer; no corresponding `cloudio` class is documented) |

**Important design consequence**: Storage is fully separated by responsibility - material files live in R2, submission/approval "state" lives in Git, and human-facing progress display lives in Spreadsheet. During a single submission (`upload_file`), writes are made in order to these three: Git → R2 → Spreadsheet.

---

## 5. Configuration Files and Data Flow

All configuration is consolidated into the directory pointed to by the `SHELLARC_PROJECT_CTX` environment variable.

```
$SHELLARC_PROJECT_CTX/
├── project_settings.json   # Base project settings & component definitions → read by Cfg_IO
├── spreadsheet_map.json    # Spreadsheet cell coordinate mapping → read by SpreadsheetMap_IO
└── .env                    # Credentials for each service → read by each Access class under auth/
```

`Cfg_IO` and `SpreadsheetMap_IO` are designed to **load their JSON exactly once, in the constructor**. Classes in the `cloudio` layer (`GCP_IO`, `R2_IO`, `Git_IO`, etc.) use these internally to resolve default values such as bucket name, spreadsheet key, and Git repository path. As a result, classes in the `operations` layer generally don't need to pass these paths or keys explicitly.

---

## 6. Git Repository Data Model

```
{git_repo_local}/
├── project_main.json        # Per-cut component definitions ("common" + per-cut overrides)
└── stage/
    ├── cut1/
    │   ├── modeling.json          # {"creator": ..., "fileindex": ...} or {"repointer": N}
    │   ├── .sa_pending_modeling   # Present only when a review is pending
    │   └── texturing.json
    └── cut2/ ...
```

- **`project_main.json`**: The `common` key defines the default component composition for all cuts. If a `cut{N}` key exists, it overrides `common` for that cut only.
- **Component JSON (normal submission)**: Takes the form `{"creator": "submitter name", "fileindex": "cut1_modeling_abc123_20240101120000"}`. `fileindex` uniquely identifies the file in R2.
- **Component JSON (repoint)**: Takes the form `{"repointer": 3}`. This cut's data **references** the data of the specified cut number (`3` in this example) rather than copying it. `get_component_info()` detects this key and automatically resolves the reference recursively.
- **`.sa_pending_{component}`**: An empty file. Its presence indicates that the component is awaiting review - a "flag file" outside Git's normal tracking, checked via the output of `git status --porcelain`.

Two branches always exist:

| Branch | Meaning |
|---|---|
| `pending` | Work-in-progress / awaiting-review data. All submissions (SUBMIT) are committed here first |
| `main` | Approved, finalized data. Only content approved via `pend_data()` is reflected here |

---

## 7. Concurrency Control

`Git_IO` holds a class variable `_git_lock = asyncio.Lock()`, and the following write methods are **exclusively locked at the class level**:

- `update_data` (new submission)
- `pend_data` (approval / rejection)
- `repoint_data` (repointing a reference)

On the other hand, **`absorb_data` (copying data by value) does not acquire the lock**. This asymmetry is explicitly documented in the source material - if you call `absorb_data` concurrently with other write operations, you should consider adding your own exclusion control at the call site.

This locking exists because the local Git working directory (working tree) is singular. Running multiple submission/approval operations concurrently in an async environment can cause `git checkout` conflicts, which is why this exclusion control is required.

---

## 8. Exception Design

Exceptions fall into two families depending on whether the cause lies with the user or with the system. Internally, both use a shared classification enum, `SA_ExceptionType`.

### 8-1. User-Caused Exceptions (`user_exception.py`)

These inherit from the base class `ShellArcException` and carry a `frontend_msg` property that can be shown directly in the UI.

| Class | Purpose |
|---|---|
| `SA_DataNotExist` | Referenced data does not exist |
| `SA_InvalidUserQuery` | An invalid request (e.g. a disallowed file format) |
| `SA_InvalidRequestObj` | Reference to a nonexistent object (e.g. an unsubmitted cut) |
| `SA_EditingRejection` | Prevents an unintended overwrite (e.g. an assignee is already registered) |
| `SA_SapycSyntaxError` | A proprietary syntax error |

### 8-2. System-Caused Exceptions (`structure_error.py`)

These inherit from the base class `ShellArcError`, and `frontend_msg` is always the fixed string `"Please contact the tech team: {error_code.name}"`. `error_code` is further subdivided via the `SA_ErrorCode` enum, and an `is_fatal` flag controls log severity.

| Class | Typical Error Codes | `is_fatal` |
|---|---|---|
| `SA_ProjStructError` | SA_4001, SA_4002, SA_6001, SA_6002 | True |
| `SA_RequestItemError` | SA_5001, SA_5002 | False |
| `SA_CommunicationError` | SA_3000, SA_8001 | True |
| `SA_AuthError` | SA_9000, SA_9001 | True |
| `SA_LocalIOError` | SA_8000, SA_8002 | True |
| `SA_InternalSyntaxError` | SA_7000 | True |

**Design intent**: This two-way split lets the calling application mechanically distinguish, purely by exception type, between "errors where the user should retry the operation" (`ShellArcException` family) and "fatal errors that developers/operators should be notified about" (`ShellArcError` family).

---

## 9. Key Processing Flows

### 9-1. Material Submission (Upload) Flow

```
ShellArc_Upload.upload_file()
  1. Check the component's allowed formats
  2. If multiple files & zip is allowed → FileOperation.make_zip() zips the PNGs
  3. Git_IO.update_data()
       → checkout the pending branch
       → write stage/cut{N}/{component}.json (SUBMIT commit)
       → create .sa_pending_{component}
       → return file_index_name
  4. R2_IO.upload_file()
       → upload to {collection_name}/stage/{file_index_name}.{format}
  5. GCP_IO.update_info()  → {component}_PIC = submitter_name
  6. GCP_IO.update_info()  → {component}_progress = "In Progress"
  7. GCP_IO.color_cell()   → color the {component}_PIC cell yellow (1,1,0)
```

### 9-2. Review (Approval / Rejection) Flow

```
ShellArc_Review.pending_action()
  1. Check for the existence of .sa_pending_{component}
     (raises SA_InvalidRequestObj if it doesn't exist)
  2. Git_IO.pend_data()
     On approval:
       → delete .sa_pending_{component}
       → APPROVE commit on the pending branch
       → checkout the main branch
       → bring the pending JSON into main, APPROVE commit on main as well
     On rejection:
       → delete .sa_pending_{component}
       → DECLINE commit on the pending branch only (not reflected to main)
  3. (approval only) GCP_IO.update_info() → {component}_progress = "Complete"
  4. (approval only) GCP_IO.color_cell()  → color the {component}_PIC cell green (0,1,0)
```

Rollback: if a Git command fails at step 2, `.sa_pending_{component}` is recreated and then `SA_LocalIOError(SA_8002)` is raised.

### 9-3. Download Flow

```
ShellArc_Request.download_material(requesting_take)
  requesting_take:
    "0"  → main branch (latest finalized version)
    "-1" → pending branch (latest work-in-progress)
    other → a specific commit ID
  1. Git_IO.get_component_info() retrieves the component JSON (repointer is auto-resolved)
  2. Resolve the R2 file path from fileindex
  3. Check the file size
       > 10 MB → R2_IO.issue_presigned_url() returns a presigned URL
       ≤ 10 MB → R2_IO.download_file() saves to a local temp file and returns its path
```

### 9-4. Repoint (Reference) vs. Absorption (Copy)

| | `repoint_data` | `absorb_data` |
|---|---|---|
| Meaning | A **reference** to another cut's data | A **value copy** of another cut's data |
| Acquires lock | Yes | **No** |
| Commit type | `REPOINT` | `ABSORPTION` |
| If the referenced data is later updated | Automatically reflected (resolved on each access) | Not reflected (fixed at copy time) |

Both are reflected to the `main` branch only after going through review approval (`pend_data`).

---

## 10. Git Commit Message Specification

Every commit is recorded in a fixed `*`-delimited format, which `get_log()` parses.

```
{commit_type} * {cut_num} * {component} * {creator_name} * {message} * {timemark} * {file_index_name}
```

| Index | Field | Example |
|---|---|---|
| 0 | `commit_type` | `SUBMIT` / `APPROVE` / `DECLINE` / `REPOINT` / `ABSORPTION` |
| 1 | `cut_num` | `5` |
| 2 | `component` | `modeling` |
| 3 | `creator_name` | `YamadaTaro` (fixed string for REPOINT/ABSORPTION) |
| 4 | `message` | `No message` |
| 5 | `timemark` | `20240101120000` (JST) |
| 6 | `file_index_name` | `cut5_modeling_abc123_20240101120000` (`5->3` format for REPOINT/ABSORPTION) |

**Notes:**
- Any `*` in a user-supplied `message` is automatically replaced with `+` (to avoid colliding with the field delimiter).
- If an index specified in `output_format` exceeds the number of fields in the commit message, that log line is skipped (e.g. for initialization commits).

---

## 11. Guidelines for Extension / Implementation

When building a new application on top of `shellarc_core`, the recommended order of understanding/implementation is as follows :

1. Prepare the three files under `$SHELLARC_PROJECT_CTX` (`project_settings.json`, `spreadsheet_map.json`, `.env`).
2. Initialize the Git repository for a new project with `Git_IO.make_proj_repo()` (one-time only).
3. Rather than using `cloudio`-layer classes (`Git_IO`, `R2_IO`, `GCP_IO`, `Notion_IO`) directly, build use-case-level classes by following the reference implementations in the `operations` layer (e.g. `ShellArc_Upload`).
4. Distinguish between the `ShellArcException` and `ShellArcError` families when handling exceptions: present `frontend_msg` directly to the user for the former, and present the fixed tech-team-contact message for the latter.

Internal methods (prefixed with `_`) are documented for the sake of understanding behavior, both here and in the original `shellarc_core_api_guide.md`, but are not recommended for direct external use.
