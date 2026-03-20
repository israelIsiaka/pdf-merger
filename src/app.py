"""
PDF Merger Application - Main UI Module
A professional PDF merging application with platform-native styling.
"""
import datetime
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .merger import PDFMerger
from .history import HistoryManager
from .theme import ThemeManager

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# -- Custom button widget ──────────────────────────────────────────────────────

class _FlatButton(tk.Frame):
    """
    Reliably-coloured button for all platforms.

    macOS's Aqua theme ignores tk.Button bg/fg, so this widget uses a
    Frame (background) + Label (text) and wires up events manually.
    """

    def __init__(self, parent, *, text, command,
                 bg, fg, hover_bg, disabled_fg,
                 font, padx=14, pady=8, width=0, cursor="hand2", **_):
        super().__init__(parent, bg=bg, cursor=cursor)
        self._bg = bg
        self._fg = fg
        self._hover_bg = hover_bg
        self._disabled_fg = disabled_fg
        self._command = command
        self._enabled = True

        lbl_kw = dict(text=text, bg=bg, fg=fg, font=font,
                      padx=padx, pady=pady, cursor=cursor)
        if width:
            lbl_kw["width"] = width
        self._lbl = tk.Label(self, **lbl_kw)
        self._lbl.pack(fill="both", expand=True)

        for w in (self, self._lbl):
            w.bind("<Enter>",           self._on_enter)
            w.bind("<Leave>",           self._on_leave)
            w.bind("<ButtonRelease-1>", self._on_click)

    def _on_enter(self, _=None):
        if self._enabled:
            self._set_bg(self._hover_bg)

    def _on_leave(self, _=None):
        self._set_bg(self._bg)

    def _on_click(self, _=None):
        if self._enabled and self._command:
            self._command()

    def _set_bg(self, color: str):
        self.configure(bg=color)
        self._lbl.configure(bg=color)

    def config(self, **kwargs):
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._enabled = (state != "disabled")
            self._lbl.configure(
                fg=self._fg if self._enabled else self._disabled_fg,
                cursor="hand2" if self._enabled else "arrow",
            )
            self._set_bg(self._bg)
        if kwargs:
            super().config(**kwargs)


# -- Password dialog ───────────────────────────────────────────────────────────

class _PasswordDialog(tk.Toplevel):
    """Modal dialog for entering a password, with optional confirmation field."""

    def __init__(self, parent, theme, ff, title, prompt, confirm=False):
        super().__init__(parent)
        self.result = None
        self._theme = theme
        self._ff = ff
        self._confirm = confirm

        self.title(title)
        self.resizable(False, False)
        self.configure(bg=theme.get_color("bg"))

        self._build(prompt)

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

        self.transient(parent)
        self.grab_set()
        self._pwd_entry.focus_set()
        self.wait_window()

    def _build(self, prompt):
        bg  = self._theme.get_color("bg")
        fg  = self._theme.get_color("label_main")
        sbg = self._theme.get_color("secondary_bg")
        acc = self._theme.get_color("button_bg")

        border = self._theme.get_color("border")
        entry_kw = dict(
            show="*", font=(self._ff, 11),
            bg=sbg, fg=fg,
            insertbackground=acc,
            relief="flat", bd=0, width=32,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=acc,
        )

        tk.Label(
            self, text=prompt, bg=bg, fg=fg,
            font=(self._ff, 11), wraplength=340, justify="left",
        ).pack(pady=(18, 6), padx=22, anchor="w")

        self._pwd_var = tk.StringVar()
        self._pwd_entry = tk.Entry(self, textvariable=self._pwd_var, **entry_kw)
        self._pwd_entry.pack(padx=22, pady=(0, 10))

        self._confirm_var = tk.StringVar()
        if self._confirm:
            tk.Label(
                self, text="Confirm Password:", bg=bg, fg=fg,
                font=(self._ff, 11),
            ).pack(padx=22, anchor="w")
            tk.Entry(self, textvariable=self._confirm_var, **entry_kw).pack(
                padx=22, pady=(4, 10)
            )

        self._err_var = tk.StringVar()
        tk.Label(
            self, textvariable=self._err_var, bg=bg,
            fg=self._theme.get_color("error"),
            font=(self._ff, 9),
        ).pack(padx=22, anchor="w")

        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(pady=(6, 18), padx=22, fill="x")

        cancel_kw = dict(
            bg=self._theme.get_color("secondary_btn_bg"),
            fg=self._theme.get_color("secondary_btn_fg"),
            hover_bg=self._theme.get_color("secondary_btn_hover"),
            disabled_fg=self._theme.get_color("label_secondary"),
            font=(self._ff, 11, "bold"), padx=14, pady=7,
        )
        ok_kw = dict(
            bg=self._theme.get_color("button_bg"),
            fg=self._theme.get_color("button_fg"),
            hover_bg=self._theme.get_color("button_hover"),
            disabled_fg=self._theme.get_color("label_secondary"),
            font=(self._ff, 11, "bold"), padx=14, pady=7,
        )

        _FlatButton(btn_row, text="Cancel", command=self.destroy, **cancel_kw).pack(side="left")
        _FlatButton(btn_row, text="OK",     command=self._submit,  **ok_kw).pack(side="right")

        self.bind("<Return>", lambda _: self._submit())
        self.bind("<Escape>", lambda _: self.destroy())

    def _submit(self):
        pwd = self._pwd_var.get()
        if not pwd:
            self._err_var.set("Password cannot be empty.")
            return
        if self._confirm and pwd != self._confirm_var.get():
            self._err_var.set("Passwords do not match.")
            return
        self.result = pwd
        self.destroy()


# -- Main application window ───────────────────────────────────────────────────

class PDFMergerApp(tk.Tk):
    """Main application window for PDF Merger."""

    def __init__(self):
        super().__init__()

        self.theme  = ThemeManager()
        self.merger = PDFMerger()
        self.history = HistoryManager()

        self.title("PDF Merger")
        self.geometry("860x720")
        self.minsize(780, 640)
        self.resizable(True, True)
        self.configure(bg=self.theme.get_color("bg"))

        self._load_icon()
        self._make_pdf_icon()
        self._build_ui()

    # -- Icon helpers ──────────────────────────────────────────────────────────

    def _load_icon(self):
        """Load application window icon."""
        # Handle both development layout and PyInstaller bundle
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent

        # Windows: prefer .ico via iconbitmap for reliable taskbar/title icon
        import platform
        if platform.system() == "Windows":
            ico = base / "Logo.ico"
            if ico.exists():
                try:
                    self.iconbitmap(str(ico))
                    return
                except Exception as e:
                    print(f"Warning: Could not load .ico icon: {e}")

        # macOS / Linux: iconphoto with .icns or .png
        for name in ("Logo.icns", "Logo.png"):
            candidate = base / name
            if candidate.exists():
                if HAS_PIL:
                    try:
                        img = Image.open(str(candidate))
                        img = img.resize((256, 256), Image.Resampling.LANCZOS)
                        icon = ImageTk.PhotoImage(img)
                        self.iconphoto(True, icon)
                        self._app_icon = icon
                    except Exception as e:
                        print(f"Warning: Could not load icon: {e}")
                elif str(candidate).endswith(".png"):
                    try:
                        icon = tk.PhotoImage(file=str(candidate))
                        self.iconphoto(True, icon)
                        self._app_icon = icon
                    except Exception as e:
                        print(f"Warning: Could not load icon: {e}")
                return

    def _make_pdf_icon(self):
        """Create a small PDF document icon for treeview rows."""
        self._pdf_icon = None
        if not HAS_PIL:
            return
        try:
            W, H = 22, 26
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rectangle([1, 0, W - 2, H - 1], fill="#FFFFFF", outline="#CCCCCC")
            corner = 6
            d.polygon([W - 2 - corner, 0, W - 2, 0, W - 2, corner], fill="#CCCCCC")
            d.polygon([W - 2 - corner, 0, W - 2, corner, W - 2 - corner, corner],
                      fill="#EFEFEF")
            d.rectangle([1, H - 9, W - 2, H - 1], fill="#E53935")
            try:
                from PIL import ImageFont
                fnt = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", 6)
            except Exception:
                from PIL import ImageFont
                fnt = ImageFont.load_default()
            d.text((W // 2, H - 5), "PDF", fill="#FFFFFF", anchor="mm", font=fnt)
            self._pdf_icon = ImageTk.PhotoImage(img)
        except Exception:
            self._pdf_icon = None

    # -- UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._ff = self.theme.get_font("font_family")
        self._fm = self.theme.get_font("font_mono")

        main = tk.Frame(self, bg=self.theme.get_color("bg"))
        main.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        tk.Label(
            main, text="PDF Merger",
            font=(self._ff, 18, "bold"),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main"),
        ).pack(pady=(0, 10))

        self._style_notebook()

        self.notebook = ttk.Notebook(main, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))

        merge_frame   = tk.Frame(self.notebook, bg=self.theme.get_color("bg"))
        protect_frame = tk.Frame(self.notebook, bg=self.theme.get_color("bg"))
        peep_frame    = tk.Frame(self.notebook, bg=self.theme.get_color("bg"))
        history_frame = tk.Frame(self.notebook, bg=self.theme.get_color("bg"))

        self.notebook.add(merge_frame,   text="  Merge PDFs  ")
        self.notebook.add(protect_frame, text="  Protect PDF  ")
        self.notebook.add(peep_frame,    text="  Peep  ")
        self.notebook.add(history_frame, text="  History  ")

        self._build_merge_tab(merge_frame)
        self._build_protect_tab(protect_frame)
        self._build_peep_tab(peep_frame)
        self._build_history_tab(history_frame)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _style_notebook(self):
        bg      = self.theme.get_color("bg")
        tab_bg  = self.theme.get_color("secondary_btn_bg")
        sel_fg  = self.theme.get_color("button_bg")
        fg      = self.theme.get_color("label_main")
        border  = self.theme.get_color("border")

        s = ttk.Style()
        s.configure("Custom.TNotebook",
            background=bg, borderwidth=1,
            tabmargins=[0, 4, 0, 0],
        )
        s.configure("Custom.TNotebook.Tab",
            background=tab_bg, foreground=fg,
            padding=[16, 8],
            font=(self._ff, 11, "bold"),
            borderwidth=0,
        )
        s.map("Custom.TNotebook.Tab",
            background=[("selected", bg)],
            foreground=[("selected", sel_fg)],
            expand=[("selected", [2, 2, 2, 0])],
        )

    # -- Merge tab ─────────────────────────────────────────────────────────────

    def _build_merge_tab(self, parent):
        p = tk.Frame(parent, bg=self.theme.get_color("bg"))
        p.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_action_buttons(p)
        self._build_file_list(p)
        self._build_output_frame(p)
        self._build_progress_frame(p)
        self._build_merge_button(p)

    # -- button factories ──────────────────────────────────────────────────────

    def _primary_kw(self, size=11, padx=14, pady=8, width=0) -> dict:
        return dict(
            bg=self.theme.get_color("button_bg"),
            fg=self.theme.get_color("button_fg"),
            hover_bg=self.theme.get_color("button_hover"),
            disabled_fg=self.theme.get_color("label_secondary"),
            font=(self._ff, size, "bold"),
            padx=padx, pady=pady, width=width,
        )

    def _secondary_kw(self, size=11, padx=14, pady=8, width=0) -> dict:
        return dict(
            bg=self.theme.get_color("secondary_btn_bg"),
            fg=self.theme.get_color("secondary_btn_fg"),
            hover_bg=self.theme.get_color("secondary_btn_hover"),
            disabled_fg=self.theme.get_color("label_secondary"),
            font=(self._ff, size, "bold"),
            padx=padx, pady=pady, width=width,
        )

    def _build_action_buttons(self, parent):
        row = tk.Frame(parent, bg=self.theme.get_color("bg"))
        row.pack(fill="x", pady=(0, 10))

        kw = self._secondary_kw()
        _FlatButton(row, text="+  Add PDFs",        command=self._add_files,       **kw).pack(side="left", padx=(0, 8))
        _FlatButton(row, text="+  Add Folder",      command=self._add_folder,      **kw).pack(side="left", padx=(0, 8))
        _FlatButton(row, text="-  Remove Selected", command=self._remove_selected, **kw).pack(side="left", padx=(0, 8))
        _FlatButton(row, text="-  Clear All",       command=self._clear_all,       **kw).pack(side="left")

    def _build_file_list(self, parent):
        container = tk.Frame(parent, bg=self.theme.get_color("bg"))
        container.pack(fill="both", expand=True, pady=(0, 12))

        reorder = tk.Frame(container, bg=self.theme.get_color("bg"))
        reorder.pack(side="right", fill="y", padx=(10, 0))

        kw = self._secondary_kw(size=10, padx=10, pady=8, width=7)
        _FlatButton(reorder, text="^  Up",   command=self._move_up,   **kw).pack(pady=(0, 6))
        _FlatButton(reorder, text="v  Down", command=self._move_down, **kw).pack()

        # Tonal layering: white (#ffffff) list on #f8fafb background creates
        # natural lift without a hard border line (Design System "No-Line" rule).
        inner = tk.Frame(container, bg=self.theme.get_color("listbox_bg"))
        inner.pack(side="left", fill="both", expand=True)

        s = ttk.Style()
        s.theme_use("default")
        bg  = self.theme.get_color("listbox_bg")
        fg  = self.theme.get_color("listbox_fg")
        sel = self.theme.get_color("listbox_select")
        hbg = self.theme.get_color("tree_header_bg")
        hfg = self.theme.get_color("tree_header_fg")
        alt = self.theme.get_color("tree_alt_bg")

        s.configure("FileList.Treeview",
            background=bg, foreground=fg, fieldbackground=bg,
            rowheight=38, font=(self._fm, 10),
            borderwidth=0, relief="flat",
        )
        s.configure("FileList.Treeview.Heading",
            background=hbg, foreground=hfg,
            font=(self._ff, 10), relief="flat", borderwidth=0,
        )
        s.map("FileList.Treeview",
            background=[("selected", sel)],
            foreground=[("selected", "#FFFFFF")],
        )
        s.map("FileList.Treeview.Heading",
            background=[("active", hbg)],
        )

        scrollbar = tk.Scrollbar(inner)
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            inner,
            columns=("size", "created"),
            show="tree headings",
            selectmode="extended",
            yscrollcommand=scrollbar.set,
            style="FileList.Treeview",
        )

        self.tree.heading("#0",      text="  Name",  anchor="w")
        self.tree.heading("size",    text="Size",    anchor="e")
        self.tree.heading("created", text="Created", anchor="w")

        self.tree.column("#0",      stretch=True,  anchor="w", minwidth=120)
        self.tree.column("size",    width=90,  stretch=False, anchor="e")
        self.tree.column("created", width=190, stretch=False, anchor="w")

        self.tree.tag_configure("even", background=bg)
        self.tree.tag_configure("odd",  background=alt)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

    def _build_output_frame(self, parent):
        tk.Label(
            parent, text="Save As:",
            font=(self._ff, 11, "bold"),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main"),
        ).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(parent, bg=self.theme.get_color("bg"))
        row.pack(fill="x", pady=(0, 10))

        self.output_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "merged_output.pdf")
        )
        tk.Entry(
            row, textvariable=self.output_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"),
            fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        _FlatButton(
            row, text="Browse...", command=self._browse_output,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

    def _build_progress_frame(self, parent):
        s = ttk.Style()
        s.configure("Custom.Horizontal.TProgressbar",
            troughcolor=self.theme.get_color("secondary_bg"),
            background=self.theme.get_color("button_bg"),
            darkcolor=self.theme.get_color("button_bg"),
            lightcolor=self.theme.get_color("button_bg"),
        )
        self.progress = ttk.Progressbar(
            parent, length=400, mode="determinate",
            style="Custom.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(0, 6))

        self.status_var = tk.StringVar(value="Add PDFs to get started.")
        self.status_label = tk.Label(
            parent, textvariable=self.status_var,
            font=(self._ff, 9),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main"),
        )
        self.status_label.pack(anchor="w", pady=(0, 6))

    def _build_merge_button(self, parent):
        self.merge_btn = _FlatButton(
            parent, text="Merge PDFs", command=self._start_merge,
            **self._primary_kw(size=14, padx=30, pady=14),
        )
        self.merge_btn.pack(fill="x")

    # -- Protect PDF tab ───────────────────────────────────────────────────────

    def _build_protect_tab(self, parent):
        p = tk.Frame(parent, bg=self.theme.get_color("bg"))
        p.pack(fill="both", expand=True, padx=16, pady=16)

        bg     = self.theme.get_color("bg")
        fg     = self.theme.get_color("label_main")
        sec_fg = self.theme.get_color("label_secondary")

        tk.Label(
            p, text="Add a password to any PDF file.",
            font=(self._ff, 11), bg=bg, fg=sec_fg,
        ).pack(anchor="w", pady=(0, 18))

        # Input PDF
        tk.Label(p, text="Select PDF:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        row1 = tk.Frame(p, bg=bg)
        row1.pack(fill="x", pady=(0, 14))
        self._protect_input_var = tk.StringVar()
        tk.Entry(
            row1, textvariable=self._protect_input_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _FlatButton(
            row1, text="Browse...", command=self._browse_protect_input,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

        # Output PDF
        tk.Label(p, text="Save Protected PDF As:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        row2 = tk.Frame(p, bg=bg)
        row2.pack(fill="x", pady=(0, 14))
        self._protect_output_var = tk.StringVar()
        tk.Entry(
            row2, textvariable=self._protect_output_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _FlatButton(
            row2, text="Browse...", command=self._browse_protect_output,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

        # Password
        tk.Label(p, text="Password:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        self._protect_pwd_var = tk.StringVar()
        tk.Entry(
            p, textvariable=self._protect_pwd_var, show="*",
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(fill="x", pady=(0, 14))

        # Confirm password
        tk.Label(p, text="Confirm Password:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        self._protect_confirm_var = tk.StringVar()
        tk.Entry(
            p, textvariable=self._protect_confirm_var, show="*",
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(fill="x", pady=(0, 16))

        # Status
        self._protect_status_var = tk.StringVar()
        self._protect_status_lbl = tk.Label(
            p, textvariable=self._protect_status_var,
            font=(self._ff, 9), bg=bg, fg=fg,
        )
        self._protect_status_lbl.pack(anchor="w", pady=(0, 8))

        # Action button
        _FlatButton(
            p, text="Protect PDF", command=self._do_protect,
            **self._primary_kw(size=14, padx=30, pady=14),
        ).pack(fill="x")

    # -- Peep tab ──────────────────────────────────────────────────────────────

    def _build_peep_tab(self, parent):
        p = tk.Frame(parent, bg=self.theme.get_color("bg"))
        p.pack(fill="both", expand=True, padx=16, pady=16)

        bg     = self.theme.get_color("bg")
        fg     = self.theme.get_color("label_main")
        sec_fg = self.theme.get_color("label_secondary")

        tk.Label(
            p,
            text=(
                "Create a preview PDF paired with a password-protected full version.\n"
                "Share the preview freely — viewers must unlock the full file to read the rest."
            ),
            font=(self._ff, 11), bg=bg, fg=sec_fg,
            justify="left", wraplength=600,
        ).pack(anchor="w", pady=(0, 16))

        # Input PDF
        tk.Label(p, text="Select PDF:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        row_in = tk.Frame(p, bg=bg)
        row_in.pack(fill="x", pady=(0, 2))
        self._peep_input_var = tk.StringVar()
        tk.Entry(
            row_in, textvariable=self._peep_input_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _FlatButton(
            row_in, text="Browse...", command=self._browse_peep_input,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

        self._peep_pages_hint_var = tk.StringVar(value="")
        tk.Label(
            p, textvariable=self._peep_pages_hint_var,
            font=(self._ff, 9), bg=bg, fg=sec_fg,
        ).pack(anchor="w", pady=(2, 10))

        # Free view pages
        row_fv = tk.Frame(p, bg=bg)
        row_fv.pack(fill="x", pady=(0, 14))
        tk.Label(row_fv, text="Free View Pages:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(side="left", padx=(0, 10))
        self._peep_pages_var = tk.StringVar(value="1")
        self._peep_spinbox = ttk.Spinbox(
            row_fv, from_=1, to=9999,
            textvariable=self._peep_pages_var,
            width=6, font=(self._ff, 11),
        )
        self._peep_spinbox.pack(side="left", padx=(0, 10))
        tk.Label(
            row_fv, text="pages viewable without a password",
            font=(self._ff, 11), bg=bg, fg=sec_fg,
        ).pack(side="left")

        # Password
        tk.Label(p, text="Password:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        self._peep_pwd_var = tk.StringVar()
        tk.Entry(
            p, textvariable=self._peep_pwd_var, show="*",
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(fill="x", pady=(0, 12))

        # Confirm password
        tk.Label(p, text="Confirm Password:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        self._peep_confirm_var = tk.StringVar()
        tk.Entry(
            p, textvariable=self._peep_confirm_var, show="*",
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(fill="x", pady=(0, 14))

        # Preview output path
        tk.Label(p, text="Preview Output:", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        row_prev = tk.Frame(p, bg=bg)
        row_prev.pack(fill="x", pady=(0, 10))
        self._peep_preview_var = tk.StringVar()
        tk.Entry(
            row_prev, textvariable=self._peep_preview_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _FlatButton(
            row_prev, text="Browse...", command=self._browse_peep_preview,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

        # Full output path
        tk.Label(p, text="Full Output (Password-Protected):", font=(self._ff, 11, "bold"), bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
        row_full = tk.Frame(p, bg=bg)
        row_full.pack(fill="x", pady=(0, 14))
        self._peep_full_var = tk.StringVar()
        tk.Entry(
            row_full, textvariable=self._peep_full_var,
            font=(self._fm, 9),
            bg=self.theme.get_color("secondary_bg"), fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.get_color("border"),
            highlightcolor=self.theme.get_color("button_bg"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _FlatButton(
            row_full, text="Browse...", command=self._browse_peep_full,
            **self._secondary_kw(size=11, padx=14, pady=6),
        ).pack(side="left")

        # Status + action button
        self._peep_status_var = tk.StringVar()
        self._peep_status_lbl = tk.Label(
            p, textvariable=self._peep_status_var,
            font=(self._ff, 9), bg=bg, fg=fg,
        )
        self._peep_status_lbl.pack(anchor="w", pady=(0, 8))

        _FlatButton(
            p, text="Create Peep Files", command=self._do_peep,
            **self._primary_kw(size=14, padx=30, pady=14),
        ).pack(fill="x")

    # -- History tab ───────────────────────────────────────────────────────────

    def _build_history_tab(self, parent):
        p = tk.Frame(parent, bg=self.theme.get_color("bg"))
        p.pack(fill="both", expand=True, padx=16, pady=16)

        bg = self.theme.get_color("bg")
        fg = self.theme.get_color("label_main")

        header = tk.Frame(p, bg=bg)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header, text="Operation History",
            font=(self._ff, 13, "bold"), bg=bg, fg=fg,
        ).pack(side="left")
        _FlatButton(
            header, text="Clear History", command=self._clear_history,
            **self._secondary_kw(size=10, padx=12, pady=6),
        ).pack(side="right")

        inner = tk.Frame(p, bg=self.theme.get_color("listbox_bg"))
        inner.pack(fill="both", expand=True)

        s = ttk.Style()
        s.configure("History.Treeview",
            background=self.theme.get_color("listbox_bg"),
            foreground=self.theme.get_color("listbox_fg"),
            fieldbackground=self.theme.get_color("listbox_bg"),
            rowheight=32, font=(self._fm, 10),
            borderwidth=0, relief="flat",
        )
        s.configure("History.Treeview.Heading",
            background=self.theme.get_color("tree_header_bg"),
            foreground=self.theme.get_color("tree_header_fg"),
            font=(self._ff, 10), relief="flat", borderwidth=0,
        )
        s.map("History.Treeview",
            background=[("selected", self.theme.get_color("listbox_select"))],
            foreground=[("selected", "#FFFFFF")],
        )

        scrollbar = tk.Scrollbar(inner)
        scrollbar.pack(side="right", fill="y")

        self.history_tree = ttk.Treeview(
            inner,
            columns=("type", "file", "date", "protected"),
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set,
            style="History.Treeview",
        )
        self.history_tree.heading("type",      text="Type",      anchor="w")
        self.history_tree.heading("file",      text="File",      anchor="w")
        self.history_tree.heading("date",      text="Date",      anchor="w")
        self.history_tree.heading("protected", text="Protected", anchor="center")

        self.history_tree.column("type",      width=80,  stretch=False, anchor="w")
        self.history_tree.column("file",      stretch=True, anchor="w", minwidth=100)
        self.history_tree.column("date",      width=175, stretch=False, anchor="w")
        self.history_tree.column("protected", width=90,  stretch=False, anchor="center")

        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_tree.yview)

    # -- Merge callbacks ───────────────────────────────────────────────────────

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files", filetypes=[("PDF Files", "*.pdf")]
        )
        count = self.merger.add_files(list(paths))
        self._refresh_treeview()
        self._update_status(f"Added {count} file(s)." if count else "")

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing PDFs")
        if folder:
            count = self.merger.add_folder(folder)
            self._refresh_treeview()
            self._update_status(f"Added {count} file(s) from folder." if count else "")

    def _remove_selected(self):
        indices = sorted(self._selected_indices(), reverse=True)
        for idx in indices:
            self.merger.remove_file(idx)
        self._refresh_treeview()
        self._update_status()

    def _clear_all(self):
        self.merger.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.progress["value"] = 0
        self._update_status()

    def _move_up(self):
        indices = self._selected_indices()
        new_sel = [idx - 1 if self.merger.move_file_up(idx) else idx
                   for idx in indices]
        self._refresh_treeview(restore_selection=new_sel)

    def _move_down(self):
        indices = list(reversed(self._selected_indices()))
        new_sel = [idx + 1 if self.merger.move_file_down(idx) else idx
                   for idx in indices]
        self._refresh_treeview(restore_selection=new_sel)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if path:
            self.output_var.set(path)

    # -- Protect PDF callbacks ─────────────────────────────────────────────────

    def _browse_protect_input(self):
        path = filedialog.askopenfilename(
            title="Select PDF to protect",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if path:
            self._protect_input_var.set(path)
            # Auto-suggest output path if not already set
            if not self._protect_output_var.get():
                stem = path[:-4] if path.lower().endswith(".pdf") else path
                self._protect_output_var.set(stem + "_protected.pdf")

    def _browse_protect_output(self):
        path = filedialog.asksaveasfilename(
            title="Save protected PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if path:
            self._protect_output_var.set(path)

    def _do_protect(self):
        """Handle the Protect PDF button."""
        input_path  = self._protect_input_var.get().strip()
        output_path = self._protect_output_var.get().strip()
        pwd         = self._protect_pwd_var.get()
        confirm     = self._protect_confirm_var.get()

        if not input_path or not os.path.isfile(input_path):
            self._set_protect_status("Please select a valid PDF file.", error=True)
            return
        if not output_path:
            self._set_protect_status("Please set an output file path.", error=True)
            return
        if not pwd:
            self._set_protect_status("Please enter a password.", error=True)
            return
        if pwd != confirm:
            self._set_protect_status("Passwords do not match.", error=True)
            return

        success, message = self.merger.protect_pdf(input_path, output_path, pwd)
        if success:
            self._set_protect_status(f"Saved to: {output_path}")
            self.history.add_protect(output_path)
            self._protect_pwd_var.set("")
            self._protect_confirm_var.set("")
            messagebox.showinfo("Success", message)
        else:
            self._set_protect_status("Failed to protect PDF.", error=True)
            messagebox.showerror("Error", message)

    def _set_protect_status(self, msg: str, error: bool = False):
        color = (self.theme.get_color("error") if error
                 else self.theme.get_color("label_main"))
        self._protect_status_lbl.config(fg=color)
        self._protect_status_var.set(msg)

    # -- Peep callbacks ────────────────────────────────────────────────────────

    def _browse_peep_input(self):
        path = filedialog.askopenfilename(
            title="Select PDF for Peep",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not path:
            return
        self._peep_input_var.set(path)

        # Show total page count and update spinbox upper bound
        try:
            from pypdf import PdfReader as _PR
            total = len(_PR(path).pages)
            self._peep_pages_hint_var.set(f"{total} pages total")
            self._peep_spinbox.configure(to=total)
        except Exception:
            self._peep_pages_hint_var.set("")

        # Auto-fill output paths if not already set
        stem = path[:-4] if path.lower().endswith(".pdf") else path
        if not self._peep_preview_var.get():
            self._peep_preview_var.set(stem + "_peep_preview.pdf")
        if not self._peep_full_var.get():
            self._peep_full_var.set(stem + "_peep_full.pdf")

    def _browse_peep_preview(self):
        path = filedialog.asksaveasfilename(
            title="Save preview PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if path:
            self._peep_preview_var.set(path)

    def _browse_peep_full(self):
        path = filedialog.asksaveasfilename(
            title="Save full PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if path:
            self._peep_full_var.set(path)

    def _do_peep(self):
        input_path   = self._peep_input_var.get().strip()
        preview_path = self._peep_preview_var.get().strip()
        full_path    = self._peep_full_var.get().strip()
        pwd          = self._peep_pwd_var.get()
        confirm      = self._peep_confirm_var.get()

        try:
            free_pages = int(self._peep_pages_var.get())
        except ValueError:
            self._set_peep_status("Free view pages must be a number.", error=True)
            return

        if not input_path or not os.path.isfile(input_path):
            self._set_peep_status("Please select a valid PDF file.", error=True)
            return
        if not preview_path:
            self._set_peep_status("Please set a preview output path.", error=True)
            return
        if not full_path:
            self._set_peep_status("Please set a full output path.", error=True)
            return
        if free_pages < 1:
            self._set_peep_status("Free view pages must be at least 1.", error=True)
            return
        if not pwd:
            self._set_peep_status("Please enter a password.", error=True)
            return
        if pwd != confirm:
            self._set_peep_status("Passwords do not match.", error=True)
            return

        success, message = self.merger.create_peep(
            input_path, free_pages, preview_path, full_path, pwd
        )
        if success:
            self._set_peep_status(
                f"Created: {os.path.basename(preview_path)} + {os.path.basename(full_path)}"
            )
            self.history.add_peep(preview_path, full_path, free_pages)
            self._peep_pwd_var.set("")
            self._peep_confirm_var.set("")
            messagebox.showinfo("Peep Files Created", message)
        else:
            self._set_peep_status("Failed to create peep files.", error=True)
            messagebox.showerror("Error", message)

    def _set_peep_status(self, msg: str, error: bool = False):
        color = (self.theme.get_color("error") if error
                 else self.theme.get_color("label_main"))
        self._peep_status_lbl.config(fg=color)
        self._peep_status_var.set(msg)

    # -- History callbacks ─────────────────────────────────────────────────────

    def _on_tab_change(self, _=None):
        if self.notebook.index("current") == 3:  # History is the 4th tab (index 3)
            self._refresh_history()

    def _refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for entry in self.history.get_entries():
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.datetime.fromisoformat(ts)
                date_str = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                date_str = ts
            protected = "Yes" if entry.get("password_protected") else "No"
            self.history_tree.insert("", "end", values=(
                entry.get("type", ""),
                os.path.basename(entry.get("output", "")),
                date_str,
                protected,
            ))

    def _clear_history(self):
        confirmed = messagebox.askyesno(
            "Clear History", "Clear all history entries?"
        )
        if confirmed:
            self.history.clear()
            self._refresh_history()

    # -- Merge workflow ────────────────────────────────────────────────────────

    def _start_merge(self):
        if not self.merger.get_file_count():
            messagebox.showwarning("No Files", "Please add at least one PDF.")
            self._set_status("Please add PDF files.", error=True)
            return
        output = self.output_var.get().strip()
        if not output:
            messagebox.showwarning("No Output", "Please set an output file path.")
            self._set_status("Please set output path.", error=True)
            return

        # Collect passwords for any encrypted input files
        passwords = self._collect_input_passwords()
        if passwords is None:
            return  # User cancelled

        source_count = self.merger.get_file_count()
        self.merge_btn.config(state="disabled")
        self.progress["value"] = 0

        def progress_cb(pct: int):
            self.after(0, lambda p=pct: self.progress.configure(value=p))

        threading.Thread(
            target=self._merge_worker,
            args=(output, progress_cb, passwords, source_count),
            daemon=True,
        ).start()

    def _collect_input_passwords(self):
        """
        Check for encrypted input files and prompt for each password.
        Returns a dict {filepath: password}, or None if the user cancels.
        """
        encrypted = self.merger.check_encrypted_files()
        if not encrypted:
            return {}

        passwords = {}
        for fp in encrypted:
            name = os.path.basename(fp)
            dlg = _PasswordDialog(
                self, self.theme, self._ff,
                title="Password Required",
                prompt=f"'{name}' is password-protected.\nEnter the password to unlock it:",
                confirm=False,
            )
            if dlg.result is None:
                return None  # Cancelled
            passwords[fp] = dlg.result
        return passwords

    def _merge_worker(self, output_path, progress_callback, passwords, source_count):
        success, message = self.merger.merge(
            output_path, progress_callback, passwords=passwords
        )
        self.after(0, self._merge_done, success, message, source_count, output_path)

    def _merge_done(self, success: bool, message: str, source_count: int, output_path: str):
        self.merge_btn.config(state="normal")
        self.progress["value"] = 100 if success else 0

        if success:
            self._set_status(f"Done! Saved to: {output_path}")
            messagebox.showinfo("Success", message)

            # Ask if user wants to password-protect the merged PDF
            output_pwd = self._ask_output_password()
            protected = False
            if output_pwd:
                ok, msg2 = self.merger.protect_pdf(output_path, output_path, output_pwd)
                if ok:
                    protected = True
                    messagebox.showinfo("Protected", "Password applied to the merged PDF.")
                else:
                    messagebox.showerror("Error", msg2)

            self.history.add_merge(output_path, source_count, protected)
        else:
            self._set_status("Merge failed.", error=True)
            messagebox.showerror("Error", message)

    def _ask_output_password(self):
        """Ask if user wants to password-protect the output. Returns password or None."""
        want = messagebox.askyesno(
            "Password Protect",
            "Would you like to add a password to the merged PDF?",
        )
        if not want:
            return None
        dlg = _PasswordDialog(
            self, self.theme, self._ff,
            title="Set Password",
            prompt="Enter a password for the merged PDF:",
            confirm=True,
        )
        return dlg.result

    # -- Helpers ───────────────────────────────────────────────────────────────

    def _selected_indices(self) -> list:
        children = self.tree.get_children()
        return sorted(list(children).index(iid) for iid in self.tree.selection())

    def _refresh_treeview(self, restore_selection: list = None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, info in enumerate(self.merger.get_file_info()):
            tag = "even" if i % 2 == 0 else "odd"
            kw = dict(
                text=f"   {info['display_name']}",
                values=(info["size_str"], info["created_str"]),
                tags=(tag,),
            )
            if self._pdf_icon:
                kw["image"] = self._pdf_icon
            self.tree.insert("", "end", **kw)

        if restore_selection:
            children = self.tree.get_children()
            for idx in restore_selection:
                if 0 <= idx < len(children):
                    self.tree.selection_add(children[idx])

        self._update_status()

    def _set_status(self, msg: str, error: bool = False):
        color = (self.theme.get_color("error") if error
                 else self.theme.get_color("label_main"))
        self.status_label.config(fg=color)
        self.status_var.set(msg)

    def _update_status(self, msg: str = None):
        count = self.merger.get_file_count()
        if msg:
            self._set_status(msg)
        elif count:
            self._set_status(f"{count} file(s) ready to merge.")
        else:
            self._set_status("Add PDFs to get started.")


def main():
    app = PDFMergerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
