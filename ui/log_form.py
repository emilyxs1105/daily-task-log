import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from core import data as db
from core import leaves as leaves_mod
from ui.glass import GlassCard, PillButton, bind_scroll


class LogForm(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=parent["bg"])
        self.app = app
        self.task_rows = []
        self._build()

    def _cfg(self):
        return self.app.config_data

    def _build(self):
        c = self.app.colors
        bg = c["bg"]
        self.configure(bg=bg)

        # Scrollable canvas so the form works on small windows
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)

        def _autoscroll(first, last):
            first, last = float(first), float(last)
            if first <= 0.0 and last >= 1.0:
                scrollbar.pack_forget()
            elif not scrollbar.winfo_ismapped():
                scrollbar.pack(side="right", fill="y")
            scrollbar.set(first, last)

        canvas.configure(yscrollcommand=_autoscroll)

        self._scroll_frame = tk.Frame(canvas, bg=bg)
        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        canvas.find_withtag("all")[0], width=e.width))

        bind_scroll(canvas)
        self._canvas = canvas
        self._inner_build()

    def _inner_build(self):
        sf = self._scroll_frame
        c = self.app.colors
        bg = c["bg"]

        # ── Page header ──────────────────────────────────────────────────────
        hdr = tk.Frame(sf, bg=bg)
        hdr.pack(fill="x", padx=24, pady=(22, 2))
        tk.Label(hdr, text="Log Tasks",
                 font=("Segoe UI", 20, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Label(hdr, text="Record what you worked on today",
                 font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        # ── Date & Project card ───────────────────────────────────────────────
        meta_card = GlassCard(sf, self.app)
        meta_card.pack(fill="x", padx=24, pady=(14, 0))
        inn = meta_card.inner
        inn.configure(bg=c["card"], padx=18, pady=14)

        col_frame = tk.Frame(inn, bg=c["card"])
        col_frame.pack(fill="x")

        # Date
        date_col = tk.Frame(col_frame, bg=c["card"])
        date_col.pack(side="left", padx=(0, 24))
        tk.Label(date_col, text="DATE", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 4))
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        entry_row = tk.Frame(date_col, bg=c["card"])
        entry_row.pack()
        tk.Entry(entry_row, textvariable=self.date_var,
                 font=("Segoe UI", 11), width=13,
                 bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                 insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", ipady=6)
        from ui import icons
        self._cal_img = icons.get_icon("calendar", theme=self.app.config_data.get("theme", "light"), size=18)
        tk.Button(entry_row, image=self._cal_img,
                  bg=c["input"], relief="flat", bd=0,
                  activebackground=c["highlight"], activeforeground=c["accent"],
                  cursor="hand2",
                  command=self._show_calendar
                  ).pack(side="left", padx=(4, 0), ipady=3)

        # Project
        proj_col = tk.Frame(col_frame, bg=c["card"])
        proj_col.pack(side="left", padx=(0, 16))
        tk.Label(proj_col, text="PROJECT", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 4))
        self.project_var = tk.StringVar()
        projects_dict = self._cfg().get("projects", {})
        project_names = list(projects_dict.keys())
        if project_names:
            self.project_var.set(project_names[0])
        self.project_cb = ttk.Combobox(proj_col, textvariable=self.project_var,
                                        values=project_names, font=("Segoe UI", 11),
                                        width=18, state="readonly")
        self.project_cb.pack(ipady=4)
        self.project_cb.bind("<<ComboboxSelected>>", lambda _: self._on_project_change())

        # Subproject
        subproj_col = tk.Frame(col_frame, bg=c["card"])
        subproj_col.pack(side="left")
        tk.Label(subproj_col, text="SUBPROJECT", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 4))
        self.subproject_var = tk.StringVar()
        self.subproject_cb = ttk.Combobox(subproj_col, textvariable=self.subproject_var,
                                           font=("Segoe UI", 11), width=18, state="readonly")
        self.subproject_cb.pack(ipady=4)
        self._on_project_change()

        # ── Day status card ───────────────────────────────────────────────────
        status_card = GlassCard(sf, self.app)
        status_card.pack(fill="x", padx=24, pady=(10, 0))
        status_inn = status_card.inner
        status_inn.configure(bg=c["card"], padx=18, pady=12)

        tk.Label(status_inn, text="MARK DAY AS", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 8))

        self._pending_leave_type = None

        btn_row = tk.Frame(status_inn, bg=c["card"])
        btn_row.pack(anchor="w")
        self._btn_ph = PillButton(btn_row, self.app, "Public Holiday",
                                  command=lambda: self._select_leave("public_holiday"),
                                  outer_bg=c["card"], small=True, min_width=130, icon_name="holiday")
        self._btn_ph.pack(side="left", padx=(0, 6))
        self._btn_al = PillButton(btn_row, self.app, "Annual Leave",
                                  command=lambda: self._select_leave("annual_leave"),
                                  outer_bg=c["card"], small=True, min_width=120, icon_name="leave")
        self._btn_al.pack(side="left", padx=(0, 6))
        self._btn_mc = PillButton(btn_row, self.app, "MC Leave",
                                  command=lambda: self._select_leave("mc_leave"),
                                  outer_bg=c["card"], small=True, min_width=100, icon_name="mc")
        self._btn_mc.pack(side="left", padx=(0, 6))
        PillButton(btn_row, self.app, "Clear",
                   command=self._clear_day,
                   outer_bg=c["card"], small=True, min_width=80, icon_name="clear"
                   ).pack(side="left", padx=(0, 6))

        self._day_status_lbl = tk.Label(
            status_inn, text="", font=("Segoe UI", 9),
            bg=c["card"], fg=c["muted"])
        self._day_status_lbl.pack(anchor="w", pady=(8, 0))

        self.date_var.trace_add("write", lambda *_: self._on_date_change())

        # ── Collapsible section (hidden when day is leave/holiday) ────────────
        self._log_section = tk.Frame(sf, bg=bg)
        self._log_section.pack(fill="x")

        # ── Tasks card ────────────────────────────────────────────────────────
        tasks_card = GlassCard(self._log_section, self.app)
        tasks_card.pack(fill="x", padx=24, pady=(10, 0))
        tasks_inn = tasks_card.inner
        tasks_inn.configure(bg=c["card"], padx=18, pady=14)

        tk.Label(tasks_inn, text="TASKS", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 8))

        self.tasks_frame = tk.Frame(tasks_inn, bg=c["card"])
        self.tasks_frame.pack(fill="x")

        self._add_task_row()

        # Row actions
        row_btns = tk.Frame(tasks_inn, bg=c["card"])
        row_btns.pack(anchor="w", pady=(10, 0))

        PillButton(row_btns, self.app, "Add row",
                   command=self._add_task_row,
                   outer_bg=c["card"], small=True, min_width=90, icon_name="add"
                   ).pack(side="left")
        PillButton(row_btns, self.app, "Duplicate last day",
                   command=self._duplicate_last_day,
                   outer_bg=c["card"], small=True, min_width=150, icon_name="copy"
                   ).pack(side="left", padx=(8, 0))

        # ── Notes card ────────────────────────────────────────────────────────
        notes_card = GlassCard(self._log_section, self.app)
        notes_card.pack(fill="x", padx=24, pady=(10, 0))
        notes_inn = notes_card.inner
        notes_inn.configure(bg=c["card"], padx=18, pady=14)

        tk.Label(notes_inn, text="NOTES (OPTIONAL)", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 6))
        self.notes_text = tk.Text(notes_inn, font=("Segoe UI", 10), height=3,
                                  bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                                  insertbackground=c["fg"], wrap="word",
                                  highlightbackground=c["border"], highlightthickness=1)
        self.notes_text.pack(fill="x")

        # ── Footer: total + save ──────────────────────────────────────────────
        footer = tk.Frame(self._log_section, bg=bg)
        footer.pack(fill="x", padx=24, pady=(14, 24))

        self.total_var = tk.StringVar(value="Total: 0.0 hrs")
        tk.Label(footer, textvariable=self.total_var,
                 font=("Segoe UI", 11, "bold"), bg=bg, fg=c["fg"]
                 ).pack(side="left", pady=4)

        PillButton(footer, self.app, "Save Log",
                   command=self._save, primary=True,
                   outer_bg=bg, min_width=110
                   ).pack(side="right")

        self._on_date_change()

    def _on_project_change(self):
        projects_dict = self._cfg().get("projects", {})
        subs = projects_dict.get(self.project_var.get(), [])
        self.subproject_cb.configure(values=[""] + subs)
        self.subproject_var.set("")
        self.subproject_cb.configure(state="readonly" if subs else "disabled")

    def _show_calendar(self):
        from ui.glass import CalendarPopup
        CalendarPopup(self, self.app, self.date_var)

    def _add_task_row(self, task_text="", hours_text=""):
        c = self.app.colors
        bg = c["card"]

        row = tk.Frame(self.tasks_frame, bg=bg)
        row.pack(fill="x", pady=3)

        task_var = tk.StringVar(value=task_text)
        tk.Entry(row, textvariable=task_var, font=("Segoe UI", 10),
                 bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                 insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        hours_var = tk.StringVar(value=hours_text)
        tk.Entry(row, textvariable=hours_var, font=("Segoe UI", 10), width=6,
                 bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                 insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", ipady=6, padx=(0, 4))
        tk.Label(row, text="hrs", font=("Segoe UI", 9),
                 bg=bg, fg=c["muted"]).pack(side="left", padx=(0, 8))

        hours_var.trace_add("write", lambda *_: self._update_total())

        tk.Button(row, text="✕", font=("Segoe UI", 9),
                  bg=bg, fg=c["muted"], relief="flat", bd=0, cursor="hand2",
                  command=lambda rf=row, tv=task_var, hv=hours_var:
                      self._remove_row(rf, tv, hv)
                  ).pack(side="left")

        self.task_rows.append((task_var, hours_var, row))

    def _remove_row(self, row_frame, task_var, hours_var):
        self.task_rows = [r for r in self.task_rows if r[2] is not row_frame]
        row_frame.destroy()
        self._update_total()

    def _update_total(self):
        total = 0.0
        for _, hv, _ in self.task_rows:
            try:
                total += float(hv.get())
            except ValueError:
                pass
        self.total_var.set(f"Total: {total:.1f} hrs")

    def _current_date(self):
        try:
            return datetime.strptime(self.date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    def _on_date_change(self):
        d = self._current_date()
        self._pending_leave_type = leaves_mod.get(d) if d else None
        self._refresh_day_status()

    def _select_leave(self, leave_type: str):
        self._pending_leave_type = leave_type
        self._refresh_day_status()

    def _clear_day(self):
        self._pending_leave_type = None
        d = self._current_date()
        if d:
            leaves_mod.clear(d)
        self._refresh_day_status()

    def _refresh_day_status(self):
        d = self._current_date()
        if d is None:
            self._day_status_lbl.configure(text="")
            self._set_leave_btn_active(None)
            return
        saved_type = leaves_mod.get(d)
        self._set_leave_btn_active(self._pending_leave_type)
        if saved_type:
            icon = leaves_mod.ICONS.get(saved_type, "")
            label = leaves_mod.TYPES.get(saved_type, saved_type)
            self._day_status_lbl.configure(
                text=f"{icon}  {d.strftime('%d %b %Y')} marked as {label} — saved.",
                fg=self.app.colors["accent"])
            self._log_section.pack_forget()
        elif self._pending_leave_type:
            icon = leaves_mod.ICONS.get(self._pending_leave_type, "")
            label = leaves_mod.TYPES.get(self._pending_leave_type, self._pending_leave_type)
            self._day_status_lbl.configure(
                text=f"{icon}  {label} selected — click Save Log to confirm",
                fg=self.app.colors["muted"])
            if not self._log_section.winfo_ismapped():
                self._log_section.pack(fill="x")
        else:
            self._day_status_lbl.configure(
                text=f"{d.strftime('%d %b %Y')} — no special status",
                fg=self.app.colors["muted"])
            if not self._log_section.winfo_ismapped():
                self._log_section.pack(fill="x")

    def _set_leave_btn_active(self, active_type):
        for lt, btn in (("public_holiday", self._btn_ph),
                        ("annual_leave",   self._btn_al),
                        ("mc_leave",       self._btn_mc)):
            btn._primary = (lt == active_type)
            btn._danger  = False
            btn._draw()

    def _duplicate_last_day(self):
        entries = db.load_all(self._cfg()["excel_path"])
        last = db.get_last_day_entries(entries)
        if not last:
            messagebox.showinfo("No previous entries",
                                "No previous entries found to duplicate.", parent=self.winfo_toplevel())
            return
        for r in list(self.task_rows):
            r[2].destroy()
        self.task_rows = []
        for e in last:
            self._add_task_row(task_text=e["task"],
                               hours_text=str(e["hours"]))
        if last[0].get("project") in self._cfg().get("projects", []):
            self.project_var.set(last[0]["project"])
        self.notes_text.delete("1.0", "end")
        if last[0].get("notes"):
            self.notes_text.insert("1.0", last[0]["notes"])
        self._update_total()

    def _save(self):
        date_str = self.date_var.get().strip()
        try:
            entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid date", "Enter date as YYYY-MM-DD.", parent=self.winfo_toplevel())
            return

        # Leave / holiday path — no tasks needed
        if self._pending_leave_type:
            leaves_mod.mark(entry_date, self._pending_leave_type)
            self.app._dirty = True
            label = leaves_mod.TYPES.get(self._pending_leave_type, self._pending_leave_type)
            messagebox.showinfo("Saved",
                                f"{entry_date.strftime('%d %b %Y')} marked as {label}.", parent=self.winfo_toplevel())
            self._on_date_change()
            return

        project = self.project_var.get().strip()
        subproject = self.subproject_var.get().strip()
        notes = self.notes_text.get("1.0", "end").strip()
        saved = 0

        for task_var, hours_var, _ in self.task_rows:
            task = task_var.get().strip()
            if not task:
                continue
            try:
                hours = float(hours_var.get())
            except ValueError:
                hours = 0.0
            db.save_entry(self._cfg()["excel_path"], {
                "date": entry_date,
                "project": project,
                "subproject": subproject,
                "task": task,
                "hours": hours,
                "notes": notes,
            })
            saved += 1

        if saved == 0:
            messagebox.showwarning("Nothing to save",
                                   "Please enter at least one task.", parent=self.winfo_toplevel())
            return

        self.app._dirty = True
        messagebox.showinfo("Saved",
                            f"{saved} task(s) saved for "
                            f"{entry_date.strftime('%d %b %Y')}.", parent=self.winfo_toplevel())
        for r in list(self.task_rows):
            r[2].destroy()
        self.task_rows = []
        self.notes_text.delete("1.0", "end")
        self._add_task_row()
        self._update_total()

    def set_date(self, d: date):
        self.date_var.set(d.strftime("%Y-%m-%d"))

    def prefill(self, task: str, project: str = "", subproject: str = ""):
        for r in list(self.task_rows):
            r[2].destroy()
        self.task_rows = []
        self._add_task_row(task_text=task)

        projects = list(self._cfg().get("projects", {}).keys())
        if project and project in projects:
            self.project_var.set(project)
            self._on_project_change()
            subs = self._cfg().get("projects", {}).get(project, [])
            if subproject and subproject in subs:
                self.subproject_var.set(subproject)

        self._update_total()
