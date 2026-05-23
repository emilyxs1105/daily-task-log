import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
from core import data as db
from core import leaves as leaves_mod
from ui.glass import GlassCard, PillButton


class LogViewer(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=parent["bg"])
        self.app = app
        self._all_entries = []
        self._all_leaves = {}
        self.cal_year = date.today().year
        self.cal_month = date.today().month
        self._build()

    def _cfg(self):
        return self.app.config_data

    def _build(self):
        c = self.app.colors
        bg = c["bg"]
        self.configure(bg=bg)

        # ── Page header ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill="x", padx=24, pady=(22, 2))
        
        title_frame = tk.Frame(hdr, bg=bg)
        title_frame.pack(side="left", fill="y", anchor="w")
        
        tk.Label(title_frame, text="History",
                 font=("Segoe UI", 20, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Label(title_frame, text="Browse, search and edit your logged tasks",
                 font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        # View Switcher in Header
        toggle_frame = tk.Frame(hdr, bg=bg)
        toggle_frame.pack(side="right", anchor="se", pady=(0, 2))
        
        self.view_mode = tk.StringVar(value="list")
        
        self.btn_list_view = PillButton(toggle_frame, self.app, "List View", 
                                        command=lambda: self._switch_view("list"), 
                                        small=True, outer_bg=bg, min_width=90, icon_name="list")
        self.btn_list_view.pack(side="left", padx=4)
        self.btn_list_view._primary = True
        
        self.btn_cal_view = PillButton(toggle_frame, self.app, "Calendar View", 
                                       command=lambda: self._switch_view("calendar"), 
                                       small=True, outer_bg=bg, min_width=110, icon_name="calendar")
        self.btn_cal_view.pack(side="left", padx=4)

        # ── View Containers ──────────────────────────────────────────────────
        self.list_view_frame = tk.Frame(self, bg=bg)
        self.list_view_frame.pack(fill="both", expand=True)
        
        self.cal_view_frame = tk.Frame(self, bg=bg)

        # ── Filter card ───────────────────────────────────────────────────────
        filter_card = GlassCard(self.list_view_frame, self.app)
        filter_card.pack(fill="x", padx=24, pady=(14, 0))
        ff = filter_card.inner
        ff.configure(bg=c["card"], padx=18, pady=12)

        row1 = tk.Frame(ff, bg=c["card"])
        row1.pack(fill="x", pady=(0, 8))

        row2 = tk.Frame(ff, bg=c["card"])
        row2.pack(fill="x")

        def _lbl(parent, text):
            return tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                            bg=c["card"], fg=c["muted"])

        def _entry(parent, var, w=13):
            return tk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=w,
                            bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                            insertbackground=c["fg"],
                            highlightbackground=c["border"], highlightthickness=1)

        self.search_var = tk.StringVar()

        # Row 1: Search
        _lbl(row1, "SEARCH").pack(side="left", padx=(0, 8))
        search_frame = tk.Frame(row1, bg=c["input"], highlightbackground=c["border"], highlightthickness=1)
        search_frame.pack(side="left", padx=(0, 24), ipady=3)
        
        from ui import icons
        self._search_icon_img = icons.get_icon("search", theme=self.app.config_data.get("theme", "light"), size=14)
        tk.Label(search_frame, image=self._search_icon_img, bg=c["input"]).pack(side="left", padx=(8, 2))
        
        self.search_ent = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10), width=22,
                                   bg=c["input"], fg=c["fg"], relief="flat", bd=0, insertbackground=c["fg"])
        self.search_ent.pack(side="left", fill="x", padx=(0, 6))

        # Placeholder logic
        def on_focus_in(event):
            if self.search_var.get() == "Search tasks...":
                self.search_var.set("")
                self.search_ent.configure(fg=c["fg"])

        def on_focus_out(event):
            if not self.search_var.get().strip():
                self.search_var.set("Search tasks...")
                self.search_ent.configure(fg=c["muted"])

        self.search_var.set("Search tasks...")
        self.search_ent.configure(fg=c["muted"])
        self.search_ent.bind("<FocusIn>", on_focus_in)
        self.search_ent.bind("<FocusOut>", on_focus_out)

        # Row 1: Project
        _lbl(row1, "PROJECT").pack(side="left", padx=(0, 8))
        self.proj_filter_var = tk.StringVar(value="All")
        projects = ["All"] + list(self._cfg().get("projects", {}).keys())
        self.proj_cb = ttk.Combobox(row1, textvariable=self.proj_filter_var,
                                     values=projects, font=("Segoe UI", 10),
                                     width=14, state="readonly")
        self.proj_cb.pack(side="left", ipady=3)
        self.proj_cb.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())

        # Row 2: Date From
        _lbl(row2, "FROM").pack(side="left", padx=(0, 8))
        self.from_var = tk.StringVar(
            value=date(date.today().year, 1, 1).strftime("%Y-%m-%d"))
        _entry(row2, self.from_var, 11).pack(side="left", ipady=5)
        from ui import icons
        self._cal_img = icons.get_icon("calendar", theme=self.app.config_data.get("theme", "light"), size=18)

        tk.Button(row2, image=self._cal_img,
                  bg=c["card"], relief="flat", bd=0,
                  activebackground=c["highlight"], activeforeground=c["accent"],
                  cursor="hand2",
                  command=lambda: self._show_calendar(self.from_var)
                  ).pack(side="left", padx=(2, 24))

        # Row 2: Date To
        _lbl(row2, "TO").pack(side="left", padx=(0, 8))
        self.to_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        _entry(row2, self.to_var, 11).pack(side="left", ipady=5)
        tk.Button(row2, image=self._cal_img,
                  bg=c["card"], relief="flat", bd=0,
                  activebackground=c["highlight"], activeforeground=c["accent"],
                  cursor="hand2",
                  command=lambda: self._show_calendar(self.to_var)
                  ).pack(side="left", padx=(2, 24))

        # Row 2: Buttons
        PillButton(row2, self.app, "Filter", command=self._apply_filters,
                   primary=True, small=True, outer_bg=c["card"], min_width=72
                   ).pack(side="left", padx=(0, 8))
        PillButton(row2, self.app, "Export", command=self._export,
                   small=True, outer_bg=c["card"], min_width=88, icon_name="export"
                   ).pack(side="left")

        # ── Stats row ─────────────────────────────────────────────────────────
        self.stats_frame = tk.Frame(self.list_view_frame, bg=bg)
        self.stats_frame.pack(fill="x", padx=24, pady=(10, 0))

        # ── Table ─────────────────────────────────────────────────────────────
        table_card = GlassCard(self.list_view_frame, self.app)
        table_card.pack(fill="both", expand=True, padx=24, pady=(10, 0))
        table_inn = table_card.inner
        table_inn.configure(bg=c["card"])

        cols = ("project", "task", "hours", "notes")
        self.tree = ttk.Treeview(table_inn, columns=cols,
                                  show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Date")
        self.tree.column("#0", width=120, anchor="w")
        for col, heading, w, anchor in [
            ("project", "Project", 180, "w"),
            ("task",    "Task",    230, "w"),
            ("hours",   "Hrs",     55,  "center"),
            ("notes",   "Notes",   150, "w"),
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=w, anchor=anchor)

        sb = ttk.Scrollbar(table_inn, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("missed",          background=c["missed_bg"])
        self.tree.tag_configure("even",            background=c["bg"])
        self.tree.tag_configure("public_holiday",  background="#FFF3E0")
        self.tree.tag_configure("annual_leave",    background="#E8F5E9")
        self.tree.tag_configure("mc_leave",        background="#FFF0F0")
        self.tree.bind("<Double-1>", self._on_edit)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # ── Action bar ────────────────────────────────────────────────────────
        action = tk.Frame(self.list_view_frame, bg=bg)
        action.pack(fill="x", padx=24, pady=(8, 16))

        PillButton(action, self.app, "Edit",
                   command=self._on_edit, small=True,
                   outer_bg=bg, min_width=80
                   ).pack(side="left", padx=(0, 8))
        PillButton(action, self.app, "Delete",
                   command=self._on_delete, danger=True, small=True,
                   outer_bg=bg, min_width=90
                   ).pack(side="left")

        self.footer_var = tk.StringVar(value="")
        tk.Label(action, textvariable=self.footer_var,
                 font=("Segoe UI", 9), bg=bg, fg=c["muted"]).pack(side="right")

        # Trace search input changes after all fields are initialized
        self.search_var.trace_add("write", lambda *_: self._apply_filters())

    # ── Stats ──────────────────────────────────────────────────────────────────
    def _build_stats(self, entries, from_date=None, to_date=None):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        c = self.app.colors

        total_hrs   = sum(e["hours"] for e in entries)
        logged_days = len({e["date"] for e in entries})
        
        missed_count = 0
        if from_date and to_date:
            today = date.today()
            limit_date = min(to_date, today - timedelta(days=1))
            all_logged_dates = {e["date"] for e in self._all_entries}
            leave_dates = set(self._all_leaves or {})
            
            curr = limit_date
            while curr >= from_date:
                if (curr.weekday() < 5
                        and curr not in all_logged_dates
                        and curr.strftime("%Y-%m-%d") not in leave_dates):
                    missed_count += 1
                curr -= timedelta(days=1)

        projects = {}
        for e in entries:
            projects[e["project"]] = projects.get(e["project"], 0) + e["hours"]
        top_proj = max(projects, key=projects.get) if projects else "—"

        year_str = str(from_date.year) if from_date else str(date.today().year)
        if from_date and to_date and from_date.year != to_date.year:
            year_str = f"{from_date.year}-{to_date.year}"

        stats = [
            ("Total hours",  f"{total_hrs:.1f}", f"in {year_str}"),
            ("Days logged",  str(logged_days),   f"in {year_str}"),
            ("Missed days",  str(missed_count),   f"in {year_str}"),
            ("Top project",  top_proj,            f"{projects.get(top_proj, 0):.1f} hrs"),
        ]

        for label, val, sub in stats:
            card = GlassCard(self.stats_frame, self.app)
            card.pack(side="left", padx=(0, 8))
            inn = card.inner
            inn.configure(bg=c["card"], padx=14, pady=8)
            tk.Label(inn, text=label, font=("Segoe UI", 8, "bold"),
                     bg=c["card"], fg=c["muted"]).pack(anchor="w")
            tk.Label(inn, text=val, font=("Segoe UI", 15, "bold"),
                     bg=c["card"], fg=c["fg"]).pack(anchor="w")
            tk.Label(inn, text=sub, font=("Segoe UI", 8),
                     bg=c["card"], fg=c["muted"]).pack(anchor="w")

    # ── Data loading ───────────────────────────────────────────────────────────
    def load(self):
        self._all_entries = db.load_all(self._cfg()["excel_path"])
        self._all_leaves = leaves_mod.load()
        if self.view_mode.get() == "calendar":
            self._refresh_calendar()
        else:
            self._apply_filters()

    def _apply_filters(self):
        search = self.search_var.get().strip()
        if search == "Search tasks...":
            search = ""
        search = search.lower()
        proj   = self.proj_filter_var.get()
        try:
            from_date = datetime.strptime(self.from_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            from_date = date.today() - timedelta(days=365)
        try:
            to_date = datetime.strptime(self.to_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            to_date = date.today()

        filtered = [
            e for e in self._all_entries
            if from_date <= e["date"] <= to_date
            and (proj == "All" or e["project"] == proj)
            and (not search or search in e["task"].lower()
                 or search in e.get("notes", "").lower())
        ]
        self._populate_tree(filtered, from_date, to_date)
        self._build_stats(filtered, from_date, to_date)

    def _populate_tree(self, entries, from_date=None, to_date=None):
        self.tree.delete(*self.tree.get_children())
        total = 0.0
        
        combined_items = []
        logged_dates = {e["date"] for e in entries}
        
        # Group entries by date
        entries_by_date = {}
        for e in entries:
            d = e["date"]
            if d not in entries_by_date:
                entries_by_date[d] = []
            entries_by_date[d].append(e)

        # 1. Add Logged Day Entries
        for d, day_entries in entries_by_date.items():
            combined_items.append({
                "date": d,
                "type": "log",
                "data": day_entries
            })
            for e in day_entries:
                total += e["hours"]

        # 2. Add Leaves within the filter range
        if from_date and to_date:
            for date_str, leave_type in self._all_leaves.items():
                try:
                    d = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if not (from_date <= d <= to_date):
                    continue
                if d in logged_dates:
                    continue
                combined_items.append({
                    "date": d,
                    "type": "leave",
                    "data": leave_type
                })

        # 3. Add Missed Days within the filter range
        if from_date and to_date:
            today = date.today()
            limit_date = min(to_date, today - timedelta(days=1))
            all_logged_dates = {e["date"] for e in self._all_entries}
            leave_dates = set(self._all_leaves or {})
            
            curr = limit_date
            while curr >= from_date:
                if (curr.weekday() < 5
                        and curr not in all_logged_dates
                        and curr.strftime("%Y-%m-%d") not in leave_dates):
                    combined_items.append({
                        "date": curr,
                        "type": "missed",
                        "data": None
                    })
                curr -= timedelta(days=1)

        # 4. Sort combined items descending by date
        combined_items.sort(key=lambda x: x["date"], reverse=True)

        # 5. Populate Treeview
        even_idx = 0
        for item in combined_items:
            d = item["date"]
            itype = item["type"]
            
            if itype == "log":
                day_entries = item["data"]
                
                d_str = d.strftime("%Y-%m-%d")
                leave_type = self._all_leaves.get(d_str)
                
                if leave_type:
                    tag = leave_type
                    icon = leaves_mod.ICONS.get(leave_type, "")
                    friendly_leave = leaves_mod.TYPES.get(leave_type, "")
                    date_display = f"{icon} {d.strftime('%d %b %Y')} ({friendly_leave})"
                else:
                    tag = "even" if even_idx % 2 == 0 else ""
                    even_idx += 1
                    date_display = d.strftime("%d %b %Y")
                
                projs = []
                for e in day_entries:
                    p = f"{e['project']} > {e['subproject']}" if e.get("subproject") else e["project"]
                    if p not in projs:
                        projs.append(p)
                proj_display = ", ".join(projs)
                
                if len(day_entries) == 1:
                    task_display = day_entries[0]["task"]
                    notes_display = day_entries[0].get("notes", "")
                    hours_display = f"{day_entries[0]['hours']:.1f}"
                    iid_val = str(day_entries[0]["id"])
                    
                    self.tree.insert("", "end", iid=iid_val, text=date_display, values=(
                        proj_display,
                        task_display,
                        hours_display,
                        notes_display,
                    ), tags=(tag,))
                else:
                    day_hours = sum(e["hours"] for e in day_entries)
                    hours_display = f"{day_hours:.1f}"
                    iid_val = f"day_{d.strftime('%Y-%m-%d')}"
                    task_display = f"📂  {len(day_entries)} Tasks logged"
                    notes_display = ""
                    
                    parent_node = self.tree.insert("", "end", iid=iid_val, text=date_display, values=(
                        proj_display,
                        task_display,
                        hours_display,
                        notes_display,
                    ), tags=(tag,))
                    
                    for idx, e in enumerate(day_entries, 1):
                        p = f"{e['project']} > {e['subproject']}" if e.get("subproject") else e["project"]
                        child_iid = str(e["id"])
                        self.tree.insert(parent_node, "end", iid=child_iid, text="", values=(
                            p,
                            f"  ↳  {e['task']}",
                            f"{e['hours']:.1f}",
                            e.get("notes", ""),
                        ), tags=(tag,))
                
            elif itype == "leave":
                leave_type = item["data"]
                icon = leaves_mod.ICONS.get(leave_type, "")
                label = leaves_mod.TYPES.get(leave_type, leave_type)
                self.tree.insert("", "end", iid=f"leave_{d.strftime('%Y-%m-%d')}", text=d.strftime("%d %b %Y"), values=(
                    "—",
                    f"{icon}  {label}", "", "",
                ), tags=(leave_type,))
                
            elif itype == "missed":
                self.tree.insert("", "end", iid=f"missed_{d}", text=d.strftime("%d %b %Y"), values=(
                    "—",
                    "⚠  No log entry — click Edit to add", "", "",
                ), tags=("missed",))

        self.footer_var.set(f"{len(entries)} entries  ·  {total:.1f} hrs total")

    def _show_calendar(self, var):
        from ui.glass import CalendarPopup
        CalendarPopup(self, self.app, var)

    def _get_selected_entry(self):
        sel = self.tree.selection()
        if not sel or sel[0].startswith("missed_") or sel[0].startswith("leave_") or sel[0].startswith("day_"):
            return None
        try:
            eid = int(sel[0])
        except ValueError:
            return None
        return next((e for e in self._all_entries if e["id"] == eid), None)

    def _on_edit(self, event=None):
        if event:
            clicked_item = self.tree.identify_row(event.y)
        else:
            sel = self.tree.selection()
            clicked_item = sel[0] if sel else None

        if not clicked_item:
            return

        if clicked_item.startswith("missed_"):
            date_str = clicked_item.split("_", 1)[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return
            new_entry = {
                "id": None,
                "date": d,
                "project": "",
                "subproject": "",
                "task": "",
                "hours": 0.0,
                "notes": ""
            }
            EditDialog(self, self.app, new_entry, on_save=self._after_add_missed)
            return
        elif clicked_item.startswith("leave_"):
            date_str = clicked_item.split("_", 1)[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return
            new_entry = {
                "id": None,
                "date": d,
                "project": "",
                "subproject": "",
                "task": "",
                "hours": 0.0,
                "notes": ""
            }
            EditDialog(self, self.app, new_entry, on_save=self._after_add_missed)
            return
        elif clicked_item.startswith("day_"):
            if event:
                is_open = self.tree.item(clicked_item, "open")
                self.tree.item(clicked_item, open=not is_open)
                return
            date_str = clicked_item.split("_", 1)[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return
            entries_on_day = [e for e in self._all_entries if e["date"] == d]
            TaskSelectDialog(self, self.app, entries_on_day, on_select=self._open_edit_for_entry)
            return

        # If it's a normal entry child row
        entry = next((e for e in self._all_entries if str(e["id"]) == clicked_item), None)
        if not entry:
            if not event:
                messagebox.showinfo("Select entry", "Select an entry to edit.", parent=self.winfo_toplevel())
            return
        EditDialog(self, self.app, entry, on_save=self._after_edit)

    def _open_edit_for_entry(self, entry):
        EditDialog(self, self.app, entry, on_save=self._after_edit)

    def _after_edit(self, updated):
        db.update_entry(self._cfg()["excel_path"], updated)
        self.app._dirty = True
        self.load()

    def _after_add_missed(self, new_entry):
        db.save_entry(self._cfg()["excel_path"], new_entry)
        self.app._dirty = True
        self.load()

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        if sel[0].startswith("leave_"):
            date_str = sel[0].split("_", 1)[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return
            
            friendly_date = d.strftime("%d %b %Y")
            leave_type = leaves_mod.get(d)
            friendly_leave = leaves_mod.TYPES.get(leave_type, "Leave/Holiday") if leave_type else "Leave/Holiday"
            
            if messagebox.askyesno("Delete Leave Marker",
                                   f"Remove '{friendly_leave}' on {friendly_date}?",
                                   parent=self.winfo_toplevel()):
                leaves_mod.clear(d)
                self.app._dirty = True
                self.load()
            return
        elif sel[0].startswith("day_"):
            date_str = sel[0].split("_", 1)[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return
            entries_on_day = [e for e in self._all_entries if e["date"] == d]
            if not entries_on_day:
                return
            
            dlg = TaskSelectDialog(self, self.app, entries_on_day, on_select=self._confirm_delete_entry)
            dlg.title("Select Task to Delete")
            return

        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo("Select entry", "Select an entry first.", parent=self.winfo_toplevel())
            return
        self._confirm_delete_entry(entry)

    def _confirm_delete_entry(self, entry):
        if messagebox.askyesno("Delete Task",
                               f"Delete '{entry['task']}' on {entry['date'].strftime('%d %b %Y')}?",
                               parent=self.winfo_toplevel()):
            db.delete_entry(self._cfg()["excel_path"], entry["id"])
            self.app._dirty = True
            self.load()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx"), ("CSV file", "*.csv")],
            title="Export log")
        if not path:
            return

        entry_by_id = {e["id"]: e for e in self._all_entries}
        sel_entries = []
        for iid in self.tree.get_children():
            if iid.startswith("missed_") or iid.startswith("leave_"):
                continue
            if iid.startswith("day_"):
                for child_iid in self.tree.get_children(iid):
                    try:
                        eid = int(child_iid)
                    except ValueError:
                        continue
                    entry = entry_by_id.get(eid)
                    if entry:
                        sel_entries.append(entry)
            else:
                try:
                    eid = int(iid)
                except ValueError:
                    continue
                entry = entry_by_id.get(eid)
                if entry:
                    sel_entries.append(entry)

        if path.endswith(".csv"):
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f, fieldnames=["id", "date", "project", "task", "hours", "notes"])
                w.writeheader()
                for e in sel_entries:
                    w.writerow({**e, "date": e["date"].strftime("%Y-%m-%d")})
        else:
            db.export_filtered(self._cfg()["excel_path"], sel_entries, path)

        messagebox.showinfo("Exported",
                            f"Exported {len(sel_entries)} entries to:\n{path}", parent=self.winfo_toplevel())

    def _on_tree_click(self, event):
        clicked_item = self.tree.identify_row(event.y)
        if clicked_item and clicked_item.startswith("day_"):
            region = self.tree.identify_region(event.x, event.y)
            if region in ("tree", "cell"):
                element = self.tree.identify_element(event.x, event.y)
                if element != "Treeitem.indicator":
                    is_open = self.tree.item(clicked_item, "open")
                    self.tree.item(clicked_item, open=not is_open)

    def _switch_view(self, mode):
        self.view_mode.set(mode)
        if mode == "list":
            self.btn_list_view._primary = True
            self.btn_list_view._draw()
            self.btn_cal_view._primary = False
            self.btn_cal_view._draw()
            
            self.cal_view_frame.pack_forget()
            self.list_view_frame.pack(fill="both", expand=True)
            self._apply_filters()
        else:
            self.btn_list_view._primary = False
            self.btn_list_view._draw()
            self.btn_cal_view._primary = True
            self.btn_cal_view._draw()
            
            self.list_view_frame.pack_forget()
            self.cal_view_frame.pack(fill="both", expand=True)
            self._refresh_calendar()

    def _refresh_calendar(self):
        c = self.app.colors
        bg = c["bg"]
        
        for w in self.cal_view_frame.winfo_children():
            w.destroy()
            
        cal_hdr = tk.Frame(self.cal_view_frame, bg=bg)
        cal_hdr.pack(fill="x", padx=24, pady=(10, 8))
        
        btn_prev = PillButton(cal_hdr, self.app, "←", command=self._prev_month, small=True, outer_bg=bg, min_width=36)
        btn_prev.pack(side="left", padx=4)
        
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        lbl_month = tk.Label(cal_hdr, text=f"{month_names[self.cal_month]} {self.cal_year}", 
                             font=("Segoe UI", 14, "bold"), bg=bg, fg=c["fg"])
        lbl_month.pack(side="left", fill="x", expand=True)
        
        btn_next = PillButton(cal_hdr, self.app, "→", command=self._next_month, small=True, outer_bg=bg, min_width=36)
        btn_next.pack(side="right", padx=4)
        
        grid_card = GlassCard(self.cal_view_frame, self.app)
        grid_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        grid_card.inner.configure(bg=c["card"], padx=12, pady=12)
        
        for i in range(7):
            grid_card.inner.columnconfigure(i, weight=1, uniform="cal_col")
        grid_card.inner.rowconfigure(0, weight=0)
        for i in range(1, 7):
            grid_card.inner.rowconfigure(i, weight=1, uniform="cal_row")
            
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for col, wd in enumerate(weekdays):
            lbl = tk.Label(grid_card.inner, text=wd, font=("Segoe UI", 9, "bold"), 
                           bg=c["card"], fg=c["muted"])
            lbl.grid(row=0, column=col, pady=(0, 8), sticky="n")
            
        import calendar
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.cal_year, self.cal_month)
        
        entries_by_day = {}
        for e in self._all_entries:
            if e["date"].year == self.cal_year and e["date"].month == self.cal_month:
                day = e["date"].day
                if day not in entries_by_day:
                    entries_by_day[day] = []
                entries_by_day[day].append(e)
                
        leaves_by_day = {}
        for date_str, leave_type in self._all_leaves.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                if dt.year == self.cal_year and dt.month == self.cal_month:
                    leaves_by_day[dt.day] = leave_type
            except ValueError:
                continue
                
        for row_idx, week in enumerate(weeks, 1):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    self._create_day_cell(grid_card.inner, 0, None, [], None, col_idx, row_idx)
                else:
                    d = date(self.cal_year, self.cal_month, day_num)
                    logs = entries_by_day.get(day_num, [])
                    leave = leaves_by_day.get(day_num, None)
                    self._create_day_cell(grid_card.inner, day_num, d, logs, leave, col_idx, row_idx)

    def _create_day_cell(self, parent, day_num, d, logs, leave_type, col, row_idx):
        c = self.app.colors
        is_weekend = (d.weekday() >= 5) if d else False
        cell_bg = c["bg"] if is_weekend else c["card"]

        cell = tk.Frame(parent, bg=cell_bg, highlightbackground=c["border"], highlightthickness=1)
        cell.grid(row=row_idx, column=col, sticky="nsew", padx=2, pady=2)

        if not d:
            cell.configure(bg="#F9F9FB")
            return cell

        lbl_num = tk.Label(cell, text=str(day_num), font=("Segoe UI", 9, "bold"),
                           bg=cell_bg, fg=c["fg"])
        lbl_num.pack(anchor="nw", padx=6, pady=4)

        badges_container = tk.Frame(cell, bg=cell_bg)
        badges_container.pack(anchor="center", expand=True)

        if leave_type:
            icon = leaves_mod.ICONS.get(leave_type, "")
            lbl = leaves_mod.TYPES.get(leave_type, leave_type)
            badge_bg = "#FFF0F0" if leave_type == "mc_leave" else ("#E8F5E9" if leave_type == "annual_leave" else "#FFF3E0")
            badge_fg = "#D32F2F" if leave_type == "mc_leave" else ("#2E7D32" if leave_type == "annual_leave" else "#E65100")
            badge = tk.Frame(badges_container, bg=badge_bg, padx=6, pady=2, highlightthickness=0)
            badge.pack(pady=2)
            tk.Label(badge, text=f"{icon} {lbl}", font=("Segoe UI", 8, "bold"), bg=badge_bg, fg=badge_fg).pack()

        if logs:
            total_hrs = sum(e["hours"] for e in logs)
            badge_bg = c["sidebar_active_bg"]
            badge_fg = c["sidebar_active"]
            badge_hrs = tk.Frame(badges_container, bg=badge_bg, padx=8, pady=3, highlightthickness=0)
            badge_hrs.pack(pady=2)
            tk.Label(badge_hrs, text=f"{total_hrs:.1f} hrs", font=("Segoe UI", 8, "bold"), bg=badge_bg, fg=badge_fg).pack()
            task_text = logs[0]["task"] if len(logs) == 1 else f"{len(logs)} tasks logged"
            if len(task_text) > 18:
                task_text = task_text[:16] + "..."
            lbl_task = tk.Label(cell, text=task_text, font=("Segoe UI", 8), bg=cell_bg, fg=c["muted"])
            lbl_task.pack(anchor="s", pady=(0, 4))
        elif not leave_type and not is_weekend and d <= date.today():
            badge_bg = "#FFF8EC"
            badge_fg = "#B25E00"
            badge_missed = tk.Frame(badges_container, bg=badge_bg, padx=6, pady=3, highlightthickness=0)
            badge_missed.pack()
            tk.Label(badge_missed, text="⚠ Missed", font=("Segoe UI", 8, "bold"), bg=badge_bg, fg=badge_fg).pack()

        def on_enter(e):
            cell.configure(highlightbackground=c["accent"], highlightthickness=1)
        def on_leave(e):
            cell.configure(highlightbackground=c["border"], highlightthickness=1)
        cell.bind("<Enter>", on_enter)
        cell.bind("<Leave>", on_leave)

        def on_click(e):
            self._on_calendar_day_click(d, logs)
        for widget in [cell, lbl_num] + cell.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.bind("<Button-1>", on_click)
                for child in widget.winfo_children():
                    child.bind("<Button-1>", on_click)
            else:
                widget.bind("<Button-1>", on_click)

    def _on_calendar_day_click(self, d, logs):
        if not logs:
            new_entry = {
                "id": None,
                "date": d,
                "project": "",
                "subproject": "",
                "task": "",
                "hours": 0.0,
                "notes": ""
            }
            EditDialog(self, self.app, new_entry, on_save=self._after_add_missed)
        elif len(logs) == 1:
            EditDialog(self, self.app, logs[0], on_save=self._after_edit)
        else:
            TaskSelectDialog(self, self.app, logs, on_select=self._open_edit_for_entry)

    def _prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        self._refresh_calendar()

    def _next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        self._refresh_calendar()


class EditDialog(tk.Toplevel):
    def __init__(self, parent, app, entry, on_save):
        super().__init__(parent)
        self.app = app
        self.entry = dict(entry)
        self.on_save = on_save
        c = app.colors
        self.configure(bg=c["bg"])
        self.title("Edit Entry" if self.entry.get("id") is not None else "Add Log Entry")
        self.resizable(False, True)
        self.grab_set()
        self._build(c)
        self.update_idletasks()
        # Center over the top-level app window
        top_win = parent.winfo_toplevel()
        top_win.update_idletasks()
        pw = top_win.winfo_width()
        ph = top_win.winfo_height()
        px = top_win.winfo_x()
        py = top_win.winfo_y()
        w = 440
        h = self.winfo_reqheight()
        cx = px + (pw - w) // 2
        cy = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{cx}+{cy}")

    def _build(self, c):
        bg = c["bg"]
        tk.Label(self, text="Edit task" if self.entry.get("id") is not None else "Add task log",
                 font=("Segoe UI", 14, "bold"), bg=bg, fg=c["fg"]
                 ).pack(anchor="w", padx=20, pady=(18, 12))

        card = GlassCard(self, self.app)
        card.pack(fill="x", padx=20, pady=(0, 12))
        inn = card.inner
        inn.configure(bg=c["card"], padx=16, pady=14)

        # DATE row (Universal, always at the top)
        self.date_var = tk.StringVar(value=self.entry["date"].strftime("%Y-%m-%d"))
        
        def _date_row():
            f = tk.Frame(inn, bg=c["card"])
            f.pack(fill="x", pady=(0, 10))
            e = tk.Entry(
                f, textvariable=self.date_var, font=("Segoe UI", 10),
                bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                insertbackground=c["fg"],
                highlightbackground=c["border"], highlightthickness=1
            )
            e.pack(side="left", fill="x", expand=True, ipady=5)
            from ui import icons
            self._cal_img_dialog = icons.get_icon("calendar", theme=self.app.config_data.get("theme", "light"), size=18)
            tk.Button(f, image=self._cal_img_dialog,
                      bg=c["card"], relief="flat", bd=0,
                      activebackground=c["highlight"], activeforeground=c["accent"],
                      cursor="hand2",
                      command=lambda: self._show_calendar(self.date_var)
                      ).pack(side="left", padx=(4, 0))
            return f
            
        tk.Label(inn, text="DATE (YYYY-MM-DD)", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(2, 2))
        _date_row()

        # Entry Type Switcher
        tk.Label(inn, text="ENTRY TYPE", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(6, 2))
                 
        switcher_frame = tk.Frame(inn, bg=c["card"])
        switcher_frame.pack(fill="x", pady=(0, 10))
        
        self.entry_type_var = tk.StringVar(value="log")
        existing_leave = leaves_mod.get(self.entry["date"])
        if existing_leave and self.entry.get("id") is None:
            self.entry_type_var.set("leave")
            
        self.btn_type_log = PillButton(switcher_frame, self.app, "📝 Task Log",
                                       command=lambda: self._set_type("log"),
                                       small=True, outer_bg=c["card"], min_width=110)
        self.btn_type_log.pack(side="left", padx=(0, 6))
        
        self.btn_type_leave = PillButton(switcher_frame, self.app, "🏖 Leave/Holiday",
                                         command=lambda: self._set_type("leave"),
                                         small=True, outer_bg=c["card"], min_width=130)
        self.btn_type_leave.pack(side="left")
        
        if self.entry_type_var.get() == "log":
            self.btn_type_log._primary = True
        else:
            self.btn_type_leave._primary = True

        self.log_fields_frame = tk.Frame(inn, bg=c["card"])
        self.leave_fields_frame = tk.Frame(inn, bg=c["card"])

        # Define _row wrapper for log fields
        def _row(label, widget_fn):
            tk.Label(self.log_fields_frame, text=label, font=("Segoe UI", 8, "bold"),
                     bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(6, 2))
            return widget_fn()

        # Build LOG sub-form
        projects_dict = self.app.config_data.get("projects", {})
        project_names = list(projects_dict.keys())

        self.proj_var = tk.StringVar(value=self.entry["project"])
        if not self.proj_var.get() and project_names:
            self.proj_var.set(project_names[0])
        proj_cb = ttk.Combobox(self.log_fields_frame, textvariable=self.proj_var, values=project_names,
                               font=("Segoe UI", 10), state="readonly")
        _row("PROJECT", lambda: proj_cb.pack(fill="x", ipady=3))

        self.subproj_var = tk.StringVar(value=self.entry.get("subproject", ""))
        self.subproj_cb = ttk.Combobox(self.log_fields_frame, textvariable=self.subproj_var,
                                        font=("Segoe UI", 10), state="readonly")
        _row("SUBPROJECT", lambda: self.subproj_cb.pack(fill="x", ipady=3))
        self._refresh_subprojects()
        proj_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_subprojects())

        self.task_var = tk.StringVar(value=self.entry["task"])
        _row("TASK", lambda: tk.Entry(
            self.log_fields_frame, textvariable=self.task_var, font=("Segoe UI", 10),
            bg=c["input"], fg=c["fg"], relief="flat",
            insertbackground=c["fg"],
            highlightbackground=c["border"], highlightthickness=1
        ).pack(fill="x", ipady=5))

        self.hours_var = tk.StringVar(value=str(self.entry["hours"]))
        _row("HOURS", lambda: tk.Entry(
            self.log_fields_frame, textvariable=self.hours_var, font=("Segoe UI", 10), width=10,
            bg=c["input"], fg=c["fg"], relief="flat",
            insertbackground=c["fg"],
            highlightbackground=c["border"], highlightthickness=1
        ).pack(anchor="w", ipady=5))

        tk.Label(self.log_fields_frame, text="NOTES", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(6, 2))
        self.notes_text = tk.Text(
            self.log_fields_frame, font=("Segoe UI", 10), height=3, wrap="word",
            bg=c["input"], fg=c["fg"], relief="flat",
            insertbackground=c["fg"],
            highlightbackground=c["border"], highlightthickness=1)
        self.notes_text.pack(fill="x", ipady=4)
        self.notes_text.insert("1.0", self.entry.get("notes", ""))

        # Build LEAVE sub-form
        tk.Label(self.leave_fields_frame, text="LEAVE TYPE", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(6, 2))
                 
        leave_options = ["Public Holiday", "Annual Leave", "MC Leave"]
        self.leave_type_var = tk.StringVar()
        if existing_leave:
            friendly_name = leaves_mod.TYPES.get(existing_leave, leave_options[0])
            self.leave_type_var.set(friendly_name)
        else:
            self.leave_type_var.set(leave_options[0])
            
        self.leave_cb = ttk.Combobox(self.leave_fields_frame, textvariable=self.leave_type_var,
                                     values=leave_options, font=("Segoe UI", 10), state="readonly")
        self.leave_cb.pack(fill="x", ipady=3, pady=(0, 10))
        
        # Clear leave button (only show if there is an existing leave)
        if existing_leave:
            self.btn_clear_leave = PillButton(self.leave_fields_frame, self.app, "Clear Leave",
                                              command=self._clear_leave_direct,
                                              small=True, danger=True, outer_bg=c["card"], min_width=110, icon_name="clear")
            self.btn_clear_leave.pack(anchor="w", pady=(10, 0))

        # Show initial sub-form
        if self.entry_type_var.get() == "log":
            self.log_fields_frame.pack(fill="x")
        else:
            self.leave_fields_frame.pack(fill="x")

        # Action Buttons
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        PillButton(btn_row, self.app, "Cancel",
                   command=self.destroy, outer_bg=bg, min_width=88
                   ).pack(side="right", padx=(8, 0))
        PillButton(btn_row, self.app, "Save",
                   command=self._save, primary=True, outer_bg=bg, min_width=88
                   ).pack(side="right")

    def _refresh_subprojects(self):
        projects_dict = self.app.config_data.get("projects", {})
        subs = projects_dict.get(self.proj_var.get(), [])
        self.subproj_cb.configure(values=[""] + subs,
                                  state="readonly" if subs else "disabled")
        if self.subproj_var.get() not in subs:
            self.subproj_var.set("")

    def _set_type(self, etype):
        self.entry_type_var.set(etype)
        if etype == "log":
            self.btn_type_log._primary = True
            self.btn_type_log._draw()
            self.btn_type_leave._primary = False
            self.btn_type_leave._draw()
            
            self.leave_fields_frame.pack_forget()
            self.log_fields_frame.pack(fill="x")
        else:
            self.btn_type_log._primary = False
            self.btn_type_log._draw()
            self.btn_type_leave._primary = True
            self.btn_type_leave._draw()
            
            self.log_fields_frame.pack_forget()
            self.leave_fields_frame.pack(fill="x")
        self.update_idletasks()
        self.geometry(f"440x{self.winfo_reqheight()}")

    def _show_calendar(self, var):
        from ui.glass import CalendarPopup
        CalendarPopup(self, self.app, var)

    def _clear_leave_direct(self):
        try:
            d = datetime.strptime(self.date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            return
        leaves_mod.clear(d)
        self.master.app._dirty = True
        self.master.load()
        if hasattr(self, "btn_clear_leave"):
            self.btn_clear_leave.pack_forget()
        self._set_type("log")

    def _save(self):
        try:
            d = datetime.strptime(self.date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD format.", parent=self)
            return
            
        if self.entry_type_var.get() == "leave":
            friendly_name = self.leave_type_var.get()
            reverse_types = {v: k for k, v in leaves_mod.TYPES.items()}
            leave_key = reverse_types.get(friendly_name, "public_holiday")

            leaves_mod.mark(d, leave_key)
            self.master.app._dirty = True
            self.master.load()
            self.destroy()
            return
            
        # If logging a work task
        try:
            hours = float(self.hours_var.get())
        except ValueError:
            hours = 0.0
            
        self.entry.update({
            "date": d,
            "project": self.proj_var.get(),
            "subproject": self.subproj_var.get().strip(),
            "task": self.task_var.get().strip(),
            "hours": hours,
            "notes": self.notes_text.get("1.0", "end-1c").strip(),
        })
        self.on_save(self.entry)
        self.destroy()


class TaskSelectDialog(tk.Toplevel):
    """A beautiful, premium theme-aware dialog to select a task to edit on multi-task days."""

    def __init__(self, parent, app, entries, on_select):
        super().__init__(parent)
        self.app = app
        self.entries = entries
        self.on_select = on_select
        c = app.colors
        
        self.title("Select Task")
        self.configure(bg=c["bg"])
        self.resizable(False, False)
        self.grab_set()
        
        tk.Label(self, text="Select which task to edit:", font=("Segoe UI", 10, "bold"),
                 bg=c["bg"], fg=c["fg"]).pack(padx=20, pady=(15, 10), anchor="w")
                 
        self.listbox = tk.Listbox(self, font=("Segoe UI", 10), height=6, width=50,
                                  bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                                  selectbackground=c["accent"], selectforeground="#FFFFFF",
                                  highlightbackground=c["border"], highlightthickness=1)
        self.listbox.pack(padx=20, pady=(0, 15))
        
        for e in entries:
            proj = f"{e['project']} > {e['subproject']}" if e.get("subproject") else e["project"]
            self.listbox.insert("end", f"[{proj}] {e['task']} ({e['hours']}h)")
            
        self.listbox.selection_set(0)
        
        btn_row = tk.Frame(self, bg=c["bg"])
        btn_row.pack(fill="x", padx=20, pady=(0, 15))
        
        PillButton(btn_row, app, "Cancel", command=self.destroy, small=True).pack(side="right", padx=(8, 0))
        PillButton(btn_row, app, "Select", command=self._confirm, primary=True, small=True).pack(side="right")
        PillButton(btn_row, app, "Add New", command=self._add_new, small=True, min_width=90, icon_name="add").pack(side="left")
        
        # Center over the top-level app window
        self.update_idletasks()
        top_win = parent.winfo_toplevel()
        top_win.update_idletasks()
        pw = top_win.winfo_width()
        ph = top_win.winfo_height()
        px = top_win.winfo_x()
        py = top_win.winfo_y()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        cx = px + (pw - w) // 2
        cy = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{cx}+{cy}")
        
    def _confirm(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.on_select(self.entries[idx])
        self.destroy()

    def _add_new(self):
        target_date = self.entries[0]["date"]
        self.destroy()
        new_entry = {
            "id": None,
            "date": target_date,
            "project": "",
            "subproject": "",
            "task": "",
            "hours": 0.0,
            "notes": ""
        }
        EditDialog(self.master, self.app, new_entry, on_save=self.master._after_add_missed)
