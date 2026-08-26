# shellarc_core

### *日本語版はこちら → [README_jpn.md](./README_jpn.md)*

Anime and video production is full of small headaches — "where's that file?", "who approved this again?", "oops, forgot to update the spreadsheet…". `shellarc_core` takes care of all of that for you, automatically.

Plug it into whatever front end you like — a Discord bot, a Slack bot, a web dashboard, a CLI tool — and let `shellarc_core` handle everything happening behind the scenes.

---

## 🎬 What can you actually do with it?

- **📁Stop hunting for files**
  Every submission is automatically tracked with who submitted it, when, and which version. No more digging through a shared drive for `_final_v3_actually_final.blend`.

- **✅Approve once, and everything updates itself**
  When a director approves or rejects something, the progress spreadsheet's status text and cell colors update automatically. Nobody has to manually edit a tracking sheet ever again.

- **🖼️Storyboards, handled too**
  Upload and manage storyboard images without touching the Notion API directly — the library takes care of URLs and progress updates for you.

- **🔄Reuse assets across cuts without duplicating them**
  Want to use the same background in two different cuts? Reference it, or make a full copy — either way it's one function call, and it flows through the same review process as a normal submission.

- **📦Big files just work**
  Small files come back as ready-to-use local paths; larger ones automatically switch to signed download URLs. No need to hold huge files in memory on the bot or app side.

- **📜Full history, on demand**
  Pull the submission and approval history for any cut, any time. Perfect for dashboards, a Discord `/history cut5` command, or audit logs.

---

## ✨ What makes it different?

- **🔌You build the interface, the library runs the pipeline**
  Whether it's Discord, Slack, a web app, or a plain CLI, you're calling the same small set of classes under the hood. All the tricky logic for tying together Git, storage, spreadsheets, and Notion is already solved.

- **🎯State never gets out of sync**
  Git is the single source of truth, and everything else (like your spreadsheet) is just a reflection of it. You'll never end up with "the spreadsheet says approved but the actual file was never reviewed."

- **🔍Errors tell you whose problem they are**
  Every error is sorted into either "something the user needs to fix" (with a message you can show as-is) or "something actually broken in the system" (meant for whoever runs the pipeline). No guessing which one you're looking at.

- **🚀A ready-to-run setup, out of the box**
  You don't have to write a single line of code to get started — a full Discord bot suite (submission, approval, history, and more) comes ready to use. Or build your own front end on top of the same library if you'd rather.

---

## 🚀 Getting started

Setup instructions live in [DOCS/HOW_TO_START.md](./DOCS/HOW_TO_START.md) — start there.

If you want to go deeper into internal design or the full API, check these out too:

- 🏛️[ARCHITECTURE.md](./DOCS/ARCHITECTURE.md) — internal design, data model, processing flow
- 📖[shellarc_core_api_guide.md](./shellarc_core_api_guide.md) — full API reference

---

*This project is licensed under the Apache 2.0 License - see the [LICENSE](./LICENSE) file for details.*