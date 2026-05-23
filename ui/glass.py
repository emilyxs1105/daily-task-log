"""Liquid Glass UI helpers — GlassCard container and PillButton widget."""
import tkinter as tk


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_to_hex(r, g, b):
    return f'#{int(r):02x}{int(g):02x}{int(b):02x}'


def adjust_color(hex_color, amount):
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(
        max(0, min(255, r + amount)),
        max(0, min(255, g + amount)),
        max(0, min(255, b + amount)),
    )


def _pill_pts(x1, y1, x2, y2, r):
    r = max(1, min(int(r), (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        x1 + r, y1,  x2 - r, y1,
        x2, y1,      x2, y1 + r,
        x2, y2 - r,  x2, y2,
        x2 - r, y2,  x1 + r, y2,
        x1, y2,      x1, y2 - r,
        x1, y1 + r,  x1, y1,
    ]


def bind_scroll(canvas):
    """Enable mousewheel / touchpad gesture scrolling on a tk.Canvas (Windows)."""
    def _scroll(event):
        try:
            if canvas.winfo_ismapped():
                first, last = canvas.yview()
                if not (first <= 0.0 and last >= 1.0):
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass
    canvas.bind_all("<MouseWheel>", _scroll, add=True)


def apply_mica(hwnd):
    """Enable Windows 11 Mica backdrop (silently no-ops on older Windows)."""
    try:
        import ctypes
        # DWMWA_SYSTEMBACKDROP_TYPE = 38, DWM_SYSTEMBACKDROP_MICA = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 38, ctypes.byref(ctypes.c_int(2)), 4)
    except Exception:
        pass


class GlassCard(tk.Frame):
    """
    A card panel that mimics the Liquid Glass material:
    shadow border → white card body → 1 px top-edge highlight → .inner content.

    Usage:
        card = GlassCard(parent, app)
        card.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(card.inner, text='Hello', bg=app.colors['card']).pack()
    """

    def __init__(self, parent, app, **kw):
        c = app.colors
        outer_bg = kw.pop('outer_bg', c['bg'])
        super().__init__(parent, bg=outer_bg, bd=0, highlightthickness=0, **kw)

        # 1 px shadow frame (slightly darker/contrasting border)
        self._shadow = tk.Frame(self, bg=c['shadow'], bd=0, highlightthickness=0)
        self._shadow.pack(fill='both', expand=True)

        # Card body (1 px inset from shadow)
        self._body = tk.Frame(self._shadow, bg=c['card'], bd=0,
                              highlightthickness=0)
        self._body.pack(fill='both', expand=True, padx=1, pady=1)

        # Top glass-edge highlight strip (1 px)
        self._top = tk.Frame(self._body, bg=c['highlight'], height=1, bd=0)
        self._top.pack(fill='x')

        # Public content frame — callers pack/grid children here
        self.inner = tk.Frame(self._body, bg=c['card'])
        self.inner.pack(fill='both', expand=True)

    def refresh(self, app):
        c = app.colors
        self.configure(bg=c['bg'])
        self._shadow.configure(bg=c['shadow'])
        self._body.configure(bg=c['card'])
        self._top.configure(bg=c['highlight'])
        self.inner.configure(bg=c['card'])


class PillButton(tk.Canvas):
    """
    A fully rounded pill-shaped button drawn on a Canvas.
    Supports primary (filled accent), danger (red), and secondary (outlined) styles,
    along with custom Pillow-rendered color icons next to the text.

    Usage:
        btn = PillButton(parent, app, 'Save', command=fn, primary=True, icon_name='save')
        btn.pack(side='right', padx=(8, 0))
    """

    def __init__(self, parent, app, text='', command=None,
                 primary=False, danger=False, small=False,
                 outer_bg=None, icon_name=None, **kw):
        c = app.colors
        h = 30 if small else 36
        bg = outer_bg if outer_bg is not None else c['bg']
        min_width = kw.pop('min_width', 88)
        
        extra_w = 24 if icon_name else 0
        kw.setdefault('width', max(min_width, len(text) * 8 + 32 + extra_w))
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0,
                         height=h, **kw)

        self._app = app
        self._text = text
        self._cmd = command
        self._primary = primary
        self._danger = danger
        self._small = small
        self._icon_name = icon_name
        self._hovered = False
        self._pressed = False

        self.configure(cursor='hand2')
        self.bind('<Configure>', self._draw)
        self.bind('<Enter>',         lambda _: self._update(hover=True))
        self.bind('<Leave>',         lambda _: self._update(hover=False, pressed=False))
        self.bind('<ButtonPress-1>', lambda _: self._update(pressed=True))
        self.bind('<ButtonRelease-1>', self._click)

    def _update(self, hover=None, pressed=None):
        if hover is not None:
            self._hovered = hover
        if pressed is not None:
            self._pressed = pressed
        self._draw()

    def _click(self, _=None):
        self._update(pressed=False)
        if self._cmd:
            self._cmd()

    def _base(self):
        c = self._app.colors
        if self._danger:
            return '#FF3B30' if c['fg'] == '#1C1C1E' else '#FF453A'
        if self._primary:
            return c['accent']
        return c['card']

    def _draw(self, _=None):
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        c = self._app.colors
        base = self._base()
        delta = -30 if self._pressed else (-14 if self._hovered else 0)
        fill = adjust_color(base, delta)

        is_solid = self._primary or self._danger
        outline = '' if is_solid else c['border']
        fg = '#FFFFFF' if is_solid else c['fg']

        pts = _pill_pts(0, 0, w - 1, h - 1, h // 2)
        self.create_polygon(pts, smooth=True, fill=fill,
                            outline=outline, width=1 if outline else 0)

        fs = 9 if self._small else 10
        fw = 'bold' if self._primary else 'normal'

        if self._icon_name:
            from ui import icons
            isize = 14 if self._small else 18
            img = icons.get_icon(self._icon_name, theme=self._app.config_data.get("theme", "light"), size=isize, selected=self._primary)
            
            # Estimate text width and layout side-by-side
            text_width = len(self._text) * (6 if self._small else 7)
            total_content_width = isize + 6 + text_width
            start_x = (w - total_content_width) // 2
            
            self.create_image(start_x, h // 2, image=img, anchor='w')
            self.create_text(start_x + isize + 6, h // 2, text=self._text, fill=fg,
                             font=('Segoe UI', fs, fw), anchor='w')
        else:
            self.create_text(w // 2, h // 2, text=self._text, fill=fg,
                             font=('Segoe UI', fs, fw), anchor='center')

    def set_text(self, text):
        self._text = text
        self._draw()

    def refresh(self, app):
        c = app.colors
        self.configure(bg=c['bg'])
        self._draw()


class CalendarPopup(tk.Toplevel):
    """A beautiful, lightweight, premium custom calendar date picker in pure Tkinter."""

    def __init__(self, parent, app, target_var):
        super().__init__(parent)
        self.app = app
        self.target_var = target_var

        c = app.colors
        self.title("Select Date")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Premium flat style (no window title bar border decorations if desired, but standard is safer)
        self.configure(bg=c["bg"], highlightbackground=c["border"], highlightthickness=1)

        import calendar
        from datetime import date as d_date, datetime

        try:
            current_val = datetime.strptime(target_var.get().strip(), "%Y-%m-%d").date()
        except Exception:
            current_val = d_date.today()

        self.view_year = current_val.year
        self.view_month = current_val.month
        self.selected_day = current_val.day

        # Header Frame
        self.hdr = tk.Frame(self, bg=c["bg"], pady=10)
        self.hdr.pack(fill="x")

        self.btn_prev = tk.Button(
            self.hdr, text="←", font=("Segoe UI", 10), bg=c["card"], fg=c["fg"],
            relief="flat", bd=0, activebackground=c["highlight"], activeforeground=c["accent"],
            cursor="hand2", padx=8, pady=2, command=self._prev_month)
        self.btn_prev.pack(side="left", padx=12)

        self.lbl_month = tk.Label(self.hdr, font=("Segoe UI", 10, "bold"), bg=c["bg"], fg=c["fg"])
        self.lbl_month.pack(side="left", fill="x", expand=True)

        self.btn_next = tk.Button(
            self.hdr, text="→", font=("Segoe UI", 10), bg=c["card"], fg=c["fg"],
            relief="flat", bd=0, activebackground=c["highlight"], activeforeground=c["accent"],
            cursor="hand2", padx=8, pady=2, command=self._next_month)
        self.btn_next.pack(side="right", padx=12)

        # Calendar Grid
        self.grid_frame = tk.Frame(self, bg=c["bg"], padx=12, pady=8)
        self.grid_frame.pack()

        self._render()

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

    def _render(self):
        import calendar
        from datetime import date as d_date
        c = self.app.colors

        # Clear existing grid
        for w in self.grid_frame.winfo_children():
            w.destroy()

        # Update Month Label
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        self.lbl_month.configure(text=f"{month_names[self.view_month]} {self.view_year}")

        # Weekday Headers
        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, wd in enumerate(weekdays):
            lbl = tk.Label(self.grid_frame, text=wd, font=("Segoe UI", 8, "bold"),
                           bg=c["bg"], fg=c["muted"], width=4, height=1)
            lbl.grid(row=0, column=col, pady=(0, 6))

        # Get Days Grid
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.view_year, self.view_month)

        for row_idx, week in enumerate(weeks, 1):
            for col_idx, day in enumerate(week):
                if day == 0:
                    lbl = tk.Label(self.grid_frame, text="", bg=c["bg"], width=4, height=1)
                    lbl.grid(row=row_idx, column=col_idx)
                else:
                    is_selected = (day == self.selected_day)
                    
                    if is_selected:
                        bg_color = c["accent"]
                        fg_color = "#FFFFFF"
                        font_style = ("Segoe UI", 9, "bold")
                    else:
                        bg_color = c["card"]
                        fg_color = c["fg"]
                        font_style = ("Segoe UI", 9)

                    btn = tk.Button(
                        self.grid_frame, text=str(day), font=font_style,
                        bg=bg_color, fg=fg_color, relief="flat", bd=0,
                        activebackground=c["highlight"], activeforeground=c["accent"],
                        width=4, height=1, cursor="hand2",
                        command=lambda d=day: self._select_day(d))
                    btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)

    def _select_day(self, day):
        from datetime import date as d_date
        selected = d_date(self.view_year, self.view_month, day)
        self.target_var.set(selected.strftime("%Y-%m-%d"))
        self.destroy()

    def _prev_month(self):
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self.selected_day = None
        self._render()

    def _next_month(self):
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self.selected_day = None
        self._render()
