import sys
import os
import socket
import threading
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import config as cfg_mod
from core.reminder import ReminderThread, create_tray_icon
from ui.glass import apply_mica

# Apple Liquid Glass palette
THEMES = {
    "light": {
        "bg":               "#F2F2F7",   # grouped background
        "card":             "#FFFFFF",   # card surface
        "fg":               "#1C1C1E",   # primary label
        "muted":            "#8E8E93",   # secondary label
        "accent":           "#007AFF",   # system blue
        "border":           "#D1D1D6",   # separator
        "input":            "#FFFFFF",   # text-field bg
        "shadow":           "#E5E5EA",   # card shadow border
        "highlight":        "#FFFFFF",   # 1 px top-edge shimmer
        "sidebar_bg":       "#F9F9FB",   # sidebar surface
        "sidebar_fg":       "#8E8E93",
        "sidebar_active":   "#007AFF",
        "sidebar_active_bg":"#EAF2FF",
        "missed_bg":        "#FFF8EC",
    },
}


NAV_ITEMS = [
    ("Log Tasks", "📝"),
    ("History",   "📋"),
    ("Summary",   "📊"),
    ("To-Do",     "☑"),
    ("Settings",  "⚙"),
]

SINGLE_INSTANCE_PORT = 47293

_NAV_KEY = {
    "Log Tasks": "log",
    "History":   "history",
    "Summary":   "summary",
    "To-Do":     "todo",
    "Settings":  "settings",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = cfg_mod.load()
        self.colors = THEMES[self.config_data.get("theme", "light")]
        self._current_page = None
        self._pages = {}
        self._dirty = False
        self._tray_icon = None
        self._reminder_thread = None
        self._setup_window()
        self._build_ui()
        self._start_tray()
        self._start_reminder()
        self._start_instance_server()
        self._register_protocol()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        self.title("Daily Task Log")
        self.geometry("1080x720")
        self.minsize(860, 600)
        self.configure(bg=self.colors["bg"])
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        style = ttk.Style()
        style.theme_use("clam")
        self._apply_ttk_style()
        # Apply Mica glass effect after window is mapped
        self.after(100, lambda: apply_mica(self.winfo_id()))

    def _apply_ttk_style(self):
        c = self.colors
        s = ttk.Style()
        s.configure("Treeview",
                    background=c["card"], foreground=c["fg"],
                    fieldbackground=c["card"], rowheight=30,
                    font=("Segoe UI", 10))
        s.configure("Treeview.Heading",
                    background=c["bg"], foreground=c["muted"],
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", c["accent"])],
              foreground=[("selected", "#FFFFFF")])
        s.configure("TCombobox",
                    fieldbackground=c["input"],
                    background=c["input"],
                    foreground=c["fg"],
                    selectbackground=c["accent"],
                    selectforeground="#FFFFFF")
        s.configure("Vertical.TScrollbar",
                    background=c["bg"], troughcolor=c["card"],
                    bordercolor=c["border"], arrowcolor=c["muted"])

    def _build_ui(self):
        c = self.colors

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = tk.Frame(self, bg=c["sidebar_bg"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Thin vertical separator between sidebar and content
        self._sep = tk.Frame(self, bg=c["border"], width=1)
        self._sep.pack(side="left", fill="y")

        # Brand block
        brand = tk.Frame(self.sidebar, bg=c["sidebar_bg"])
        brand.pack(fill="x", padx=20, pady=(28, 0))
        tk.Label(brand, text="Task Log",
                 font=("Segoe UI", 16, "bold"),
                 bg=c["sidebar_bg"], fg=c["fg"]).pack(anchor="w")
        tk.Label(brand, text="Daily tracker",
                 font=("Segoe UI", 9),
                 bg=c["sidebar_bg"], fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        tk.Frame(self.sidebar, bg=c["border"], height=1).pack(
            fill="x", padx=20, pady=(16, 10))

        # Nav buttons
        self._nav_btns = []
        from ui import icons
        for label, emoji_icon in NAV_ITEMS:
            name_key = _NAV_KEY.get(label, "log")
            
            img = icons.get_icon(name_key, theme=self.config_data.get("theme", "light"), size=20)
            
            btn = tk.Button(
                self.sidebar,
                text=f"   {label}",
                image=img,
                compound="left",
                font=("Segoe UI", 10),
                bg=c["sidebar_bg"], fg=c["sidebar_fg"],
                activebackground=c["sidebar_active_bg"],
                activeforeground=c["sidebar_active"],
                relief="flat", bd=0, anchor="w",
                padx=16, pady=8, cursor="hand2",
                command=lambda l=label: self._navigate(l))
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns.append((label, btn))

        # ── Main frame ───────────────────────────────────────────────────────
        self.main_frame = tk.Frame(self, bg=c["bg"])
        self.main_frame.pack(side="left", fill="both", expand=True)

        self._navigate("Log Tasks")

    def _navigate(self, page_name):
        # 1. Check for unsaved changes if leaving Settings page
        if self._current_page and self._current_page.__class__.__name__ == "Settings":
            if self._current_page.has_unsaved_changes():
                from tkinter import messagebox
                res = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved settings. Do you want to save them before leaving?",
                    parent=self
                )
                if res is True:
                    if not self._current_page._save():
                        return
                elif res is False:
                    self._pages.pop("Settings", None)
                else:
                    return

        c = self.colors
        for label, btn in self._nav_btns:
            if label == page_name:
                btn.configure(bg=c["sidebar_active_bg"],
                              fg=c["sidebar_active"],
                              font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=c["sidebar_bg"],
                              fg=c["sidebar_fg"],
                              font=("Segoe UI", 10))

        if self._current_page:
            self._current_page.pack_forget()

        is_new = page_name not in self._pages
        if is_new:
            self._pages[page_name] = self._create_page(page_name)

        page = self._pages[page_name]
        if page_name in ("History", "Summary") and (is_new or self._dirty):
            page.load()
            self._dirty = False
        page.pack(fill="both", expand=True)
        self._current_page = page

    def _create_page(self, page_name):
        from ui.log_form import LogForm
        from ui.log_viewer import LogViewer
        from ui.summary import Summary
        from ui.todo import TodoPage
        from ui.settings import Settings

        mapping = {
            "Log Tasks": LogForm,
            "History":   LogViewer,
            "Summary":   Summary,
            "To-Do":     TodoPage,
            "Settings":  Settings,
        }
        return mapping[page_name](self.main_frame, self)

    def apply_theme(self):
        self.colors = THEMES[self.config_data.get("theme", "light")]
        c = self.colors
        self.configure(bg=c["bg"])
        self._apply_ttk_style()
        self._pages.clear()
        self._current_page = None
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self._navigate("Log Tasks")

    def _on_close(self):
        self.withdraw()

    def _start_tray(self):
        icon = create_tray_icon(
            lambda: self.after(0, self.show_window),
            self._quit,
            lambda: self.config_data,
        )
        if icon:
            self._tray_icon = icon
            threading.Thread(target=icon.run, daemon=True).start()

    def _start_reminder(self):
        self._reminder_thread = ReminderThread(
            get_config_fn=lambda: self.config_data,
            show_window_fn=self.show_window,
        )
        self._reminder_thread.start()

    def _start_instance_server(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
            srv.listen(5)
        except OSError:
            return

        def _serve():
            while True:
                try:
                    conn, _ = srv.accept()
                    if conn.recv(16).strip() == b'show':
                        self.after(0, self.show_window)
                    conn.close()
                except Exception:
                    return

        threading.Thread(target=_serve, daemon=True).start()

    def _register_protocol(self):
        try:
            import winreg
            cmd = (f'"{sys.executable}" --show' if getattr(sys, 'frozen', False)
                   else f'"{sys.executable}" "{os.path.abspath(__file__)}" --show')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'Software\Classes\dailytasklog') as k:
                winreg.SetValueEx(k, '', 0, winreg.REG_SZ, 'URL:Daily Task Log')
                winreg.SetValueEx(k, 'URL Protocol', 0, winreg.REG_SZ, '')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'Software\Classes\dailytasklog\shell\open\command') as k:
                winreg.SetValueEx(k, '', 0, winreg.REG_SZ, cmd)
        except Exception as e:
            print(f'Protocol registration error: {e}')

    def _quit(self):
        if self._reminder_thread:
            self._reminder_thread.stop()
        if self._tray_icon:
            self._tray_icon.stop()
        self.destroy()
        sys.exit(0)


def main():
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    if '--show' in sys.argv[1:]:
        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
            s.send(b'show')
            s.close()
        except Exception:
            pass
        return

    try:
        s = socket.socket()
        s.settimeout(0.3)
        s.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
        s.send(b'show')
        s.close()
        return
    except (ConnectionRefusedError, OSError):
        pass

    app = App()
    app.withdraw()
    app.after(500, app.show_window)
    app.mainloop()


if __name__ == "__main__":
    main()
