# shellarc_core

### 日本語バージョンについては、[README_jpn.md](./README_jpn.md) をご参照ください。

`shellarc_core` is a pipeline backend framework library for **cut management** in anime/video production. It combines the following cloud services to automate version control, review flow, and progress tracking for cut materials.

| Service | Purpose |
|---|---|
| **Cloudflare R2** (S3-compatible) | Storage for material files |
| **Google Spreadsheet** | Progress / assignee tracking ledger |
| **Git** (local + remote) | Per-cut version control and approval flow |
| **Notion** | Management of layout images (storyboards) |
| **Firebase Firestore** | General-purpose database (e.g. credential management) |

For internal design, layer structure, and data flow details, see [ARCHITECTURE.md](./DOCS/ARCHITECTURE.md). This README focuses on "how to use it."

---

## Table of Contents

- [Basic Concepts](#basic-concepts)
- [Setup](#setup)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Exception Handling](#exception-handling)
- [Reference: Use Case List](#reference-use-case-list)

---

## Basic Concepts

| Term | Description |
|---|---|
| Cut | The smallest unit of work in video production, identified by `cut_num` (int) |
| Component | A type of work that makes up a cut (e.g. `modeling`, `texturing`) |
| Take | A submitted version of a component; corresponds to a Git commit |
| Pending | A submission awaiting review, managed via Git's `pending` branch |

---

## Setup

### 1. Environment Variable

Set `SHELLARC_PROJECT_CTX` (required) to the absolute path of the project context directory.

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_context
```

### 2. Prepare the Project Context Directory

Place the following three files in this directory.

```
$SHELLARC_PROJECT_CTX/
├── project_settings.json   # Project settings (bucket name, component definitions, etc.)
├── spreadsheet_map.json    # Spreadsheet cell coordinate mapping
└── .env                    # Credentials for each service
```

**Example `project_settings.json`:**

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

**Example `spreadsheet_map.json`:**

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

**Variables required in `.env`:**

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

### 3. Initialize the Git Repository for a New Project (one-time only)

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

This creates a repository with `main` / `pending` branches at `git_repo_local`, along with `stage/cut{N}/` directories for every cut.

---

## Quick Start

### Submitting a Material (Upload)

```python
from shellarc_core.operations.uploader import ShellArc_Upload

uploader = ShellArc_Upload(cut_num=5, working_component="modeling")

await uploader.upload_file(
    file={"cut5_model_v1.blend": file_bytes},
    submitter_name="YamadaTaro",
    message="Initial submission"
)
```

### Downloading a Material

```python
from shellarc_core.operations.requesting import ShellArc_Request

req = ShellArc_Request(cut_num=5, requesting_component="modeling")

# "0" = latest finalized version (main) / "-1" = work in progress (pending) / other = specific commit ID
path_or_url, filename, type_indicator = await req.download_material("0")

if type_indicator == "url":
    print(f"Download URL: {path_or_url}")
else:
    with open(path_or_url, "rb") as f:
        file_bytes = f.read()
    import os
    os.unlink(path_or_url)  # Temp file — delete after use
```

### Review (Approve / Reject)

```python
from shellarc_core.operations.reviewing import ShellArc_Review

review = ShellArc_Review(cut_num=5, reviewing_component="modeling")
await review.pending_action(
    reviewer_name="DirectorSato",
    is_approve=True,
    message="Looks good, approved"
)
```

### Registering an Assignee

```python
from shellarc_core.operations.register import ShellArc_Register

register = ShellArc_Register()
await register.register_work(
    registering_person="YamadaTaro",
    registering_component="modeling",
    registering_cut=5
)
```

### Querying Submission History

```python
from shellarc_core.operations.query import ShellArc_Query

history = await ShellArc_Query.get_history(
    cut_num=5,
    component="modeling",
    max_length=10
)
# → {"abc1234": "20240101120000 YamadaTaro Initial submission", ...}
```

For other use cases (large-file uploads via presigned URL, storyboard upload/download, etc.), see [Key Processing Flows in ARCHITECTURE.md](./DOCS/ARCHITECTURE.md#9-key-processing-flows).

---

## Directory Structure

```
shellarc_core/
├── cfg/          # Loading configuration files (JSON)
├── auth/         # Authentication with each cloud service
├── cloudio/      # Actual CRUD operations against each cloud service
├── utils/        # Local file operation utilities
├── exception/    # Exception classes
└── operations/   # Business logic (reference implementations for library consumers)
```

Detailed responsibilities of each module are summarized in [ARCHITECTURE.md](./DOCS/ARCHITECTURE.md#2-layered-architecture).

---

## Exception Handling

`shellarc_core` exceptions fall into two families.

| Family | Base Class | Characteristics |
|---|---|---|
| User-caused | `ShellArcException` (`exception/user_exception.py`) | `frontend_msg` can be shown directly in the UI |
| System-caused | `ShellArcError` (`exception/structure_error.py`) | `frontend_msg` is a fixed string (`"Please contact the tech team: {error_code.name}"`) |

Representative user-caused exceptions: `SA_DataNotExist`, `SA_InvalidUserQuery`, `SA_InvalidRequestObj`, `SA_EditingRejection`

For the full list of exceptions and error codes, see [Exception Design in ARCHITECTURE.md](./DOCS/ARCHITECTURE.md#8-exception-design).

---

## Reference: Use Case List

| Use Case | Class Used |
|---|---|
| Submitting a material | `operations.uploader.ShellArc_Upload` |
| Large-file upload via presigned URL | `operations.uploader.ShellArc_Upload.get_upload_page` |
| Downloading a material | `operations.requesting.ShellArc_Request` |
| Review (approve / reject) | `operations.reviewing.ShellArc_Review` |
| Assignee registration | `operations.register.ShellArc_Register` |
| Storyboard upload / download | `operations.storyboard.ShellArc_Storyboard` |
| Querying submission / approval history | `operations.query.ShellArc_Query` |
| Initializing a new project | `cloudio.io_git.Git_IO.make_proj_repo` |

---

*This README and ARCHITECTURE.md were created based on the contents of `shellarc_core_api_guide.md`. For the complete specification of every public interface (argument types, raised exceptions, return value formats, etc.), refer to the original API guide.*