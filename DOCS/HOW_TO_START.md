# Getting started with shellarc_core

### *日本語版はこちら → [HOW_TO_START_jpn.md](../DOCS_jpn/HOW_TO_START_jpn.md)*

This guide walks you through setting up and running `shellarc_core`. For an overview of what the project does, see [README.md](../README.md).

---

## 🚀 Quick start: no code required, up and running as a Discord server

ShellArc ships with a full Discord bot suite as its standard front end. Everything described in the overview - submissions, reviews, progress tracking - is already implemented as Discord commands and buttons. All you need to do is configure and deploy; you don't need to write any application code.

| docker-compose service | Dockerfile used | Discord commands added |
|---|---|---|
| `bot` (main workflow bot) | `Dockerfile.dc` | `..up` submit a file ・ `..upbig` submit a large file via a temporary upload link ・ `..appr` approve/reject via buttons ・ `..dl` download a take ・ `..check` check pending review status ・ `..reg` register as an assignee ・ `..history` look up submission/approval history ・ `..ask` "what's my assigned work?" ・ `..sync` sync local Git to remote |
| `itemi_action` (progress tracking / reminder bot) | `Dockerfile.itemi` | `..lo` upload/download/repoint storyboard images ・ `..remind` schedule a reminder ・ `..daiben` relay a message on someone's behalf |
| `ai_chat` (AI chat bot) | `Dockerfile.nullai` | `..nuru` ask the AI assistant (via Dify) ・ `..summary` summarize the message you replied to ・ `..weather` check the weather |

### 1. Prepare a project context directory

```
project_ctx/
├── project_settings.json     # core library configuration
├── spreadsheet_map.json      # core library configuration
├── discord_config.json       # command prefix, channel/role mapping, etc.
└── .env                      # credentials for each service + Discord bot tokens
```

In addition to the core library's own credentials, `.env` needs the following:

```dotenv
Discord_token=...              # for the main "bot" service
Discord_pmmanager_token=...    # for the itemi_action service
Discord_charbot_token=...      # for the ai_chat service
Discord_server_id=...
Dify_token=...                 # only needed for the ai_chat service
Dify_baseurl=...
```

`discord_config.json` controls per-server behavior (command prefix, channel/role names, how cut numbers are extracted, etc.). See the bot's source code for the specific fields.

### 2. Turn the template into a real `docker-compose.yml`

`docker-compose_yml.template` contains placeholders that need to be filled in before production use.

```bash
cp docker-compose_yml.template docker-compose.yml
```

Inside `docker-compose.yml`, edit these two kinds of placeholders:

**a. Git identity - the `###` placeholders (`bot` service only)**

Every submission and approval is recorded as a Git commit. Git needs an author/committer identity to create a commit. This is separate from the `submitter_name` and `reviewer_name` stored in the commit message - set a fixed identity representing the bot process itself.

```yaml
environment:
  - SHELLARC_PROJECT_CTX
  - GIT_AUTHOR_NAME=ShellArc Bot
  - GIT_AUTHOR_EMAIL=shellarc-bot@yourproject.local
  - GIT_COMMITTER_NAME=ShellArc Bot
  - GIT_COMMITTER_EMAIL=shellarc-bot@yourproject.local
```

**b. Persistent volumes - the `~_in_code:~_in_server` placeholders**

Each of these is a `<host path or named volume>:<container path>` pair. The left side is where the data actually lives (so it survives container rebuilds); the right side is the path the container expects.

| Placeholder | Used by | Stores | Must match |
|---|---|---|---|
| `version_management_dir_in_code:actual_version_management_dir_in_server` | `bot`, `itemi_action`, `ai_chat` | The Git repository holding submission/approval state (`Git_IO`) | `git_repo_local` in `project_settings.json` |
| `itemi_action_dir_in_code:itemi_action_dir_in_server` | `itemi_action` only | Persistent data for the reminder scheduler (`ShellArc_ScheduleManager`) | `schedule_path` in `discord_config.json` |
| `.config_dir_in_code:.config_dir_in_server` | `itemi_action` only | The container's standard Linux `~/.config` directory, used by libraries like `platformdirs`/`keyring` (see `pyproject.toml`) for persisting credentials/cache | The container user's `~/.config` (e.g. `/root/.config` if running as root) |

Example (assuming `project_settings.json` sets `"git_repo_local": "/data/git_repo"`):

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

**Important**: the volume for the Git repository must mount the **same volume and the same container-side path** across all three services. If `bot` / `itemi_action` / `ai_chat` end up using different volumes or paths, each service will see its own (unsynced) copy of the repository.

### 3. Point at your project context

```bash
export SHELLARC_PROJECT_CTX=/path/to/project_ctx
```

### 4. Start all three bots with Docker Compose

```bash
docker compose up -d --build
```

This builds and starts the `bot`, `itemi_action`, and `ai_chat` containers. All three mount the same project context directory and share the same Git version-control volume, so they always see the same pipeline state.

### 5. Use it on Discord

```
..up            # attach a file, pick the component from the dropdown, confirm
..appr          # pick a component, choose "approve" or "needs revision"
..dl 0          # download the latest approved take
..history modeling 5    # last 5 submissions for "modeling"
```

That's it - the whole submit → review → track cycle works without writing a single line of Python.

---

## 🛠️ shellarc_devkit - supporting tools

Separate from the Discord front end, `shellarc_devkit` includes a few standalone scripts to help set up and maintain a project. None of them depend on the Discord bots being up.

| Script | What it does |
|---|---|
| `project_init_cli.py` | An interactive wizard for setting up a new project. It initializes the Git repository (`Git_IO.make_proj_repo`), checks connectivity to your spreadsheet, and - if you want - writes a header row and cut-number column into a new spreadsheet automatically. |
| `cloud_access_check.py` | Checks connectivity to Firebase, Cloudflare R2, and Google Spreadsheet all at once. Handy before a deploy, or as a first triage step when part of the pipeline suddenly stops responding. |
| `backup_on_local.py` + `init_settings.sh` | A backup batch that team members run on their own (or a shared) machine to pull newly submitted cut assets from R2 into a local folder. It's an independent, personal safety net separate from the main pipeline. |

### Setting up the local backup batch

This isn't run centrally - it's meant to be distributed to each team member individually.

1. Put `backup_on_local.py`, `init_settings.sh`, `requirements.txt`, and a `.env` (containing R2 credentials) together in one folder (e.g. `~/shellarc_backup/`).
2. Run the setup script once.
   ```bash
   bash init_settings.sh
   ```
   This creates a dedicated virtualenv, installs dependencies, registers `SHELLARC_LOCAL_BACKUP` (the parent of that folder) in your shell config, and sets up a `nuru` alias.
3. After reloading your shell (`source ~/.zshrc`), just run:
   ```bash
   nuru
   ```
   any time you want to pull in everything submitted since the last backup. The last backup time is recorded in `backup_config.json`, so each run only fetches the difference.

---

## Building your own front end

If you don't want to use Discord, the quick start above is just one example front end built on the same library. To build your own - a Slack bot, a web dashboard, a CLI, whatever - you'll need a project context directory (project settings, spreadsheet mapping, credentials for each service) and a one-time Git repository initialization, which you can do interactively with `project_init_cli.py` above. Once that's done, day-to-day usage is just the classes under `operations`.

For the exact configuration file formats and full API details (arguments, return values, exceptions raised), see the design docs and API reference.

- [ARCHITECTURE.md](./ARCHITECTURE.md) - internal design, data model, processing flow
- [shellarc_core_api_guide.md](../shellarc_core_api_guide.md) - full API reference