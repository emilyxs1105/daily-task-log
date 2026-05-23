import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from core import config as cfg_mod
from ui.glass import GlassCard, PillButton, bind_scroll


class Settings(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=parent["bg"])
        self.app = app
        self._build()

    def _cfg(self):
        return self.app.config_data

    def _build(self):
        c = self.app.colors
        bg = c["bg"]
        self.configure(bg=bg)

        # Scrollable wrapper so settings fit on small screens
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(canvas, bg=bg)
        sf.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        canvas.find_withtag("all")[0], width=e.width))
        bind_scroll(canvas)

        # ── Page header ──────────────────────────────────────────────────────
        hdr = tk.Frame(sf, bg=bg)
        hdr.pack(fill="x", padx=24, pady=(22, 2))
        tk.Label(hdr, text="Settings",
                 font=("Segoe UI", 20, "bold"), bg=bg, fg=c["fg"]).pack(anchor="w")
        tk.Label(hdr, text="Configure your app preferences",
                 font=("Segoe UI", 10), bg=bg, fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        # ── Reminder ─────────────────────────────────────────────────────────
        self._section_label(sf, "REMINDER", c)
        rem_card = GlassCard(sf, self.app)
        rem_card.pack(fill="x", padx=24, pady=(6, 0))
        ri = rem_card.inner
        ri.configure(bg=c["card"], padx=18, pady=14)

        self.rem_enabled = tk.BooleanVar(value=self._cfg().get("reminder_enabled", True))
        tk.Checkbutton(ri, text="Enable daily reminder",
                       variable=self.rem_enabled,
                       font=("Segoe UI", 10), bg=c["card"], fg=c["fg"],
                       activebackground=c["card"],
                       selectcolor=c["input"]).pack(anchor="w")

        time_row = tk.Frame(ri, bg=c["card"])
        time_row.pack(anchor="w", pady=(10, 0))
        tk.Label(time_row, text="Reminder time (HH:MM)",
                 font=("Segoe UI", 9), bg=c["card"], fg=c["muted"]
                 ).pack(side="left", padx=(0, 10))
        self.rem_time_var = tk.StringVar(value=self._cfg().get("reminder_time", "17:30"))
        tk.Entry(time_row, textvariable=self.rem_time_var,
                 font=("Segoe UI", 10), width=8,
                 bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                 insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", ipady=5)



        # ── Startup ──────────────────────────────────────────────────────────
        self._section_label(sf, "STARTUP", c)
        startup_card = GlassCard(sf, self.app)
        startup_card.pack(fill="x", padx=24, pady=(6, 0))
        si = startup_card.inner
        si.configure(bg=c["card"], padx=18, pady=14)

        self.autostart_var = tk.BooleanVar(value=self._cfg().get("autostart", False))
        tk.Checkbutton(si, text="Launch on Windows startup (minimised to tray)",
                       variable=self.autostart_var,
                       font=("Segoe UI", 10), bg=c["card"], fg=c["fg"],
                       activebackground=c["card"],
                       selectcolor=c["input"]).pack(anchor="w")

        # ── Data file ────────────────────────────────────────────────────────
        self._section_label(sf, "DATA FILE", c)
        data_card = GlassCard(sf, self.app)
        data_card.pack(fill="x", padx=24, pady=(6, 0))
        di = data_card.inner
        di.configure(bg=c["card"], padx=18, pady=14)

        path_row = tk.Frame(di, bg=c["card"])
        path_row.pack(fill="x")
        self.excel_var = tk.StringVar(value=self._cfg().get("excel_path", ""))
        tk.Entry(path_row, textvariable=self.excel_var,
                 font=("Segoe UI", 9), bg=c["input"], fg=c["fg"],
                 relief="flat", bd=0, insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        PillButton(path_row, self.app, "Browse",
                   command=self._browse, small=True,
                   outer_bg=c["card"], min_width=80
                   ).pack(side="left")

        # ── Projects ─────────────────────────────────────────────────────────
        self._section_label(sf, "PROJECTS & SUBPROJECTS", c)
        proj_card = GlassCard(sf, self.app)
        proj_card.pack(fill="x", padx=24, pady=(6, 0))
        pi = proj_card.inner
        pi.configure(bg=c["card"], padx=18, pady=14)

        # Load projects dict into working copy
        self._proj_data = {k: list(v) for k, v in
                           self._cfg().get("projects", {}).items()}

        panels = tk.Frame(pi, bg=c["card"])
        panels.pack(fill="x", pady=(0, 10))

        # Left panel — projects
        left = tk.Frame(panels, bg=c["card"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(left, text="Projects", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 4))
        self.proj_listbox = tk.Listbox(
            left, font=("Segoe UI", 10), height=6,
            bg=c["input"], fg=c["fg"], relief="flat", bd=0,
            selectbackground=c["accent"], selectforeground="#FFFFFF",
            highlightbackground=c["border"], highlightthickness=1,
            exportselection=False)
        self.proj_listbox.pack(fill="both", expand=True)
        for p in self._proj_data:
            self.proj_listbox.insert("end", p)
        self.proj_listbox.bind("<<ListboxSelect>>", lambda _: self._on_proj_select())

        # Right panel — subprojects
        right = tk.Frame(panels, bg=c["card"])
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Subprojects", font=("Segoe UI", 8, "bold"),
                 bg=c["card"], fg=c["muted"]).pack(anchor="w", pady=(0, 4))
        self.subproj_listbox = tk.Listbox(
            right, font=("Segoe UI", 10), height=6,
            bg=c["input"], fg=c["fg"], relief="flat", bd=0,
            selectbackground=c["accent"], selectforeground="#FFFFFF",
            highlightbackground=c["border"], highlightthickness=1,
            exportselection=False)
        self.subproj_listbox.pack(fill="both", expand=True)

        # Input row
        input_row = tk.Frame(pi, bg=c["card"])
        input_row.pack(anchor="w", pady=(0, 8))
        tk.Label(input_row, text="Name:", font=("Segoe UI", 9),
                 bg=c["card"], fg=c["muted"]).pack(side="left", padx=(0, 6))
        self.new_name_var = tk.StringVar()
        tk.Entry(input_row, textvariable=self.new_name_var,
                 font=("Segoe UI", 10), width=20,
                 bg=c["input"], fg=c["fg"], relief="flat", bd=0,
                 insertbackground=c["fg"],
                 highlightbackground=c["border"], highlightthickness=1
                 ).pack(side="left", ipady=5, padx=(0, 8))

        # Action buttons
        btn_row = tk.Frame(pi, bg=c["card"])
        btn_row.pack(anchor="w")
        PillButton(btn_row, self.app, "+ Project",
                   command=self._add_project, primary=True, small=True,
                   outer_bg=c["card"], min_width=90).pack(side="left", padx=(0, 6))
        PillButton(btn_row, self.app, "+ Subproject",
                   command=self._add_subproject, small=True,
                   outer_bg=c["card"], min_width=110).pack(side="left", padx=(0, 6))
        PillButton(btn_row, self.app, "✏ Rename",
                   command=self._rename_selected, small=True,
                   outer_bg=c["card"], min_width=90).pack(side="left", padx=(0, 6))
        PillButton(btn_row, self.app, "↑ Promote to Project",
                   command=self._promote_subproject, small=True,
                   outer_bg=c["card"], min_width=160).pack(side="left", padx=(0, 6))
        PillButton(btn_row, self.app, "🗑 Remove",
                   command=self._remove_selected, danger=True, small=True,
                   outer_bg=c["card"], min_width=90).pack(side="left")

        # ── Save button ───────────────────────────────────────────────────────
        footer = tk.Frame(sf, bg=bg)
        footer.pack(fill="x", padx=24, pady=(18, 28))
        PillButton(footer, self.app, "Save Settings",
                   command=self._save, primary=True,
                   outer_bg=bg, min_width=140
                   ).pack(side="right")

    def _section_label(self, parent, text, c):
        tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                 bg=c["bg"], fg=c["muted"]).pack(anchor="w", padx=24, pady=(18, 0))

    def _browse(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")],
            title="Choose task log file location",
            initialfile="task_log.xlsx",
            confirmoverwrite=False)
        if path:
            self.excel_var.set(path)
            self._load_from_excel_path(path)

    def _load_from_excel_path(self, path):
        import os
        if not path or not os.path.exists(path):
            return
        excel_cfg = cfg_mod._read_excel_config(path)
        if "reminder_enabled" in excel_cfg:
            self.rem_enabled.set(excel_cfg["reminder_enabled"])
        if "reminder_time" in excel_cfg:
            self.rem_time_var.set(excel_cfg["reminder_time"])
        if "autostart" in excel_cfg:
            self.autostart_var.set(excel_cfg["autostart"])
        if "projects" in excel_cfg:
            self._proj_data = {k: list(v) for k, v in excel_cfg["projects"].items()}
            self.proj_listbox.delete(0, "end")
            self.subproj_listbox.delete(0, "end")
            for p in self._proj_data:
                self.proj_listbox.insert("end", p)

    def _selected_project(self):
        sel = self.proj_listbox.curselection()
        return self.proj_listbox.get(sel[0]) if sel else None

    def _selected_subproject(self):
        sel = self.subproj_listbox.curselection()
        return self.subproj_listbox.get(sel[0]) if sel else None

    def _on_proj_select(self):
        self.subproj_listbox.delete(0, "end")
        proj = self._selected_project()
        if proj:
            for s in self._proj_data.get(proj, []):
                self.subproj_listbox.insert("end", s)

    def _add_project(self):
        name = self.new_name_var.get().strip()
        if not name:
            return
        if name in self._proj_data:
            messagebox.showinfo("Duplicate", "Project already exists.", parent=self.winfo_toplevel())
            return
        self._proj_data[name] = []
        self.proj_listbox.insert("end", name)
        self.new_name_var.set("")

    def _add_subproject(self):
        proj = self._selected_project()
        if not proj:
            messagebox.showinfo("Select project", "Select a project first.", parent=self.winfo_toplevel())
            return
        name = self.new_name_var.get().strip()
        if not name:
            return
        if name in self._proj_data[proj]:
            messagebox.showinfo("Duplicate", "Subproject already exists.", parent=self.winfo_toplevel())
            return
        self._proj_data[proj].append(name)
        self.subproj_listbox.insert("end", name)
        self.new_name_var.set("")

    def _promote_subproject(self):
        proj = self._selected_project()
        sub = self._selected_subproject()
        if not proj or not sub:
            messagebox.showinfo("Select subproject",
                                "Select a project and one of its subprojects.", parent=self.winfo_toplevel())
            return
        if sub in self._proj_data:
            messagebox.showinfo("Duplicate", f'"{sub}" already exists as a project.', parent=self.winfo_toplevel())
            return
        self._proj_data[proj].remove(sub)
        self._proj_data[sub] = []
        self.proj_listbox.insert("end", sub)
        self._on_proj_select()
        messagebox.showinfo("Promoted", f'"{sub}" is now a top-level project.', parent=self.winfo_toplevel())

    def _rename_selected(self):
        sub = self._selected_subproject()
        proj = self._selected_project()
        
        if sub and proj:
            new_name = simpledialog.askstring("Rename Subproject", f'Rename subproject "{sub}" to:', 
                                              initialvalue=sub, parent=self.winfo_toplevel())
            if not new_name:
                return
            new_name = new_name.strip()
            if not new_name or new_name == sub:
                return
            if new_name in self._proj_data[proj]:
                messagebox.showerror("Error", "Subproject already exists.", parent=self.winfo_toplevel())
                return
            
            idx = self._proj_data[proj].index(sub)
            self._proj_data[proj][idx] = new_name
            self._on_proj_select()
            
        elif proj:
            new_name = simpledialog.askstring("Rename Project", f'Rename project "{proj}" to:', 
                                              initialvalue=proj, parent=self.winfo_toplevel())
            if not new_name:
                return
            new_name = new_name.strip()
            if not new_name or new_name == proj:
                return
            if new_name in self._proj_data:
                messagebox.showerror("Error", "Project already exists.", parent=self.winfo_toplevel())
                return
                
            new_proj_data = {}
            for k, v in self._proj_data.items():
                if k == proj:
                    new_proj_data[new_name] = v
                else:
                    new_proj_data[k] = v
            self._proj_data = new_proj_data
            
            self.proj_listbox.delete(0, "end")
            for p in self._proj_data:
                self.proj_listbox.insert("end", p)
            self.subproj_listbox.delete(0, "end")
        else:
            messagebox.showinfo("Select item", "Select a project or subproject first.", parent=self.winfo_toplevel())

    def _remove_selected(self):
        sub = self._selected_subproject()
        proj = self._selected_project()
        if sub and proj:
            if not messagebox.askyesno("Remove", f'Remove subproject "{sub}"?', parent=self.winfo_toplevel()):
                return
            self._proj_data[proj].remove(sub)
            self._on_proj_select()
        elif proj:
            if self._proj_data.get(proj):
                messagebox.showinfo("Not empty",
                                    "Remove all subprojects before removing the project.", parent=self.winfo_toplevel())
                return
            if not messagebox.askyesno("Remove", f'Remove project "{proj}"?', parent=self.winfo_toplevel()):
                return
            del self._proj_data[proj]
            sel = self.proj_listbox.curselection()
            self.proj_listbox.delete(sel[0])
            self.subproj_listbox.delete(0, "end")

    def _save(self):
        time_str = self.rem_time_var.get().strip()
        try:
            h, m = map(int, time_str.split(":"))
            assert 0 <= h <= 23 and 0 <= m <= 59
        except Exception:
            messagebox.showerror("Invalid time", "Enter time as HH:MM (e.g. 17:30)", parent=self.winfo_toplevel())
            return False

        cfg = self._cfg()
        cfg.update({
            "reminder_enabled": self.rem_enabled.get(),
            "reminder_time":    time_str,
            "theme":            "light",
            "autostart":        self.autostart_var.get(),
            "excel_path":       self.excel_var.get().strip(),
            "projects":         self._proj_data,
        })
        cfg_mod.save(cfg)
        cfg_mod.set_autostart(cfg["autostart"])
        self.app.config_data = cfg
        messagebox.showinfo("Saved", "Settings saved.", parent=self.winfo_toplevel())
        self.app.apply_theme()
        return True

    def has_unsaved_changes(self) -> bool:
        cfg = self._cfg()
        if self.rem_enabled.get() != cfg.get("reminder_enabled", True):
            return True
        if self.rem_time_var.get().strip() != cfg.get("reminder_time", "17:30"):
            return True
        if self.autostart_var.get() != cfg.get("autostart", False):
            return True
        if self.excel_var.get().strip() != cfg.get("excel_path", ""):
            return True
        if self._proj_data != cfg.get("projects", {}):
            return True
        return False
