# shellarc_core

### *日本語版は [README_jpn.md](./README_jpn.md) をご覧ください。*

`shellarc_core` turns the messy, manual side of anime/video production pipelines — chasing file versions, updating spreadsheets, tracking who approved what — into a few lines of code. It's a backend library you can drop into a Discord bot, a Slack bot, a web dashboard, or a CLI tool to run your production pipeline for you.

Under the hood it coordinates Git, Cloudflare R2, Google Spreadsheet, Notion, and Firebase — but as someone building on top of it, you mostly just call things like `upload_file()` or `pending_action()` and the rest happens automatically.

---

## What you can build with it

### 🎬 A submission pipeline that never loses a version
Every file a team member submits is versioned like code. Ask for "the latest approved version" or "what's currently in review" and get it back instantly — no more digging through shared drives for `_final_v3_REALLY_FINAL.blend`.

```python
uploader = ShellArc_Upload(cut_num=5, working_component="modeling")
await uploader.upload_file(
    file={"cut5_model_v1.blend": file_bytes},
    submitter_name="YamadaTaro",
    message="First pass"
)
```

### ✅ A review/approval flow that updates itself
When a director approves or rejects a submission, the library handles the Git-side bookkeeping *and* pushes the change to the production spreadsheet — status text, cell color, everything — so nobody has to update the tracker by hand.

```python
review = ShellArc_Review(cut_num=5, reviewing_component="modeling")
await review.pending_action(reviewer_name="DirectorSato", is_approve=True)
```

### 📊 A progress tracker that's always up to date
Assignee names, work status, and completion state on your team's spreadsheet update automatically as work moves through the pipeline — you never write directly to the sheet yourself.

```python
register = ShellArc_Register()
await register.register_work(
    registering_person="YamadaTaro",
    registering_component="modeling",
    registering_cut=5
)
```

### 🖼️ Storyboard management, handled
Upload and fetch storyboard images through Notion without touching the Notion API directly — the library manages the URLs and progress updates for you.

### 🔁 Reuse work across cuts without duplicating files
Two cuts share the same background? Point one cut's component at another's data (a lightweight reference) or copy it outright — both are one function call, and both flow through the same review process as any other submission.

### 📦 Big files just work
Files under 10MB come back as a ready-to-send local path. Bigger files automatically get a presigned upload/download URL instead, so your bot or app never has to hold a huge file in memory.

### 🔍 Full history, queryable on demand
Pull submission history, approval history, or the current component list for any cut — useful for building dashboards, Discord commands like `/history cut5`, or audit logs.

```python
history = await ShellArc_Query.get_history(cut_num=5, component="modeling", max_length=10)
```

---

## 🚀 Quick Start: run it as a Discord server, no code required

ShellArc ships with a ready-made Discord frontend — three bots that already wire up everything above to Discord commands and buttons. You configure and deploy; you don't write application code.

| Docker Compose service | Dockerfile | What it adds to your Discord server |
|---|---|---|
| `bot` — main workflow bot | `Dockerfile.dc` | `..up` submit a file · `..upbig` submit a large file via a temporary upload link · `..appr` approve/reject via buttons · `..dl` download a take · `..check` check what's pending · `..reg` register an assignee · `..history` view submission/approval history · `..ask` "what am I assigned to" · `..sync` push local Git to the remote |
| `itemi_action` — PM/reminder bot | `Dockerfile.itemi` | `..lo` upload/download/repoint a storyboard image · `..remind` schedule a reminder · `..daiben` relay a message to someone on someone else's behalf |
| `ai_chat` — AI chat bot | `Dockerfile.nullai` | `..nuru` ask an AI assistant (via Dify) · `..summary` summarize a replied-to message · `..weather` look up the weather |

### 1. Prepare a project context directory

```
project_ctx/
├── project_settings.json     # core library configuration
├── spreadsheet_map.json      # core library configuration
├── discord_config.json       # bot command prefix, channel/role mapping, etc.
└── .env                      # service credentials + Discord bot tokens
```

On top of the core library's own credentials, `.env` additionally needs:

```dotenv
Discord_token=...              # main "bot" service
Discord_pmmanager_token=...    # itemi_action service
Discord_charbot_token=...      # ai_chat service
Discord_server_id=...
Dify_token=...                 # only needed for the ai_chat service
Dify_baseurl=...
```

`discord_config.json` controls per-server behavior (command prefix, channel/role names, cut-number parsing, etc.) — see the bot source for the fields it reads.

### 2. Turn the template into a real `docker-compose.yml`

`docker-compose_yml.template` ships with placeholder values that must be filled in before it can run in production.

```bash
cp docker-compose_yml.template docker-compose.yml
```

Then edit two kinds of placeholders in `docker-compose.yml`:

**a. Git identity — the `###` placeholders (`bot` service only)**

Every submission and approval is recorded as a Git commit. Git needs an author/committer identity to make that commit — this is separate from `submitter_name`/`reviewer_name`, which are stored inside the commit message itself. Set it to a fixed identity representing the bot process:

```yaml
environment:
  - SHELLARC_PROJECT_CTX
  - GIT_AUTHOR_NAME=ShellArc Bot
  - GIT_AUTHOR_EMAIL=shellarc-bot@yourproject.local
  - GIT_COMMITTER_NAME=ShellArc Bot
  - GIT_COMMITTER_EMAIL=shellarc-bot@yourproject.local
```

**b. Persistent volumes — the `..._in_code:..._in_server` placeholders**

Each of these is a `<host path or named volume>:<container path>` pair: the left side is where the data actually lives (so it survives container rebuilds), the right side is the path the container expects.

| Placeholder | Used by | What it stores | Container-side path must match |
|---|---|---|---|
| `version_management_dir_in_code:actual_version_management_dir_in_server` | `bot`, `itemi_action`, `ai_chat` | The Git repository holding submission/approval state (`Git_IO`) | `git_repo_local` in `project_settings.json` |
| `itemi_action_dir_in_code:itemi_action_dir_in_server` | `itemi_action` only | Persistent storage for the reminder scheduler (`ShellArc_ScheduleManager`) | `schedule_path` in `discord_config.json` |
| `.config_dir_in_code:.config_dir_in_server` | `itemi_action` only | Linux's standard `~/.config` directory inside the container — used by libraries such as `platformdirs`/`keyring` (see `pyproject.toml`) to persist credentials/cache | The container user's `~/.config` (e.g. `/root/.config` if running as root) |

Example, assuming `project_settings.json` sets `"git_repo_local": "/data/git_repo"`:

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

**Important**: all three services must mount the *same* volume to the *same* container-side path for the Git repository. If `bot`, `itemi_action`, and `ai_chat` each get a different volume (or different path), they'll each see their own out-of-sync copy of the repository instead of sharing one.

### 3. Point at your project context

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_ctx
```

### 4. Launch all three bots with Docker Compose

```bash
docker compose up -d --build
```

This builds and runs three containers — `bot`, `itemi_action`, `ai_chat` — each mounting your project context directory and sharing the same Git version-management volume, so all three always see the same pipeline state.

### 5. Use it from Discord

```
..up            # attach a file, pick the component from the dropdown, confirm — done
..appr          # pick a component, then 確定 (approve) or 要修正 (request changes)
..dl 0          # download the latest approved take
..history modeling 5    # last 5 submissions for "modeling"
```

That's the whole submit → review → track loop, without touching a line of Python.

---

## Why this shape works well

- **You build the interface, the library runs the pipeline.** Whether you want a Discord bot, a Slack app, a web dashboard, or a plain CLI, you're just calling the same handful of `operations` classes — the pipeline logic (Git, storage, spreadsheet, Notion) is already solved for you.
- **State never gets out of sync.** Because Git is the single source of truth and every other service is just a reflection of it, you don't end up with a spreadsheet that says "approved" while the actual file is still unreviewed.
- **Errors tell you who to blame — in a good way.** Every error is tagged as either "the user needs to fix something" (with a message you can show them directly) or "something's actually broken" (flagged for whoever maintains the pipeline). You never have to guess which.

---

## Building your own frontend

Don't want Discord? The Quick Start above is just one frontend built on the same library. To build your own (Slack bot, web dashboard, CLI), you'll need a project context directory (project settings, spreadsheet mapping, service credentials) and a one-time Git repository initialization. Once that's done, the `operations` classes shown earlier are all you need for day-to-day use.

For the exact setup steps, configuration file formats, and full API reference (arguments, return values, exceptions), see the design and API documentation:

- [ARCHITECTURE.md](./DOCS/ARCHITECTURE.md) — internal design, data model, and processing flows
- [shellarc_core_api_guide.md](./shellarc_core_api_guide.md) — the complete API specification

---

*This project is licensed under the Apache 2.0 License - see the [LICENSE](./LICENSE) file for details.*