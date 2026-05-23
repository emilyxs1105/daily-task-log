import tkinter as tk
from tkinter import ttk
from datetime import date, datetime, timedelta
from collections import defaultdict
from core import data as db
from ui.glass import GlassCard, PillButton

STATUSES = [
    "Researching", "Designing", "Developing", "Reviewing",
    "Testing", "UAT", "Paused", "Completed", "Cancelled",
]

_STATUS_STYLE = {
    "Researching": ("#EDE7F6", "#7E57C2"),
    "Designing":   ("#E8EAF6", "#5C6BC0"),
    "Developing":  ("#E3F2FD", "#1976D2"),
    "Reviewing":   ("#E0F2F1", "#00897B"),
    "Testing":     ("#FFF3E0", "#E65100"),
    "UAT":         ("#FFFDE7", "#F57F17"),
    "Paused":      ("#EFEBE9", "#6D4C41"),
    "Completed":   ("#E8F5E9", "#2E7D32"),
    "Cancelled":   ("#FFEEE8", "#C62828"),
}
_DEFAULT_STYLE = ("#F5F5F5", "#9E9E9E")


class Summary(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=parent["bg"])
        self.app = app
        self._build()

    def _cfg(self):
        return self.app.config_data

    def _build(self):
        self._entries = []
        c = self.app.colors
        bg = c["bg"]
        self.configure(bg=bg)

        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill="x", padx=24, pady=(22, 2))

        PillButton(hdr, self.app, "↺ Refresh", command=self.load,
                   small=True, outer_bg=bg, min_width=80).pack(side="right", anchor="center")

        title_frame = tk.Frame(hdr, bg=bg)
        title_frame.pack(side="left", fill="y")
        tk.Label(title_frame, text="Summary",
                 font=("Segoe UI", 20, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Label(title_frame, text="Project overview and hours by period",
                 font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        self.group_var = tk.StringVar(value="Month")

        self.content_frame = tk.Frame(self, bg=bg)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=(10, 16))

    def load(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        c = self.app.colors
        bg = c["bg"]

        self._entries = db.load_all(self._cfg()["excel_path"])
        statuses = db.load_project_statuses(self._cfg()["excel_path"])

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(self.content_frame, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=bg)

        _overflows = [False]

        def _on_scroll_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _autoscroll(first, last):
            _overflows[0] = not (float(first) <= 0.0 and float(last) >= 1.0)
            if _overflows[0]:
                sb.grid(row=0, column=1, sticky="ns")
            else:
                sb.grid_remove()
            sb.set(first, last)

        def _on_mousewheel(event):
            if _overflows[0]:
                try:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except tk.TclError:
                    pass

        scroll_frame.bind("<Configure>", _on_scroll_frame_configure)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=_autoscroll)
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add=True)
        canvas.grid(row=0, column=0, sticky="nsew")

        self._build_project_overview(scroll_frame, self._entries, statuses)
        self._build_period_section(scroll_frame, self._entries)

    def _build_project_overview(self, parent, entries, statuses):
        c = self.app.colors
        bg = c["bg"]

        sec_hdr = tk.Frame(parent, bg=bg)
        sec_hdr.pack(fill="x", pady=(0, 8))
        tk.Label(sec_hdr, text="Project Overview",
                 font=("Segoe UI", 13, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Frame(parent, bg=c["border"], height=1).pack(fill="x", pady=(0, 10))

        if not entries:
            tk.Label(parent, text="No entries yet.",
                     font=("Segoe UI", 11), bg=bg, fg=c["muted"]).pack(pady=16)
            return

        proj_data = defaultdict(lambda: {"hours": 0.0, "dates": []})
        for e in entries:
            proj_data[e["project"]]["hours"] += e["hours"]
            proj_data[e["project"]]["dates"].append(e["date"])

        for proj in sorted(proj_data.keys()):
            info = proj_data[proj]
            start = min(info["dates"])
            end = max(info["dates"])
            total_hrs = info["hours"]
            current_status = statuses.get(proj, "")
            card_bg, card_accent = _STATUS_STYLE.get(current_status, _DEFAULT_STYLE)

            card = GlassCard(parent, self.app)
            card.pack(fill="x", pady=(0, 10))
            card._shadow.configure(bg=card_accent)
            card._body.configure(bg=card_bg)
            card._top.configure(bg=card_accent)
            inn = card.inner
            inn.configure(bg=card_bg, padx=18, pady=14)

            top = tk.Frame(inn, bg=card_bg)
            top.pack(fill="x")

            left = tk.Frame(top, bg=card_bg)
            left.pack(side="left", fill="both", expand=True)

            name_lbl = tk.Label(left, text=proj, font=("Segoe UI", 12, "bold"),
                                bg=card_bg, fg=card_accent, anchor="w")
            name_lbl.pack(anchor="w")

            meta = tk.Frame(left, bg=card_bg)
            meta.pack(anchor="w", pady=(4, 0))
            date_str = f"{start.strftime('%d %b %Y')}  →  {end.strftime('%d %b %Y')}"
            date_lbl = tk.Label(meta, text=date_str,
                                font=("Segoe UI", 9), bg=card_bg, fg=card_accent)
            date_lbl.pack(side="left")
            sep_lbl = tk.Label(meta, text="  ·  ",
                               font=("Segoe UI", 9), bg=card_bg, fg=card_accent)
            sep_lbl.pack(side="left")
            hrs_lbl = tk.Label(meta, text=f"{total_hrs:.1f} hrs logged",
                               font=("Segoe UI", 9, "bold"), bg=card_bg, fg=card_accent)
            hrs_lbl.pack(side="left")

            right = tk.Frame(top, bg=card_bg)
            right.pack(side="right", anchor="n", pady=(2, 0))
            self._status_widget(right, proj, current_status, card_bg, card_accent,
                                card, inn, top, left, meta,
                                name_lbl, date_lbl, sep_lbl, hrs_lbl)

    def _status_widget(self, parent, project, current_status,
                        card_bg, card_accent, card, inn, top, left, meta,
                        name_lbl, date_lbl, sep_lbl, hrs_lbl):
        container = tk.Frame(parent, bg=card_bg)
        container.pack(anchor="e")

        pill_canvas = tk.Canvas(container, bg=card_bg, highlightthickness=0,
                                width=110, height=26, cursor="hand2")
        pill_canvas.pack(side="left")

        arrow = tk.Label(container, text="▾", font=("Segoe UI", 9),
                         bg=card_bg, fg=card_accent, cursor="hand2")
        arrow.pack(side="left", padx=(2, 0))

        # Store references needed to repaint the whole card on status change
        pill_canvas._project = project
        pill_canvas._current = current_status
        pill_canvas._card_refs = {
            "card": card, "inn": inn, "top": top, "left": left,
            "meta": meta, "container": container, "arrow": arrow,
            "name_lbl": name_lbl, "date_lbl": date_lbl,
            "sep_lbl": sep_lbl, "hrs_lbl": hrs_lbl, "right": parent,
        }

        pill_canvas.bind("<ButtonRelease-1>",
                         lambda e, p=project, cv=pill_canvas: self._open_status_menu(e, p, cv))
        arrow.bind("<ButtonRelease-1>",
                   lambda e, p=project, cv=pill_canvas: self._open_status_menu(e, p, cv))

        self._draw_status_pill(pill_canvas, current_status, card_bg, card_accent)



    def _open_status_menu(self, event, project, pill_canvas):
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 10),
                       bg="#FFFFFF", fg="#1C1C1E",
                       activebackground=self.app.colors["accent"],
                       activeforeground="#FFFFFF",
                       relief="flat", bd=1)
        for s in STATUSES:
            bg_pill, fg_pill = _STATUS_STYLE[s]
            menu.add_command(
                label=s,
                command=lambda st=s, p=project, cv=pill_canvas: self._set_status(p, st, cv))
        menu.add_separator()
        menu.add_command(label="Clear status",
                         command=lambda p=project, cv=pill_canvas: self._set_status(p, "", cv))
        try:
            menu.tk_popup(event.widget.winfo_rootx(), event.widget.winfo_rooty() + 28)
        finally:
            menu.grab_release()

    def _draw_status_pill(self, canvas, label, card_bg, card_accent):
        canvas.delete("all")
        canvas.configure(bg=card_bg)
        w, h = 110, 26
        r = 11
        # Draw a subtle outlined pill (no fill — card colour shows through)
        canvas.create_oval(0, 1, r * 2, h - 1, fill=card_bg, outline=card_accent, width=1)
        canvas.create_oval(w - r * 2, 1, w, h - 1, fill=card_bg, outline=card_accent, width=1)
        canvas.create_rectangle(r, 1, w - r, h - 1, fill=card_bg, outline=card_bg)
        # Top/bottom border lines
        canvas.create_line(r, 1, w - r, 1, fill=card_accent)
        canvas.create_line(r, h - 1, w - r, h - 1, fill=card_accent)
        text = label if label else "Set status…"
        canvas.create_text(w // 2, h // 2, text=text,
                           fill=card_accent if label else "#AAAAAA",
                           font=("Segoe UI", 9, "bold" if label else "normal"),
                           anchor="center")

    def _set_status(self, project, status, pill_canvas):
        db.save_project_status(self._cfg()["excel_path"], project, status)
        pill_canvas._current = status
        new_bg, new_accent = _STATUS_STYLE.get(status, _DEFAULT_STYLE)
        refs = pill_canvas._card_refs
        # Repaint the whole card with the new colour
        refs["card"]._shadow.configure(bg=new_accent)
        refs["card"]._body.configure(bg=new_bg)
        refs["card"]._top.configure(bg=new_accent)
        for w in (refs["inn"], refs["top"], refs["left"], refs["meta"],
                  refs["container"], refs["right"]):
            w.configure(bg=new_bg)
        refs["name_lbl"].configure(bg=new_bg, fg=new_accent)
        refs["date_lbl"].configure(bg=new_bg, fg=new_accent)
        refs["sep_lbl"].configure(bg=new_bg, fg=new_accent)
        refs["hrs_lbl"].configure(bg=new_bg, fg=new_accent)
        refs["arrow"].configure(bg=new_bg, fg=new_accent)
        self._draw_status_pill(pill_canvas, status, new_bg, new_accent)

    def _build_period_section(self, parent, entries):
        c = self.app.colors
        bg = c["bg"]

        tk.Frame(parent, bg=c["border"], height=1).pack(fill="x", pady=(6, 10))
        sec_hdr = tk.Frame(parent, bg=bg)
        sec_hdr.pack(fill="x", pady=(0, 8))
        tk.Label(sec_hdr, text="Hours by Period",
                 font=("Segoe UI", 13, "bold"), bg=bg, fg=c["fg"]).pack(side="left")
        grp = tk.Frame(sec_hdr, bg=bg)
        grp.pack(side="right", anchor="s", pady=(4, 0))
        tk.Label(grp, text="Group by:", font=("Segoe UI", 9),
                 bg=bg, fg=c["muted"]).pack(side="left", padx=(0, 6))

        self._period_cards_frame = tk.Frame(parent, bg=bg)
        self._period_cards_frame.pack(fill="x")

        for val in ("Week", "Month"):
            tk.Radiobutton(grp, text=val, variable=self.group_var, value=val,
                           font=("Segoe UI", 10), bg=bg, fg=c["fg"],
                           activebackground=bg, selectcolor=c["card"],
                           command=self._reload_period_cards).pack(side="left", padx=2)

        if not entries:
            return

        self._render_period_cards()

    def _reload_period_cards(self):
        for w in self._period_cards_frame.winfo_children():
            w.destroy()
        self._render_period_cards()

    def _render_period_cards(self):
        c = self.app.colors
        entries = self._entries
        if not entries:
            return
        parent = self._period_cards_frame
        group_by = self.group_var.get()
        buckets = defaultdict(lambda: defaultdict(float))
        for e in entries:
            if group_by == "Month":
                key = e["date"].strftime("%B %Y")
            else:
                mon = e["date"] - timedelta(days=e["date"].weekday())
                key = f"Week of {mon.strftime('%d %b %Y')}"
            buckets[key][e["project"]] += e["hours"]

        sorted_keys = sorted(
            buckets.keys(),
            key=lambda k: self._parse_key(k, group_by),
            reverse=True)

        for key in sorted_keys:
            proj_hours = buckets[key]
            total = sum(proj_hours.values())

            period_card = GlassCard(parent, self.app)
            period_card.pack(fill="x", pady=(0, 10))
            inn = period_card.inner
            inn.configure(bg=c["card"], padx=18, pady=14)

            top = tk.Frame(inn, bg=c["card"])
            top.pack(fill="x", pady=(0, 10))
            tk.Label(top, text=key, font=("Segoe UI", 12, "bold"),
                     bg=c["card"], fg=c["fg"]).pack(side="left")
            tk.Label(top, text=f"{total:.1f} hrs total",
                     font=("Segoe UI", 9), bg=c["card"], fg=c["muted"]).pack(side="right")

            tk.Frame(inn, bg=c["border"], height=1).pack(fill="x", pady=(0, 8))

            for i, (proj, hrs) in enumerate(
                    sorted(proj_hours.items(), key=lambda x: -x[1])):
                row_bg = c["bg"] if i % 2 == 0 else c["card"]
                row = tk.Frame(inn, bg=row_bg)
                row.pack(fill="x", pady=2)

                pct = (hrs / total * 100) if total > 0 else 0
                bar_max = 160
                bar_w = max(3, int(pct * bar_max / 100))

                tk.Label(row, text=proj, font=("Segoe UI", 10),
                         bg=row_bg, fg=c["fg"], width=22, anchor="w"
                         ).pack(side="left", padx=(0, 12), pady=4)

                bar_track = tk.Frame(row, bg=c["border"], height=6)
                bar_track.pack(side="left", fill="x", expand=True, pady=10)
                tk.Frame(bar_track, bg=c["accent"], height=6, width=bar_w
                         ).place(x=0, y=0)

                tk.Label(row, text=f"{hrs:.1f} h  ({pct:.0f}%)",
                         font=("Segoe UI", 9), bg=row_bg, fg=c["muted"],
                         width=14, anchor="e"
                         ).pack(side="right", padx=(12, 0), pady=4)

    def _parse_key(self, key, group_by):
        try:
            if group_by == "Month":
                return datetime.strptime(key, "%B %Y")
            return datetime.strptime(key.replace("Week of ", ""), "%d %b %Y")
        except Exception:
            return datetime.min
