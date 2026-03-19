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
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class PDFMergerApp(tk.Tk):
    """Main application window for PDF Merger."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize theme and merger
        self.theme = ThemeManager()
        self.merger = PDFMerger()
        
        # Window configuration
        self.title("PDF Merger")
        self.geometry("800x600")
        self.resizable(False, False)
        self.configure(bg=self.theme.get_color("bg"))
        
        # Load and set icon
        self._load_icon()
        
        # Build UI
        self._build_ui()
    
    def _load_icon(self):
        """Load and set application icon."""
        icon_path = Path(__file__).parent.parent / "Logo.icns" or \
                   Path(__file__).parent.parent / "Logo.png"
        
        if icon_path.exists() and HAS_PIL:
            try:
                if str(icon_path).endswith(".png"):
                    img = Image.open(icon_path)
                    img = img.resize((256, 256), Image.Resampling.LANCZOS)
                    icon = ImageTk.PhotoImage(img)
                    self.iconphoto(True, icon)
                    self.logo_image = icon
                else:
                    icon = tk.PhotoImage(file=str(icon_path))
                    self.iconphoto(True, icon)
                    self.logo_image = icon
            except Exception as e:
                print(f"Warning: Could not load icon: {e}")
    
    def _build_ui(self):
        """Build the user interface."""
        # Main frame with padding
        main_frame = tk.Frame(self, bg=self.theme.get_color("bg"))
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            main_frame,
            text="PDF Merger",
            font=("Helvetica", 18, "bold"),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main")
        )
        title.pack(pady=(0, 15))
        
        # Button frame
        self._build_button_frame(main_frame)
        
        # File list frame
        self._build_file_list(main_frame)
        
        # Output path frame
        self._build_output_frame(main_frame)
        
        # Progress frame
        self._build_progress_frame(main_frame)
        
        # Merge button
        self._build_merge_button(main_frame)
    
    def _build_button_frame(self, parent):
        """Build top button frame."""
        btn_frame = tk.Frame(parent, bg=self.theme.get_color("bg"))
        btn_frame.pack(fill="x", pady=(0, 10))
        
        button_style = {
            "bg": self.theme.get_color("button_bg"),
            "fg": self.theme.get_color("button_fg"),
            "activebackground": self.theme.get_color("button_hover"),
            "activeforeground": self.theme.get_color("button_fg"),
            "font": ("Helvetica", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 14,
            "pady": 8,
            "cursor": "hand2",
            "highlightthickness": 0,
            "overrelief": "flat",
        }
        
        tk.Button(btn_frame, text="Add PDFs", command=self._add_files, **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Add Folder", command=self._add_folder, **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Remove Selected", command=self._remove_selected, **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Clear All", command=self._clear_all, **button_style).pack(side="left")
    
    def _build_file_list(self, parent):
        """Build file list with scrollbar."""
        list_frame = tk.Frame(parent, bg=self.theme.get_color("bg"))
        list_frame.pack(fill="both", expand=True, pady=(0, 12))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Courier", 10),
            bg=self.theme.get_color("listbox_bg"),
            fg=self.theme.get_color("listbox_fg"),
            selectbackground=self.theme.get_color("listbox_select"),
            selectforeground="#FFFFFF",
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
            activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Reorder buttons
        reorder_frame = tk.Frame(list_frame, bg=self.theme.get_color("bg"))
        reorder_frame.pack(side="right", padx=(8, 0), fill="y")
        
        order_btn_style = {
            "bg": self.theme.get_color("button_bg"),
            "fg": self.theme.get_color("button_fg"),
            "activebackground": self.theme.get_color("button_hover"),
            "activeforeground": self.theme.get_color("button_fg"),
            "font": ("Helvetica", 10, "bold"),
            "width": 8,
            "cursor": "hand2",
            "relief": "flat",
            "bd": 0,
            "padx": 8,
            "pady": 6,
            "highlightthickness": 0,
        }
        
        tk.Button(reorder_frame, text="↑ Up", command=self._move_up, **order_btn_style).pack(pady=4)
        tk.Button(reorder_frame, text="↓ Down", command=self._move_down, **order_btn_style).pack(pady=4)
    
    def _build_output_frame(self, parent):
        """Build output path frame."""
        out_label = tk.Label(
            parent,
            text="Save As:",
            font=("Helvetica", 11, "bold"),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main")
        )
        out_label.pack(anchor="w", pady=(0, 6))
        
        out_frame = tk.Frame(parent, bg=self.theme.get_color("bg"))
        out_frame.pack(fill="x", pady=(0, 12))
        
        self.output_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "merged_output.pdf"))
        
        entry = tk.Entry(
            out_frame,
            textvariable=self.output_var,
            font=("Courier", 9),
            bg=self.theme.get_color("secondary_bg"),
            fg=self.theme.get_color("fg"),
            insertbackground=self.theme.get_color("button_bg"),
            relief="solid",
            bd=1
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        browse_btn = tk.Button(
            out_frame,
            text="Browse",
            command=self._browse_output,
            bg=self.theme.get_color("button_bg"),
            fg=self.theme.get_color("button_fg"),
            activebackground=self.theme.get_color("button_hover"),
            activeforeground=self.theme.get_color("button_fg"),
            font=("Helvetica", 11, "bold"),
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            highlightthickness=0,
        )
        browse_btn.pack(side="left")
    
    def _build_progress_frame(self, parent):
        """Build progress bar and status frame."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.theme.get_color("secondary_bg"),
            background=self.theme.get_color("button_bg"),
            darkcolor=self.theme.get_color("button_bg"),
            lightcolor=self.theme.get_color("button_bg"),
        )
        
        self.progress = ttk.Progressbar(
            parent,
            length=400,
            mode="determinate",
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x", pady=(0, 8))
        
        self.status_var = tk.StringVar(value="Add PDFs to get started.")
        self.status_label = tk.Label(
            parent,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg=self.theme.get_color("bg"),
            fg=self.theme.get_color("label_main")
        )
        self.status_label.pack(anchor="w", pady=(0, 12))
    
    def _build_merge_button(self, parent):
        """Build merge button."""
        self.merge_btn = tk.Button(
            parent,
            text="Merge PDFs",
            font=("Helvetica", 14, "bold"),
            bg=self.theme.get_color("button_bg"),
            fg=self.theme.get_color("button_fg"),
            activebackground=self.theme.get_color("button_hover"),
            activeforeground=self.theme.get_color("button_fg"),
            relief="flat",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            highlightthickness=0,
            command=self._start_merge
        )
        self.merge_btn.pack(fill="x")
    
    # Button callbacks
    
    def _add_files(self):
        """Add PDF files."""
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF Files", "*.pdf")]
        )
        count = self.merger.add_files(list(paths))
        self._refresh_listbox()
        self._update_status(f"Added {count} file(s)." if count else "")
    
    def _add_folder(self):
        """Add folder of PDFs."""
        folder = filedialog.askdirectory(title="Select folder containing PDFs")
        if folder:
            count = self.merger.add_folder(folder)
            self._refresh_listbox()
            self._update_status(f"Added {count} file(s) from folder." if count else "")
    
    def _remove_selected(self):
        """Remove selected files."""
        for idx in reversed(self.listbox.curselection()):
            self.merger.remove_file(idx)
        self._refresh_listbox()
        self._update_status()
    
    def _clear_all(self):
        """Clear all files."""
        self.merger.clear()
        self.listbox.delete(0, tk.END)
        self.progress["value"] = 0
        self._update_status()
    
    def _move_up(self):
        """Move selected files up."""
        for idx in list(self.listbox.curselection()):
            if self.merger.move_file_up(idx):
                self.listbox.delete(idx - 1, idx)
                label = self.merger.get_filenames()[idx - 1]
                self.listbox.insert(idx - 1, label)
        self._refresh_listbox()
    
    def _move_down(self):
        """Move selected files down."""
        for idx in reversed(list(self.listbox.curselection())):
            if self.merger.move_file_down(idx):
                self.listbox.delete(idx, idx + 1)
                label = self.merger.get_filenames()[idx + 1]
                self.listbox.insert(idx + 1, label)
        self._refresh_listbox()
    
    def _browse_output(self):
        """Browse for output file location."""
        path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.output_var.set(path)
    
    def _refresh_listbox(self):
        """Refresh the file list display."""
        self.listbox.delete(0, tk.END)
        for filename in self.merger.get_filenames():
            self.listbox.insert(tk.END, filename)
        self._update_status()
    
    def _start_merge(self):
        """Start PDF merge operation."""
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
        threading.Thread(
            target=self._merge_worker,
            args=(output, self.merger.get_file_count()),
            daemon=True
        ).start()
    
    def _merge_worker(self, output_path, total):
        """Worker thread for merging PDFs."""
        success, message = self.merger.merge(output_path)
        self.after(0, self._merge_done, success, message)
    
    def _merge_done(self, success, message):
        """Handle merge completion."""
        self.merge_btn.config(state="normal")
        self.progress["value"] = 100
        
        if success:
            self._set_status(f"✓ Done! Saved to: {self.output_var.get()}")
            messagebox.showinfo("Success", message)
        else:
            self._set_status("✗ Merge failed.", error=True)
            messagebox.showerror("Error", message)
    
    def _set_status(self, msg, error=False):
        """Set status message with optional error coloring."""
        if error:
            self.status_label.config(fg=self.theme.get_color("error"))
        else:
            self.status_label.config(fg=self.theme.get_color("label_main"))
        self.status_var.set(msg)
    
    def _update_status(self, msg=None):
        """Update status based on file count."""
        count = self.merger.get_file_count()
        if msg:
            self._set_status(msg)
        else:
            if count:
                self._set_status(f"{count} file(s) ready to merge.")
            else:
                self._set_status("Add PDFs to get started.")


def main():
    """Entry point for the application."""
    app = PDFMergerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
