# Daily Task Log

A lightweight Windows desktop app to log your daily work tasks, built with Python + Tkinter.  
Runs in the system tray and reminds you to log at a time you set.

---

## Requirements

- Windows 10 or 11
- Python 3.11+ → https://www.python.org/downloads/

---

## Setup (first time)

Open a terminal (Command Prompt or PowerShell) in this folder and run:

```
pip install -r requirements.txt
python generate_icon.py
python main.py
```

That's it. The app will appear in your system tray.

---

## Features

| Feature | Details |
|---|---|
| Log tasks | Date (any), project/subproject, task description, hours |
| Multiple tasks per day | Add as many rows as needed |
| Backfill past dates | Log for any previous date anytime |
| Duplicate last day | Copy yesterday's tasks as a starting point |
| Daily notes | Optional note per day |
| Leave / Holiday markers | Mark days as Public Holiday, Annual Leave, or MC Leave |
| Edit / Delete | Click any row in History to edit or delete |
| Calendar view | Visual month calendar in History showing logged days and leave |
| Search | Search across all task descriptions |
| Filter | Filter by date range and project |
| Summary | Hours per project by week or month, with project status tracking |
| To-Do list | Personal task list with project assignment and one-click log |
| Export | Export filtered results to Excel (.xlsx) or CSV |
| Missed days | Highlights weekdays with no log entry |
| System tray | Runs quietly in the background |
| Daily reminder | Windows notification at your chosen time |
| Auto-start | Optional: launch on Windows startup |

---

## Build as .exe (optional)

To create a standalone `.exe` that doesn't need Python installed:

```
python generate_icon.py
build.bat
```

Your `.exe` will be in the `dist\` folder. Copy `dist\DailyTaskLog.exe` anywhere and run it — no Python required on the target machine.

### Enabling auto-start from the .exe

1. Run `dist\DailyTaskLog.exe` (not `python main.py`)
2. Go to **Settings → "Launch on Windows startup"** → tick the checkbox → **Save**

This registers the exe in the Windows startup registry so it launches automatically on login and sits in the system tray.

> **Note:** Auto-start registration is silently skipped when running via `python main.py`. It only works from the built `.exe`.

---

## Data storage

All task data is saved to a single Excel file:

```
C:\Users\<YourName>\Documents\task_log.xlsx
```

You can open this file directly in Excel anytime.  
Change the path in Settings if you prefer a different location (e.g. OneDrive).

The Excel file contains multiple sheets:

| Sheet | Contents |
|---|---|
| `Task Log` | All task entries |
| `Leaves` | Leave and holiday markers |
| `Config` | App settings (reminder time, projects, etc.) |
| `Project Status` | Status labels per project |
| `To-Do` | Personal to-do items with project assignment |

App settings are also partially stored in the Windows Registry (`HKEY_CURRENT_USER\Software\DailyTaskLog`) for the file path and autostart flag.

---

## Closing the app

Clicking X minimises to tray — it keeps running so the reminder works.  
To fully quit: right-click the tray icon → Quit.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Notification doesn't appear | Check Windows Focus Assist / Do Not Disturb is off |
| App doesn't start on boot | Enable "Launch on Windows startup" in Settings and save |
| Excel file not found | Check the path in Settings |
| `pip install` fails | Make sure Python 3.11+ is installed and in PATH |
