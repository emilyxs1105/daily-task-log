# Daily Task Log — Claude Instructions

## Project overview

Lightweight Windows desktop app for logging daily work tasks. Python + Tkinter, runs in the system tray with toast notifications. Packaged with PyInstaller as a standalone `.exe`.

**Design constraint:** Tkinter was chosen over CustomTkinter for minimal RAM footprint (~15–25 MB idle in tray). Keep all suggestions minimal and lightweight. Do not introduce new dependencies.

## Stack

- Python 3.11+
- Tkinter (built-in, no CustomTkinter)
- openpyxl — Excel read/write
- pystray — system tray icon
- winotify — Windows toast notifications
- Pillow — icon generation
- PyInstaller — packaging to `.exe`

## File structure

```
main.py              App shell, sidebar nav, THEMES dict, _NAV_KEY constant, _dirty flag, tray/reminder startup
core/config.py       Registry + Excel Config sheet I/O; _read_excel_config() shared helper; DEFAULTS is schema
core/data.py         All Excel read/write (openpyxl). File: ~/Documents/task_log.xlsx
core/leaves.py       Leave/holiday markers: load(), mark(), clear(), get(); _mutate() for single-pass write
core/reminder.py     pystray tray icon + winotify notifications
ui/glass.py          GlassCard, PillButton, bind_scroll (skips scroll when content fits), apply_mica()
ui/icons.py          Pillow-generated theme-aware sidebar icons; cached as ImageTk.PhotoImage
ui/log_form.py       Daily task entry form; sets app._dirty = True on save; prefill() for To-Do → Log flow
ui/log_viewer.py     History viewer (list + calendar views, filter, search, edit, delete, missed days)
ui/summary.py        Hours by project, week/month view; project status tracking
ui/settings.py       Settings panel; delegates Excel config parsing to cfg_mod._read_excel_config()
ui/todo.py           To-Do page: add/complete/delete tasks, project assignment, one-click Log prefill
generate_icon.py     Generates assets/icon.ico
build.bat            PyInstaller build script → dist/DailyTaskLog.exe
```

## Data storage

- Task data: `~/Documents/task_log.xlsx` (configurable in Settings)
- Config is stored in two places:
  - Windows Registry `HKEY_CURRENT_USER\Software\DailyTaskLog` — `excel_path` and `autostart` only
  - Excel `Config` sheet — all other settings (reminder_enabled, reminder_time, theme, projects)
- Config schema defined in `core/config.py` — `DEFAULTS` dict is the source of truth

Excel sheets:

| Sheet | Contents |
|---|---|
| `Task Log` | Task entries |
| `Leaves` | Leave/holiday markers |
| `Config` | App settings |
| `Project Status` | Per-project status labels |
| `To-Do` | To-do items (ID, Task, Done, Created, Project, Subproject) |

`_ensure_todo_sheet()` in `core/data.py` auto-migrates older To-Do sheets that are missing the Project/Subproject columns.

## Running the app

```powershell
# First time
pip install -r requirements.txt
python generate_icon.py

# Run
python main.py
```

## Building the .exe

```
build.bat
```

Output: `dist\DailyTaskLog.exe`

## Dirty-flag pattern (main.py)

`App._dirty` controls when History and Summary reload their Excel data:
- Set to `True` by any write: `LogForm._save()`, `LogViewer._after_edit()`, `_after_add_missed()`, `_confirm_delete_entry()`, leave mark/clear in `EditDialog`, leave delete in `_on_delete()`.
- Cleared to `False` by `_navigate()` after calling `page.load()` for History or Summary.
- `page.load()` is only called on first visit or when `_dirty` is True — not on every tab switch.

## Known bugs (not yet fixed)

1. **Toast click callback silent** — `winotify` `add_actions(launch="dailytasklog://...")` launches an unregistered protocol; the Python callback is never called.
2. **`App.config` shadows `tk.Misc.config()`** — code smell in `main.py`, shouldn't crash in practice.

## Previously listed bugs — now resolved

- ~~Treeview row colors hardcoded~~ — `missed` tag reads `c["missed_bg"]` from `THEMES`; `even` tag reads `c["bg"]`.
- ~~`get_missed_days` includes weekends~~ — was already `weekday() < 5`; confirmed not a bug.
- ~~Double Excel load on first visit~~ — replaced with `_dirty` flag; `page.load()` only called when needed.

## Code style

- No comments unless the WHY is non-obvious.
- No new abstractions beyond what a task requires.
- No error handling for impossible cases — trust internal guarantees.
- Only validate at boundaries (user input, file I/O).
