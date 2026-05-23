import tkinter as tk
from tkinter import ttk
from core import data as db
from ui.glass import GlassCard, PillButton, bind_scroll


class TodoPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=parent["bg"])
        self.app = app
        self._todos = []
        self._filter = "active"
        self._build()
        self.load()

    def _cfg(self):
        return self.app.config_data

    def _build(self):
        c = self.app.colors
        bg = c["bg"]
        self.configure(bg=bg)

        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill="x", padx=24, pady=(22, 2))
        tk.Label(hdr, text="To-Do",
                 font=("Segoe UI", 20, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Label(hdr, text="Your personal task list",
                 font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        # ── Add task card ─────────────────────────────────────────────────────
        add_card = GlassCard(self, self.app)
        add_card.pack(fill="x", padx=24, pady=(14, 0))
        inn = add_card.inner
        inn.configure(bg=c["card"], padx=18, pady=14)

        add_row = tk.Frame(inn, bg=c["card"])
        add_row.pack(fill="x")

        self._task_var = tk.StringVar()
        self._task_entry = tk.Entry(
            add_row, textvariable=self._task_var,
            font=("Segoe UI", 11), bg=c["input"], fg=c["fg"],
            relief="flat", bd=0, insertbackground=c["fg"],
            highlightbackground=c["border"], highlightthickness=1)
        self._task_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        self._task_entry.bind("<Return>", lambda _: self._add_task())

        PillButton(add_row, self.app, "Add", command=self._add_task,
                   primary=True, small=True, outer_bg=c["card"],
                   min_width=72, icon_name="add").pack(side="left")

        # ── Filter bar ────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=bg)
        bar.pack(fill="x", padx=24, pady=(12, 0))

        self._filter_btns = {}
        btn_frame = tk.Frame(bar, bg=bg)
        btn_frame.pack(side="left")
        for label, key in [("All", "all"), ("Active", "active"), ("Done", "done")]:
            btn = PillButton(btn_frame, self.app, label,
                             command=lambda k=key: self._set_filter(k),
                             small=True, outer_bg=bg, min_width=72)
            btn.pack(side="left", padx=(0, 6))
            self._filter_btns[key] = btn
        self._filter_btns["active"]._primary = True
        self._filter_btns["active"]._draw()

        self._stats_var = tk.StringVar()
        tk.Label(bar, textvariable=self._stats_var,
                 font=("Segoe UI", 9), bg=bg, fg=c["muted"]).pack(side="right", anchor="s", pady=2)

        # ── Scrollable task list ──────────────────────────────────────────────
        list_card = GlassCard(self, self.app)
        list_card.pack(fill="both", expand=True, padx=24, pady=(10, 16))
        inn2 = list_card.inner
        inn2.configure(bg=c["card"])

        canvas = tk.Canvas(inn2, bg=c["card"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(inn2, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)

        def _autoscroll(first, last):
            first, last = float(first), float(last)
            if first <= 0.0 and last >= 1.0:
                scrollbar.pack_forget()
            elif not scrollbar.winfo_ismapped():
                scrollbar.pack(side="right", fill="y")
            scrollbar.set(first, last)

        canvas.configure(yscrollcommand=_autoscroll)
        bind_scroll(canvas)

        self._list_frame = tk.Frame(canvas, bg=c["card"])
        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        canvas.find_withtag("all")[0], width=e.width))

    def load(self):
        self._todos = db.load_todos(self._cfg()["excel_path"])
        self._refresh()

    def _set_filter(self, key):
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn._primary = (k == key)
            btn._draw()
        self._refresh()

    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        c = self.app.colors
        bg = c["card"]

        active = [t for t in self._todos if not t["done"]]
        done   = [t for t in self._todos if t["done"]]
        visible = {"all": self._todos, "active": active, "done": done}[self._filter]

        parts = []
        if active:
            parts.append(f"{len(active)} active")
        if done:
            parts.append(f"{len(done)} done")
        self._stats_var.set("  ·  ".join(parts) if parts else "No tasks yet")

        if not visible:
            msg = {"active": "All done — nothing pending!",
                   "done":   "No completed tasks yet.",
                   "all":    "No tasks yet. Add one above."}[self._filter]
            tk.Label(self._list_frame, text=msg,
                     font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(pady=28)
            return

        for i, todo in enumerate(visible):
            row_bg = c["bg"] if i % 2 == 0 else bg
            self._build_row(todo, row_bg, c)

    def _build_row(self, todo, row_bg, c):
        row = tk.Frame(self._list_frame, bg=row_bg)
        row.pack(fill="x")

        # Checkbox
        cb = tk.Canvas(row, width=28, height=36, bg=row_bg,
                       highlightthickness=0, cursor="hand2")
        cb.pack(side="left", padx=(12, 6))
        self._draw_checkbox(cb, todo["done"], c)
        cb.bind("<Button-1>", lambda e, t=todo: self._toggle(t))

        # Task text
        font = ("Segoe UI", 10, "overstrike") if todo["done"] else ("Segoe UI", 10)
        fg   = c["muted"] if todo["done"] else c["fg"]
        lbl  = tk.Label(row, text=todo["task"], font=font,
                        bg=row_bg, fg=fg, anchor="w")
        lbl.pack(side="left", fill="x", expand=True, pady=8)
        lbl.bind("<Button-1>", lambda e, t=todo: self._toggle(t))

        # Delete (pack right-to-left, so delete goes on far right)
        PillButton(row, self.app, "✕",
                   command=lambda t=todo: self._delete(t),
                   danger=True, small=True, outer_bg=row_bg, min_width=36
                   ).pack(side="right", padx=(0, 10), pady=6)

        # Log button
        PillButton(row, self.app, "Log",
                   command=lambda t=todo: self._log_todo(t),
                   primary=True, small=True, outer_bg=row_bg, min_width=60
                   ).pack(side="right", padx=(0, 6), pady=6)

        # Project button
        proj_text = self._project_label(todo)
        proj_pill = PillButton(row, self.app, proj_text,
                               command=lambda t=todo: self._show_project_menu(t),
                               small=True, outer_bg=row_bg, min_width=120)
        proj_pill._primary = bool(todo.get("project"))
        proj_pill._draw()
        proj_pill.pack(side="right", padx=(0, 6), pady=6)

    def _project_label(self, todo):
        proj = todo.get("project", "")
        sub  = todo.get("subproject", "")
        if proj and sub:
            return f"{proj} › {sub}"
        if proj:
            return proj
        return "assign project"

    def _draw_checkbox(self, canvas, checked, c):
        canvas.delete("all")
        y0, y1 = 4, 26
        if checked:
            canvas.create_oval(3, y0, 25, y1, fill=c["accent"], outline=c["accent"])
            canvas.create_line(7, 15, 11, 19, 21, 10,
                               fill="white", width=2, capstyle="round", joinstyle="round")
        else:
            canvas.create_oval(3, y0, 25, y1, fill="", outline=c["border"], width=2)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_task(self):
        task = self._task_var.get().strip()
        if not task:
            return
        db.add_todo(self._cfg()["excel_path"], task)
        self._task_var.set("")
        self._task_entry.focus()
        self.load()

    def _toggle(self, todo):
        db.update_todo_done(self._cfg()["excel_path"], todo["id"], not todo["done"])
        self.load()

    def _delete(self, todo):
        db.delete_todo(self._cfg()["excel_path"], todo["id"])
        self.load()

    def _show_project_menu(self, todo):
        c = self.app.colors
        projects = self._cfg().get("projects", {})
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 10),
                       bg=c["card"], fg=c["fg"],
                       activebackground=c["accent"], activeforeground="#FFFFFF",
                       relief="flat", bd=1)

        menu.add_command(
            label="— None —",
            command=lambda: self._assign_project(todo, "", ""))
        menu.add_separator()

        for proj, subs in projects.items():
            if subs:
                sub_menu = tk.Menu(menu, tearoff=0, font=("Segoe UI", 10),
                                   bg=c["card"], fg=c["fg"],
                                   activebackground=c["accent"],
                                   activeforeground="#FFFFFF")
                sub_menu.add_command(
                    label=f"{proj} (no subproject)",
                    command=lambda p=proj: self._assign_project(todo, p, ""))
                sub_menu.add_separator()
                for sub in subs:
                    sub_menu.add_command(
                        label=sub,
                        command=lambda p=proj, s=sub: self._assign_project(todo, p, s))
                menu.add_cascade(label=proj, menu=sub_menu)
            else:
                menu.add_command(
                    label=proj,
                    command=lambda p=proj: self._assign_project(todo, p, ""))

        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _assign_project(self, todo, project, subproject):
        db.update_todo_project(self._cfg()["excel_path"], todo["id"], project, subproject)
        self.load()

    def _log_todo(self, todo):
        self.app._navigate("Log Tasks")
        log_form = self.app._pages.get("Log Tasks")
        if log_form:
            log_form.prefill(todo["task"], todo.get("project", ""),
                             todo.get("subproject", ""))
