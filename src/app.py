"""
PDF Merger Application - Main UI Module
A professional PDF merging application with platform-native styling.
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .merger import PDFMerger
from .theme import ThemeManager

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ── Custom button widget ──────────────────────────────────────────────────────

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


# ── Main application window ───────────────────────────────────────────────────

class PDFMergerApp(tk.Tk):
    """Main application window for PDF Merger."""

    def __init__(self):
        super().__init__()

        self.theme = ThemeManager()
        self.merger = PDFMerger()

        self.title("PDF Merger")
        self.geometry("820x660")
        self.minsize(760, 600)
        self.resizable(True, True)
        self.configure(bg=self.theme.get_color("bg"))

        self._load_icon()
        self._make_pdf_icon()
        self._build_ui()

    # ── Icon helpers ──────────────────────────────────────────────────────────

    def _load_icon(self):
        """Load application window icon (.icns preferred, .png fallback)."""
        base = Path(__file__).parent.parent
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
            # Page body
            d.rectangle([1, 0, W - 2, H - 1], fill="#FFFFFF", outline="#CCCCCC")
            # Dog-ear fold (top-right)
            corner = 6
            d.polygon([W - 2 - corner, 0, W - 2, 0, W - 2, corner], fill="#CCCCCC")
            d.polygon([W - 2 - corner, 0, W - 2, corner, W - 2 - corner, corner],
                      fill="#EFEFEF")
            # Red label band at bottom
            d.rectangle([1, H - 9, W - 2, H - 1], fill="#E53935")
            # "PDF" label text
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

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._ff = self.theme.get_font("font_family")
        self._fm = self.theme.get_font("font_mono")

        main = tk.Frame(self, bg=self.theme.get_color("bg"))
        main.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            main, text="PDF Merger",
            font=(self._ff, 18, "bold"),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main"),
        ).pack(pady=(0, 8))

        self._build_action_buttons(main)
        self._build_file_list(main)
        self._build_output_frame(main)
        self._build_progress_frame(main)
        self._build_merge_button(main)

    # ── button factories ──────────────────────────────────────────────────────

    def _primary_kw(self, size=11, padx=14, pady=8, width=0) -> dict:
        """Blue accent button (primary action only)."""
        return dict(
            bg=self.theme.get_color("button_bg"),
            fg=self.theme.get_color("button_fg"),
            hover_bg=self.theme.get_color("button_hover"),
            disabled_fg=self.theme.get_color("label_secondary"),
            font=(self._ff, size, "bold"),
            padx=padx, pady=pady, width=width,
        )

    def _secondary_kw(self, size=11, padx=14, pady=8, width=0) -> dict:
        """Gray secondary button (all non-primary actions)."""
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
        _FlatButton(row, text="⊞  Add Folder",      command=self._add_folder,      **kw).pack(side="left", padx=(0, 8))
        _FlatButton(row, text="⊠  Remove Selected", command=self._remove_selected, **kw).pack(side="left", padx=(0, 8))
        _FlatButton(row, text="⊠  Clear All",       command=self._clear_all,       **kw).pack(side="left")

    def _build_file_list(self, parent):
        container = tk.Frame(parent, bg=self.theme.get_color("bg"))
        container.pack(fill="both", expand=True, pady=(0, 12))

        # ── Reorder buttons — pack RIGHT first so border doesn't steal the space
        reorder = tk.Frame(container, bg=self.theme.get_color("bg"))
        reorder.pack(side="right", fill="y", padx=(10, 0))

        kw = self._secondary_kw(size=10, padx=10, pady=8, width=7)
        _FlatButton(reorder, text="↑  Up",   command=self._move_up,   **kw).pack(pady=(0, 6))
        _FlatButton(reorder, text="↓  Down", command=self._move_down, **kw).pack()

        # ── Treeview (left) — packed after reorder so it fills remaining space
        border = tk.Frame(container, bg=self.theme.get_color("border"), bd=1)
        border.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(border, bg=self.theme.get_color("listbox_bg"))
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Style
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

        self.tree.heading("#0",      text="  Name",   anchor="w")
        self.tree.heading("size",    text="Size",     anchor="e")
        self.tree.heading("created", text="Created",  anchor="w")

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
            relief="solid", bd=1,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        _FlatButton(
            row, text="⊞  Browse...", command=self._browse_output,
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

    # ── callbacks ─────────────────────────────────────────────────────────────

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

    # ── merge workflow ────────────────────────────────────────────────────────

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

        self.merge_btn.config(state="disabled")
        self.progress["value"] = 0

        def progress_cb(pct: int):
            self.after(0, lambda p=pct: self.progress.configure(value=p))

        threading.Thread(
            target=self._merge_worker,
            args=(output, progress_cb),
            daemon=True,
        ).start()

    def _merge_worker(self, output_path: str, progress_callback):
        success, message = self.merger.merge(output_path, progress_callback)
        self.after(0, self._merge_done, success, message)

    def _merge_done(self, success: bool, message: str):
        self.merge_btn.config(state="normal")
        self.progress["value"] = 100 if success else 0
        if success:
            self._set_status(f"✓ Done! Saved to: {self.output_var.get()}")
            messagebox.showinfo("Success", message)
        else:
            self._set_status("✗ Merge failed.", error=True)
            messagebox.showerror("Error", message)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _selected_indices(self) -> list:
        """Return sorted list of row indices for the current treeview selection."""
        children = self.tree.get_children()
        return sorted(list(children).index(iid) for iid in self.tree.selection())

    def _refresh_treeview(self, restore_selection: list = None):
        """Rebuild the treeview from the current file list."""
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
