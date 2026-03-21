"""
PDF Merger Application - Main UI Module (PyQt6)
Design System: "The Digital Architect" - Architectural Blue palette.
"""
import datetime
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QProgressBar,
    QSpinBox, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QStyle, QScrollArea,
)

from .dialogs import _PasswordDialog
from .history import HistoryManager
from .merger import PDFMerger
from .stylesheet import build_stylesheet
from .theme import ThemeManager
from .workers import _MergeWorker, _ProtectWorker, _PeepWorker


# -- Main application window ───────────────────────────────────────────────────

class PDFMergerApp(QMainWindow):
    """Main application window for PDF Merger."""

    def __init__(self):
        super().__init__()
        self.theme   = ThemeManager()
        self.merger  = PDFMerger()
        self.history = HistoryManager()

        self._merge_worker   = None
        self._protect_worker = None
        self._peep_worker    = None
        self._source_count   = 0
        self._output_path    = ""

        # Peep auto-generated output paths
        self._peep_preview_path = ""
        self._peep_full_path    = ""

        self.setWindowTitle("PDF Merger")
        self.resize(920, 740)
        self.setMinimumSize(800, 640)

        self._load_icon()
        self._pdf_icon = self._make_pdf_icon()
        self._build_ui()
        self._apply_stylesheet()

    # -- Icon helpers ──────────────────────────────────────────────────────────

    def _load_icon(self):
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent
        for name in ("Logo.icns", "Logo.png", "Logo.ico"):
            candidate = base / name
            if candidate.exists():
                icon = QIcon(str(candidate))
                self.setWindowIcon(icon)
                QApplication.setWindowIcon(icon)
                return

    def _make_pdf_icon(self) -> QIcon:
        px = QPixmap(22, 26)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(QPen(QColor("#CCCCCC"), 1))
        p.drawRoundedRect(1, 0, 19, 25, 2, 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#E53935")))
        p.drawRoundedRect(1, 17, 19, 8, 1, 1)
        p.setPen(QPen(QColor("#FFFFFF")))
        f = QFont()
        f.setPointSize(5)
        f.setBold(True)
        p.setFont(f)
        p.drawText(4, 24, "PDF")
        p.end()
        return QIcon(px)

    def _std_icon(self, sp) -> QIcon:
        """Return a QStyle standard icon."""
        return QApplication.style().standardIcon(sp)

    # -- UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("PDF Merger")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        root.addWidget(self.tabs)

        self.tabs.addTab(self._build_merge_tab(),   "  Merge PDFs  ")
        self.tabs.addTab(self._build_protect_tab(), "  Protect PDF  ")
        self.tabs.addTab(self._build_peep_tab(),    "  Peep  ")
        self.tabs.addTab(self._build_history_tab(), "  History  ")
        self.tabs.addTab(self._build_help_tab(),    "  Help / FAQ  ")

        self.tabs.currentChanged.connect(self._on_tab_change)

    # -- Merge tab ─────────────────────────────────────────────────────────────

    def _build_merge_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Action buttons — primary blue with system icons
        SP = QStyle.StandardPixmap
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for text, slot, icon_sp in [
            ("Add PDFs",        self._add_files,        SP.SP_FileIcon),
            ("Add Folder",      self._add_folder,       SP.SP_DirOpenIcon),
            ("Remove Selected", self._remove_selected,  SP.SP_DialogDiscardButton),
            ("Clear All",       self._clear_all,        SP.SP_DialogResetButton),
        ]:
            b = self._action_btn(text, icon_sp)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # File list + reorder
        list_row = QHBoxLayout()
        list_row.setSpacing(10)

        self.file_tree = QTreeWidget()
        self.file_tree.setObjectName("fileList")
        self.file_tree.setColumnCount(3)
        self.file_tree.setHeaderLabels(["  Name", "Size", "Created"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.setIconSize(QSize(22, 26))
        hdr = self.file_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_tree.setColumnWidth(1, 90)
        self.file_tree.setColumnWidth(2, 190)
        list_row.addWidget(self.file_tree)

        reorder_col = QVBoxLayout()
        reorder_col.setSpacing(8)
        up_btn = self._secondary_btn("Up", SP.SP_ArrowUp)
        up_btn.setFixedWidth(96)
        up_btn.clicked.connect(self._move_up)
        dn_btn = self._secondary_btn("Down", SP.SP_ArrowDown)
        dn_btn.setFixedWidth(96)
        dn_btn.clicked.connect(self._move_down)
        reorder_col.addWidget(up_btn)
        reorder_col.addWidget(dn_btn)
        reorder_col.addStretch()
        list_row.addLayout(reorder_col)
        layout.addLayout(list_row)

        # Save As
        layout.addWidget(self._field_label("Save As:"))
        save_row = QHBoxLayout()
        save_row.setSpacing(8)
        self.output_edit = QLineEdit()
        self.output_edit.setObjectName("inputField")
        self.output_edit.setText(
            os.path.join(os.path.expanduser("~"), "merged_output.pdf")
        )
        save_row.addWidget(self.output_edit)
        browse_btn = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self._browse_output)
        save_row.addWidget(browse_btn)
        layout.addLayout(save_row)

        # Progress + status
        self.progress_bar = self._make_progress()
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Add PDFs to get started.")
        self.status_lbl.setObjectName("statusLabel")
        layout.addWidget(self.status_lbl)

        # Merge button
        self.merge_btn = self._primary_btn("Merge PDFs")
        self.merge_btn.setFixedHeight(52)
        self.merge_btn.clicked.connect(self._start_merge)
        layout.addWidget(self.merge_btn)

        return tab

    # -- Protect tab ───────────────────────────────────────────────────────────

    def _build_protect_tab(self) -> QWidget:
        SP = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        desc = QLabel("Add a password to any PDF file.")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)
        layout.addSpacing(8)

        layout.addWidget(self._field_label("Select PDF:"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self._protect_input = QLineEdit()
        self._protect_input.setObjectName("inputField")
        self._protect_input.setPlaceholderText("Path to PDF file...")
        row.addWidget(self._protect_input)
        b = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b.setFixedWidth(120)
        b.clicked.connect(self._browse_protect_input)
        row.addWidget(b)
        layout.addLayout(row)

        layout.addWidget(self._field_label("Save Protected PDF As:"))
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self._protect_output = QLineEdit()
        self._protect_output.setObjectName("inputField")
        self._protect_output.setPlaceholderText("Output file path (auto-filled on browse)...")
        row2.addWidget(self._protect_output)
        b2 = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b2.setFixedWidth(120)
        b2.clicked.connect(self._browse_protect_output)
        row2.addWidget(b2)
        layout.addLayout(row2)

        layout.addWidget(self._field_label("Password:"))
        _pwd_w, self._protect_pwd = self._make_pwd_field("Enter password...")
        layout.addWidget(_pwd_w)

        layout.addWidget(self._field_label("Confirm Password:"))
        _conf_w, self._protect_confirm = self._make_pwd_field("Confirm password...")
        layout.addWidget(_conf_w)

        # Progress bar + status
        self._protect_progress = self._make_progress()
        layout.addWidget(self._protect_progress)

        self._protect_status = QLabel("")
        self._protect_status.setObjectName("statusLabel")
        layout.addWidget(self._protect_status)

        layout.addStretch()

        self._protect_btn = self._primary_btn("Protect PDF")
        self._protect_btn.setFixedHeight(52)
        self._protect_btn.clicked.connect(self._do_protect)
        layout.addWidget(self._protect_btn)

        return tab

    # -- Peep tab ──────────────────────────────────────────────────────────────

    def _build_peep_tab(self) -> QWidget:
        SP = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        desc = QLabel(
            "Create a preview PDF paired with a password-protected full version.\n"
            "Share the preview freely — viewers must unlock the full file to read the rest."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        # Input PDF — auto-names both outputs on selection
        layout.addWidget(self._field_label("Select PDF:"))
        src_row = QHBoxLayout()
        src_row.setSpacing(8)
        self._peep_input = QLineEdit()
        self._peep_input.setObjectName("inputField")
        self._peep_input.setPlaceholderText("Path to PDF file...")
        src_row.addWidget(self._peep_input)
        b = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b.setFixedWidth(120)
        b.clicked.connect(self._browse_peep_input)
        src_row.addWidget(b)
        layout.addLayout(src_row)

        self._peep_pages_hint = QLabel("")
        self._peep_pages_hint.setObjectName("hintLabel")
        layout.addWidget(self._peep_pages_hint)

        # Free view pages
        fv_row = QHBoxLayout()
        fv_row.setSpacing(10)
        fv_row.addWidget(self._field_label("Free View Pages:"))
        self._peep_spinbox = QSpinBox()
        self._peep_spinbox.setObjectName("spinBox")
        self._peep_spinbox.setMinimum(1)
        self._peep_spinbox.setMaximum(9999)
        self._peep_spinbox.setValue(1)
        self._peep_spinbox.setFixedWidth(80)
        fv_row.addWidget(self._peep_spinbox)
        hint = QLabel("pages viewable without a password")
        hint.setObjectName("hintLabel")
        fv_row.addWidget(hint)
        fv_row.addStretch()
        layout.addLayout(fv_row)

        # Password
        layout.addWidget(self._field_label("Password:"))
        _pwd_w, self._peep_pwd = self._make_pwd_field("Enter password for the full PDF...")
        layout.addWidget(_pwd_w)

        layout.addWidget(self._field_label("Confirm Password:"))
        _conf_w, self._peep_confirm = self._make_pwd_field("Confirm password...")
        layout.addWidget(_conf_w)

        # Auto-named output info panel
        out_panel = QWidget()
        out_panel.setObjectName("outPanel")
        out_layout = QVBoxLayout(out_panel)
        out_layout.setContentsMargins(14, 10, 14, 10)
        out_layout.setSpacing(4)
        out_hdr = QLabel("Output files (saved alongside source PDF):")
        out_hdr.setObjectName("fieldLabel")
        out_layout.addWidget(out_hdr)
        self._peep_preview_lbl = QLabel("  Preview:  (select a PDF above)")
        self._peep_preview_lbl.setObjectName("hintLabel")
        self._peep_full_lbl = QLabel("  Full:     (select a PDF above)")
        self._peep_full_lbl.setObjectName("hintLabel")
        out_layout.addWidget(self._peep_preview_lbl)
        out_layout.addWidget(self._peep_full_lbl)
        layout.addWidget(out_panel)

        # Progress + status
        self._peep_progress = self._make_progress()
        layout.addWidget(self._peep_progress)

        self._peep_status = QLabel("")
        self._peep_status.setObjectName("statusLabel")
        layout.addWidget(self._peep_status)

        layout.addStretch()

        self._peep_btn = self._primary_btn("Create Peep Files")
        self._peep_btn.setFixedHeight(52)
        self._peep_btn.clicked.connect(self._do_peep)
        layout.addWidget(self._peep_btn)

        return tab

    # -- History tab ───────────────────────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("Operation History")
        hdr_lbl.setObjectName("sectionTitle")
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        self.history_tree = QTreeWidget()
        self.history_tree.setObjectName("historyList")
        self.history_tree.setColumnCount(4)
        self.history_tree.setHeaderLabels(["Type", "File", "Date", "Protected"])
        self.history_tree.setAlternatingRowColors(True)
        self.history_tree.setRootIsDecorated(False)
        self.history_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_tree.setUniformRowHeights(True)
        hdr = self.history_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.history_tree.setColumnWidth(0, 90)
        self.history_tree.setColumnWidth(2, 185)
        self.history_tree.setColumnWidth(3, 90)
        layout.addWidget(self.history_tree)

        return tab

    # -- Help / FAQ tab ────────────────────────────────────────────────────────

    def _build_help_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("tabPage")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("helpScroll")
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("tabPage")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 32)
        layout.setSpacing(6)

        def section(title: str):
            lbl = QLabel(title)
            lbl.setObjectName("helpSection")
            layout.addSpacing(18)
            layout.addWidget(lbl)
            layout.addSpacing(4)

        def qa(question: str, answer: str):
            q = QLabel(question)
            q.setObjectName("helpQ")
            q.setWordWrap(True)
            layout.addWidget(q)
            a = QLabel(answer)
            a.setObjectName("helpA")
            a.setWordWrap(True)
            layout.addWidget(a)
            layout.addSpacing(8)

        def table(headers: list, rows: list):
            t = QTreeWidget()
            t.setObjectName("helpTable")
            t.setColumnCount(len(headers))
            t.setHeaderLabels(headers)
            t.setRootIsDecorated(False)
            t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            t.setAlternatingRowColors(True)
            t.setUniformRowHeights(True)
            hdr = t.header()
            hdr.setStretchLastSection(True)
            for i in range(len(headers) - 1):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            for row in rows:
                item = QTreeWidgetItem(row)
                item.setTextAlignment(0, Qt.AlignmentFlag.AlignTop)
                item.setTextAlignment(1, Qt.AlignmentFlag.AlignTop)
                if len(row) > 2:
                    item.setTextAlignment(2, Qt.AlignmentFlag.AlignTop)
                t.addTopLevelItem(item)
            t.resizeColumnToContents(0)
            total_rows = len(rows)
            row_h = 36
            header_h = 32
            t.setFixedHeight(header_h + total_rows * row_h + 4)
            layout.addWidget(t)
            layout.addSpacing(8)

        # ── General ────────────────────────────────────────────────────────────
        section("General")

        qa("What is PDF Merger?",
           "PDF Merger is a desktop app for combining, password-protecting, and "
           "previewing PDFs — all offline.")

        qa("Are my files safe and private?",
           "Yes. Every operation runs entirely on your computer. Your PDFs are never "
           "uploaded, transmitted, or shared with any server.")

        qa("What operating systems are supported?",
           "macOS, Windows, and Linux are all supported. The app automatically "
           "adapts its fonts and colors to match your platform.")

        # ── Merge ──────────────────────────────────────────────────────────────
        section("Merge PDFs")

        qa("How many PDFs can I merge at once?",
           "There is no limit.")

        qa("How do I change the order of files before merging?",
           "Select a file in the list and use the Up and Down buttons on the right. "
           "You can select multiple files at once to move them together.")

        qa("What happens if one of my PDFs is password-protected?",
           "The app detects locked files before the merge starts and asks you for "
           "the password for each one individually. If you enter a wrong password "
           "that file is skipped and the rest are still merged.")

        qa("Can I merge PDFs from different folders?",
           "Yes. Use Add PDFs to pick individual files, or Add Folder to add every "
           "PDF inside a folder at once. Files from different locations can be mixed "
           "freely. If two files share the same filename, the parent folder is shown "
           "in brackets next to the name so you can tell them apart.")

        qa("Will the app warn me before overwriting an existing file?",
           "Yes. A  dialog appears if the output path already exists. "
           "The merge will not proceed until you confirm or choose a different path.")

        qa("Can the output file be the same as one of the input files?",
           "No — the app blocks this and shows an error. Overwriting a source file "
           "mid-read would corrupt it. Choose a different output path.")

        # ── Protect PDF ────────────────────────────────────────────────────────
        section("Protect PDF")

        qa("What kind of encryption is applied?",
           "pypdf applies 128-bit RC4 encryption, which is the standard PDF "
           "password protection format compatible with Adobe Acrobat and most "
           "PDF readers.")

        qa("Can I password-protect the merged output right after merging?",
           "Yes. After a successful merge the app asks if you want to add a "
           "password.")


        qa("What happens if I forget the password?",
           "There is no recovery option. Store the password somewhere safe. "
           "The encryption is designed to make the file unreadable without it.")

        # ── Peep ───────────────────────────────────────────────────────────────
        section("Peep")

        qa("What is Peep?",
           "Peep lets you share a PDF in two parts: a freely viewable preview "
           "containing the first N pages, and a full password-protected version "
           "containing all pages. Readers get a genuine preview before deciding "
           "whether to unlock the full content.")

        qa("What are the two files it creates?",
           "A _peep_preview.pdf (no password, first N pages only) and a "
           "_peep_full.pdf (all pages, password-protected). Both are saved in "
           "the same folder as your source PDF and named automatically.")

        qa("How do I decide how many free pages to allow?",
           "Set the Free View Pages number before clicking Create Peep Files. "
           "A value of 1-3 pages is typical for documents where you want to show "
           "just enough to establish credibility without giving away the content.")

        qa("Can I share the preview file freely?",
           "Yes. The preview file has no password and can be opened by anyone "
           "with any PDF reader. Only the full file requires the password you set.")

        # ── History ────────────────────────────────────────────────────────────
        section("History")

        qa("What does the History tab track?",
           "Every merge, protect, and peep operation is recorded with the output "
           "filename, date and time, and whether the result was password-protected.")

        qa("Where is the history stored?",
           "On your computer. "
           "It is never sent anywhere.")

        qa("Is my history stored in the cloud?",
           "No. The file is local only and never leaves your Computer.")

        # ── Troubleshooting ────────────────────────────────────────────────────
        section("Troubleshooting")

        qa("A file was skipped during merge — why?",
           "The file may be corrupted, have an incompatible internal structure, "
           "or be encrypted without a password being provided. The merge result "
           "dialog lists every skipped file and the reason.")

        qa("The merged PDF has fewer pages than expected — what happened?",
           "One or more input files were likely skipped (see above). Check the "
           "result message for a list of files that could not be read.")

        qa("The progress bar stopped moving — is it frozen?",
           "All operations run on a background thread so the app should stay "
           "responsive. If the bar stops, the operation is likely processing a "
           "very large file. Give it time before assuming something is wrong.")

        # ── Edge Cases table ───────────────────────────────────────────────────
        section(" Cases at a Glance")

        table(
            ["Scenario", "What Happens", "What To Do"],
            [
                ["Password-protected input PDF",
                 "App asks for the password before merging begins",
                 "Enter the correct password for each locked file"],
                ["Wrong password entered",
                 "That file is skipped; merge continues with remaining files",
                 "Re-add the file and try again with the correct password"],
                ["Output path matches an input file",
                 "Blocked — error message shown before anything runs",
                 "Choose a different output file path"],
                ["Output file already exists",
                 "Confirmation dialog shown before overwriting",
                 "Confirm to overwrite or cancel and rename"],
                ["All files fail to read",
                 "Error: no pages could be read from any file",
                 "Check whether the files are corrupted or empty"],
                ["Two files share the same filename",
                 "Parent folder shown in brackets next to the name",
                 "No action needed — it is just for clarity"],
                ["Source file moved or deleted after adding",
                 "That file is skipped during merge with an error note",
                 "Re-add the file from its new location"],
                ["PDF has zero pages",
                 "Clear error shown; operation does not proceed",
                 "Use a valid, non-empty PDF"],
                ["Peep free pages set higher than the PDF page count",
                 "Capped automatically to the total page count",
                 "No action needed"],
                ["Very large PDFs being merged",
                 "Operation takes longer; progress bar stays active",
                 "Wait for the progress bar to complete"],
            ]
        )

        # ── Resource Usage table ───────────────────────────────────────────────
 #       section("Resource Usage")

        # table(
        #     ["Resource", "At Idle", "During an Operation"],
        #     [
        #         ["CPU",
        #          "Near zero",
        #          "One core active (PDF processing is single-threaded)"],
        #         ["RAM",
        #          "60 - 90 MB (app overhead)",
        #          "Adds roughly 1-2x the total size of the PDFs being processed"],
        #         ["Disk",
        #          "None",
        #          "Sequential read of all inputs, one write of the output file"],
        #         ["GPU",
        #          "None",
        #          "Not used — all rendering is CPU-based"],
        #         ["Network",
        #          "None",
        #          "Fully offline — no data is ever sent anywhere"],
        #         ["Threads",
        #          "1 (main UI thread)",
        #          "2 (main + one background worker per operation)"],
        #     ]
        # )  
        
        

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return tab

    # -- Widget factories ──────────────────────────────────────────────────────

    def _make_progress(self) -> QProgressBar:
        bar = QProgressBar()
        bar.setObjectName("progressBar")
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        return bar

    def _primary_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("primaryBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _action_btn(self, text: str, icon_sp=None) -> QPushButton:
        """Primary-coloured action button with optional system icon."""
        btn = QPushButton(text)
        btn.setObjectName("actionBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_sp is not None:
            btn.setIcon(self._std_icon(icon_sp))
            btn.setIconSize(QSize(16, 16))
        return btn

    def _secondary_btn(self, text: str, icon_sp=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("secondaryBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_sp is not None:
            btn.setIcon(self._std_icon(icon_sp))
            btn.setIconSize(QSize(15, 15))
        return btn

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        return lbl

    def _make_pwd_field(self, placeholder: str = "Enter password..."):
        """Return (container_widget, QLineEdit) with a Show/Hide toggle."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        field = QLineEdit()
        field.setObjectName("inputField")
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText(placeholder)

        toggle = QPushButton("Show")
        toggle.setObjectName("eyeBtn")
        toggle.setCheckable(True)
        toggle.setFixedWidth(54)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.toggled.connect(
            lambda checked: (
                field.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked
                    else QLineEdit.EchoMode.Password
                ),
                toggle.setText("Hide" if checked else "Show"),
            )
        )

        row.addWidget(field)
        row.addWidget(toggle)
        return container, field

    def _std_icon(self, sp) -> QIcon:
        return QApplication.style().standardIcon(sp)

    # -- Stylesheet ────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(
            build_stylesheet(self.theme.colors, self.theme.get_font("font_family"))
        )

    # -- Merge callbacks ───────────────────────────────────────────────────────

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        count = self.merger.add_files(paths)
        self._refresh_file_tree()
        self._set_status(f"Added {count} file(s)." if count else "")

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing PDFs"
        )
        if folder:
            count = self.merger.add_folder(folder)
            self._refresh_file_tree()
            self._set_status(
                f"Added {count} file(s) from folder." if count else ""
            )

    def _remove_selected(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            return
        all_items = [
            self.file_tree.topLevelItem(i)
            for i in range(self.file_tree.topLevelItemCount())
        ]
        indices = sorted(
            [all_items.index(item) for item in selected], reverse=True
        )
        for idx in indices:
            self.merger.remove_file(idx)
        self._refresh_file_tree()

    def _clear_all(self):
        self.merger.clear()
        self.file_tree.clear()
        self.progress_bar.setValue(0)
        self._set_status()

    def _move_up(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            return
        all_items = [
            self.file_tree.topLevelItem(i)
            for i in range(self.file_tree.topLevelItemCount())
        ]
        indices = sorted([all_items.index(item) for item in selected])
        new_sel = [
            idx - 1 if self.merger.move_file_up(idx) else idx
            for idx in indices
        ]
        self._refresh_file_tree(restore_selection=new_sel)

    def _move_down(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            return
        all_items = [
            self.file_tree.topLevelItem(i)
            for i in range(self.file_tree.topLevelItemCount())
        ]
        indices = sorted(
            [all_items.index(item) for item in selected], reverse=True
        )
        new_sel = [
            idx + 1 if self.merger.move_file_down(idx) else idx
            for idx in indices
        ]
        self._refresh_file_tree(restore_selection=new_sel)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF As",
            self.output_edit.text(), "PDF Files (*.pdf)"
        )
        if path:
            self.output_edit.setText(path)

    # -- Protect callbacks ─────────────────────────────────────────────────────

    def _browse_protect_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF to Protect", "", "PDF Files (*.pdf)"
        )
        if path:
            self._protect_input.setText(path)
            if not self._protect_output.text():
                stem = path[:-4] if path.lower().endswith(".pdf") else path
                self._protect_output.setText(stem + "_protected.pdf")

    def _browse_protect_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Protected PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._protect_output.setText(path)

    def _do_protect(self):
        input_path  = self._protect_input.text().strip()
        output_path = self._protect_output.text().strip()
        pwd         = self._protect_pwd.text()
        confirm     = self._protect_confirm.text()

        def err(msg):
            self._protect_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._protect_status.setText(msg)

        if not input_path or not os.path.isfile(input_path):
            return err("Please select a valid PDF file.")
        if not output_path:
            return err("Please set an output file path.")
        if not pwd:
            return err("Please enter a password.")
        if pwd != confirm:
            return err("Passwords do not match.")

        # Guard: warn before overwriting (allow same path — intentional in-place)
        if (os.path.realpath(output_path) != os.path.realpath(input_path)
                and os.path.exists(output_path)):
            reply = QMessageBox.question(
                self, "File Already Exists",
                f"'{os.path.basename(output_path)}' already exists.\nOverwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._protect_btn.setEnabled(False)
        self._protect_progress.setValue(0)
        self._protect_status.setStyleSheet("")
        self._protect_status.setText("Protecting...")

        self._protect_worker = _ProtectWorker(
            self.merger, input_path, output_path, pwd
        )
        self._protect_worker.progress_changed.connect(
            self._protect_progress.setValue
        )
        self._protect_worker.protect_done.connect(
            lambda ok, msg: self._protect_done(ok, msg, output_path)
        )
        self._protect_worker.start()

    def _protect_done(self, success: bool, message: str, output_path: str):
        self._protect_btn.setEnabled(True)
        self._protect_progress.setValue(100 if success else 0)
        if success:
            self._protect_status.setStyleSheet(
                f"color: {self.theme.get_color('success')};"
            )
            self._protect_status.setText(
                f"Saved: {os.path.basename(output_path)}"
            )
            self.history.add_protect(output_path)
            self._protect_pwd.clear()
            self._protect_confirm.clear()
            QMessageBox.information(self, "Success", message)
        else:
            self._protect_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._protect_status.setText("Failed to protect PDF.")
            QMessageBox.critical(self, "Error", message)

    # -- Peep callbacks ────────────────────────────────────────────────────────

    def _browse_peep_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF for Peep", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._peep_input.setText(path)

        try:
            from pypdf import PdfReader as _PR
            total = len(_PR(path).pages)
            self._peep_pages_hint.setText(f"{total} pages total")
            self._peep_spinbox.setMaximum(total)
        except Exception:
            self._peep_pages_hint.setText("")

        # Auto-generate output paths alongside the source file
        stem = path[:-4] if path.lower().endswith(".pdf") else path
        self._peep_preview_path = stem + "_peep_preview.pdf"
        self._peep_full_path    = stem + "_peep_full.pdf"

        preview_name = os.path.basename(self._peep_preview_path)
        full_name    = os.path.basename(self._peep_full_path)
        self._peep_preview_lbl.setText(
            f"  Preview:  {preview_name}  (free pages)"
        )
        self._peep_full_lbl.setText(
            f"  Full:     {full_name}  (password-protected)"
        )

    def _do_peep(self):
        input_path = self._peep_input.text().strip()
        pwd        = self._peep_pwd.text()
        confirm    = self._peep_confirm.text()
        free_pages = self._peep_spinbox.value()

        def err(msg):
            self._peep_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._peep_status.setText(msg)

        if not input_path or not os.path.isfile(input_path):
            return err("Please select a valid PDF file.")
        if not self._peep_preview_path or not self._peep_full_path:
            return err("Please select an input PDF first.")
        if free_pages < 1:
            return err("Free view pages must be at least 1.")
        if not pwd:
            return err("Please enter a password.")
        if pwd != confirm:
            return err("Passwords do not match.")

        # Guard: warn before overwriting existing peep output files
        existing = [
            p for p in (self._peep_preview_path, self._peep_full_path)
            if os.path.exists(p)
        ]
        if existing:
            names = " and ".join(f"'{os.path.basename(p)}'" for p in existing)
            reply = QMessageBox.question(
                self, "File Already Exists",
                f"{names} already exist.\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._peep_btn.setEnabled(False)
        self._peep_progress.setValue(0)
        self._peep_status.setStyleSheet("")
        self._peep_status.setText("Creating peep files...")

        self._peep_worker = _PeepWorker(
            self.merger, input_path, free_pages,
            self._peep_preview_path, self._peep_full_path, pwd,
        )
        self._peep_worker.progress_changed.connect(self._peep_progress.setValue)
        self._peep_worker.peep_done.connect(self._peep_done)
        self._peep_worker.start()

    def _peep_done(self, success: bool, message: str):
        self._peep_btn.setEnabled(True)
        self._peep_progress.setValue(100 if success else 0)
        if success:
            self._peep_status.setStyleSheet(
                f"color: {self.theme.get_color('success')};"
            )
            preview_name = os.path.basename(self._peep_preview_path)
            full_name    = os.path.basename(self._peep_full_path)
            self._peep_status.setText(
                f"Created: {preview_name} + {full_name}"
            )
            free = self._peep_spinbox.value()
            self.history.add_peep(
                self._peep_preview_path, self._peep_full_path, free
            )
            self._peep_pwd.clear()
            self._peep_confirm.clear()
            QMessageBox.information(self, "Peep Files Created", message)
        else:
            self._peep_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._peep_status.setText("Failed to create peep files.")
            QMessageBox.critical(self, "Error", message)

    # -- History callbacks ─────────────────────────────────────────────────────

    def _on_tab_change(self, index: int):
        if index == 3:
            self._refresh_history()

    def _refresh_history(self):
        self.history_tree.clear()
        for entry in self.history.get_entries():
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.datetime.fromisoformat(ts)
                date_str = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                date_str = ts
            protected = "Yes" if entry.get("password_protected") else "No"
            item = QTreeWidgetItem([
                entry.get("type", ""),
                os.path.basename(entry.get("output", "")),
                date_str,
                protected,
            ])
            item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
            self.history_tree.addTopLevelItem(item)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History", "Clear all history entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._refresh_history()

    # -- Merge workflow ────────────────────────────────────────────────────────

    def _start_merge(self):
        if not self.merger.get_file_count():
            QMessageBox.warning(self, "No Files", "Please add at least one PDF.")
            self._set_status("Please add PDF files.", error=True)
            return
        output = self.output_edit.text().strip()
        if not output:
            QMessageBox.warning(self, "No Output", "Please set an output file path.")
            self._set_status("Please set output path.", error=True)
            return

        # Guard: output must not be one of the input files
        real_output = os.path.realpath(output)
        real_inputs = {os.path.realpath(p) for p in self.merger.pdf_files}
        if real_output in real_inputs:
            QMessageBox.critical(
                self, "Invalid Output",
                "The output file cannot be the same as one of the input PDFs.\n"
                "Please choose a different output path."
            )
            return

        # Guard: warn before overwriting an existing file
        if os.path.exists(output):
            reply = QMessageBox.question(
                self, "File Already Exists",
                f"'{os.path.basename(output)}' already exists.\nOverwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        passwords = self._collect_input_passwords()
        if passwords is None:
            return

        self._source_count = self.merger.get_file_count()
        self._output_path  = output
        self.merge_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self._merge_worker = _MergeWorker(self.merger, output, passwords)
        self._merge_worker.progress_changed.connect(self.progress_bar.setValue)
        self._merge_worker.merge_done.connect(self._merge_done)
        self._merge_worker.start()

    def _collect_input_passwords(self):
        encrypted = self.merger.check_encrypted_files()
        if not encrypted:
            return {}
        passwords = {}
        for fp in encrypted:
            name = os.path.basename(fp)
            dlg = _PasswordDialog(
                self,
                title="Password Required",
                prompt=(
                    f"'{name}' is password-protected.\n"
                    f"Enter the password to unlock it:"
                ),
                confirm=False,
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return None
            passwords[fp] = dlg.password
        return passwords

    def _merge_done(self, success: bool, message: str):
        self.merge_btn.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)

        if success:
            self._set_status(f"Done! Saved to: {self._output_path}")
            QMessageBox.information(self, "Success", message)

            output_pwd = self._ask_output_password()
            if output_pwd:
                self.merge_btn.setEnabled(False)
                self.progress_bar.setValue(0)
                self._set_status("Applying password...")
                self._protect_worker = _ProtectWorker(
                    self.merger, self._output_path, self._output_path, output_pwd
                )
                self._protect_worker.progress_changed.connect(self.progress_bar.setValue)
                self._protect_worker.protect_done.connect(self._merge_protect_done)
                self._protect_worker.start()
            else:
                self.history.add_merge(self._output_path, self._source_count, False)
        else:
            self._set_status("Merge failed.", error=True)
            QMessageBox.critical(self, "Error", message)

    def _merge_protect_done(self, success: bool, message: str):
        self.merge_btn.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self._set_status("Done! Password applied to merged PDF.")
            QMessageBox.information(self, "Protected", "Password applied to the merged PDF.")
            self.history.add_merge(self._output_path, self._source_count, True)
        else:
            self.progress_bar.setValue(0)
            self._set_status("Password failed.", error=True)
            QMessageBox.critical(self, "Error", message)
            self.history.add_merge(self._output_path, self._source_count, False)

    def _ask_output_password(self):
        reply = QMessageBox.question(
            self, "Password Protect",
            "Would you like to add a password to the merged PDF?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return None
        dlg = _PasswordDialog(
            self,
            title="Set Password",
            prompt="Enter a password for the merged PDF:",
            confirm=True,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return dlg.password

    # -- Helpers ───────────────────────────────────────────────────────────────

    def _refresh_file_tree(self, restore_selection=None):
        self.file_tree.clear()
        for info in self.merger.get_file_info():
            item = QTreeWidgetItem([
                f"   {info['display_name']}",
                info["size_str"],
                info["created_str"],
            ])
            item.setIcon(0, self._pdf_icon)
            item.setTextAlignment(
                1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.file_tree.addTopLevelItem(item)

        if restore_selection:
            for idx in restore_selection:
                it = self.file_tree.topLevelItem(idx)
                if it:
                    it.setSelected(True)

        self._set_status()

    def _set_status(self, msg: str = "", error: bool = False):
        color = (
            self.theme.get_color("error") if error
            else self.theme.get_color("label_main")
        )
        self.status_lbl.setStyleSheet(f"color: {color};")
        if msg:
            self.status_lbl.setText(msg)
        else:
            n = self.merger.get_file_count()
            self.status_lbl.setText(
                f"{n} file(s) ready to merge." if n
                else "Add PDFs to get started."
            )


# -- Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Merger")
    # Fusion style lets QSS fully control all widget colors on every platform.
    # Without it, macOS's native style engine partially overrides backgrounds,
    # breaking dark mode and tonal layering.
    app.setStyle("Fusion")
    window = PDFMergerApp()
    window.show()
    sys.exit(app.exec())
