# Daily Task Log — Agent Instructions

> These instructions apply to all AI coding agents (Claude Code, Copilot, Cursor, etc.) working in this repository.

## What this project is

A lightweight Windows desktop app for logging daily work tasks. The guiding constraint is **minimal memory use** (~15–25 MB idle in tray). Tkinter was deliberately chosen over heavier UI frameworks. Do not suggest replacing it.

## Rules

### Dependencies
- Do not add new `pip` packages unless absolutely necessary and explicitly approved.
- Never suggest CustomTkinter, PyQt, or other GUI frameworks as a replacement.
- The only allowed runtime deps are in `requirements.txt`: openpyxl, pystray, winotify, Pillow, pyinstaller.

### Code quality
- No comments unless the reason behind the code is non-obvious to a future reader.
- No new abstractions for hypothetical future use. Three similar lines beats a premature helper.
- No error handling for internal invariants — only validate at system boundaries (file I/O, user input).
- Do not add backwards-compatibility stubs, feature flags, or unused exports.

### Windows-only
- The app is Windows-only. Do not add cross-platform fallbacks for tray, notifications, or registry access.
- `core/config.py:set_autostart()` uses `winreg` — keep it Windows-only.

### Excel file
- All task data I/O goes through `core/data.py` using openpyxl. Do not introduce a database or ORM.
- The Excel file path is user-configurable; always read it from config, not hardcoded.

### Dirty flag
- `App._dirty` in `main.py` controls History/Summary reload. Set it `True` in any code path that writes task or leave data. `_navigate()` clears it after calling `page.load()`.

## Key files

| File | Role |
|---|---|
| `main.py` | App entry point, sidebar nav, `THEMES` dict, `_NAV_KEY` constant, `_dirty` flag, tray startup |
| `core/config.py` | Registry + Excel Config sheet I/O; `_read_excel_config()` is the shared parsing helper; `DEFAULTS` is the schema |
| `core/data.py` | All task/to-do Excel read/write; `_ensure_todo_sheet()` migrates older To-Do sheets |
| `core/leaves.py` | Leave/holiday markers; `_mutate()` opens the workbook once per write operation |
| `core/reminder.py` | Tray icon (pystray) + toast (winotify) |
| `ui/glass.py` | Shared widget primitives: `GlassCard`, `PillButton`, `bind_scroll`, `apply_mica()` |
| `ui/icons.py` | Pillow-generated sidebar icons; cached as `ImageTk.PhotoImage` — add new icons here |
| `ui/log_form.py` | Task entry form; sets `app._dirty = True` on save; `prefill()` supports To-Do → Log flow |
| `ui/log_viewer.py` | History view (list + calendar): filter, search, edit, delete, missed days |
| `ui/summary.py` | Hours summary by project, week/month; project status tracking |
| `ui/settings.py` | Settings panel; uses `cfg_mod._read_excel_config()` — do not duplicate that parsing logic |
| `ui/todo.py` | To-Do page: add/complete/delete tasks, project/subproject assignment, Log button prefills Log Tasks |

## Config storage

Settings are stored in two places — do not assume a JSON file exists:
- **Windows Registry** `HKEY_CURRENT_USER\Software\DailyTaskLog` — `excel_path` and `autostart` only.
- **Excel `Config` sheet** — everything else: `reminder_enabled`, `reminder_time`, `theme`, `projects`.

## Excel sheets

| Sheet | Contents |
|---|---|
| `Task Log` | Task entries |
| `Leaves` | Leave/holiday markers |
| `Config` | App settings |
| `Project Status` | Per-project status labels |
| `To-Do` | To-do items (ID, Task, Done, Created, Project, Subproject) |

## Known bugs (not yet fixed)

1. **Toast click callback is broken** (`core/reminder.py`) — `winotify` protocol launch doesn't call back into Python. Any fix must use winotify's supported API, not a custom protocol.
2. **`App.config` shadows `tk.Misc.config()`** (`main.py`) — rename to `app_config` or `cfg` when touching that class.

## Previously listed bugs — now resolved

- ~~Treeview row tag colours hardcoded~~ — `missed` tag reads `c["missed_bg"]` from `THEMES`; `even` tag reads `c["bg"]`.
- ~~`get_missed_days` includes weekends~~ — was already `weekday() < 5`; confirmed not a bug.
- ~~Double Excel load on first view~~ — replaced with `_dirty` flag in `App._navigate()`; `page.load()` only called on first visit or after a write.

## Running locally

```powershell
pip install -r requirements.txt
python generate_icon.py   # first time only
python main.py
```

## Building the .exe

```
build.bat
```

Output: `dist\DailyTaskLog.exe` — standalone, no Python install required.
