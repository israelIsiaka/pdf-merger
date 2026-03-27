"""
PDF Merger Application - Main UI Module (PyQt6)
Design System: "The Digital Architect" - Architectural Blue palette.
"""
import datetime
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QProgressBar,
    QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QStyle, QScrollArea,
    QButtonGroup, QRadioButton, QSlider, QStackedWidget,
)

from .annotation_dialog import _AnnotateDialog
from .annotation_profiles import AnnotationProfilesManager
from .annotator import PDFAnnotator
from .compressor import PDFCompressor, LEVEL_LIGHT, LEVEL_MEDIUM, LEVEL_HIGH, LEVEL_LABELS, LEVEL_DESCRIPTIONS
from .converter import (PDFToWordConverter, WordToPDFConverter,
                        PDFToImagesConverter, ImagesToPDFConverter)
from .faq import build_faq_widget
from .dialogs import _PasswordDialog
from .history import HistoryManager
from .merger import PDFMerger
from .splitter import PDFSplitter
from .stylesheet import build_stylesheet
from .theme import ThemeManager
from .utils import PlatformInfo
from .viewer import PDFViewerWidget
from .watermark import (PDFWatermarker, POSITION_GRID, POSITION_LABELS,
                        POS_MID_CENTER, FREQ_LABELS,
                        FREQ_ALL, FREQ_ODD, FREQ_EVEN, FREQ_FIRST, FREQ_LAST)
from .workers import (_MergeWorker, _ProtectWorker, _PeepWorker,
                      _CompressWorker, _WatermarkWorker, _WatermarkPreviewWorker,
                      _SplitWorker, _PdfToWordWorker, _WordToPdfWorker,
                      _PdfToImagesWorker, _ImagesToPdfWorker)


# -- Main application window ───────────────────────────────────────────────────

class PDFMergerApp(QMainWindow):
    """Main application window for PDF Merger."""

    def __init__(self, license_mgr=None):
        super().__init__()
        self._license_mgr      = license_mgr
        self.theme             = ThemeManager()
        self.merger            = PDFMerger()
        self.history           = HistoryManager()
        self.compressor        = PDFCompressor()
        self.watermarker       = PDFWatermarker()
        self.annotator         = PDFAnnotator()
        self.annotation_profiles = AnnotationProfilesManager()
        self.splitter          = PDFSplitter()
        self.pdf_to_word       = PDFToWordConverter()
        self.word_to_pdf       = WordToPDFConverter()
        self.pdf_to_images     = PDFToImagesConverter()
        self.images_to_pdf     = ImagesToPDFConverter()

        self._merge_worker      = None
        self._protect_worker    = None
        self._peep_worker       = None
        self._compress_worker   = None
        self._wm_worker         = None
        self._wm_preview_worker = None
        self._split_worker      = None
        self._p2w_worker        = None
        self._w2p_worker        = None
        self._p2i_worker        = None
        self._i2p_worker        = None

        # Full paths for file fields (displayed as basename only)
        self._protect_input_path   = ""
        self._protect_output_path  = ""
        self._peep_input_path      = ""
        self._compress_input_path  = ""
        self._compress_output_path = ""
        self._wm_input_path        = ""
        self._wm_image_path        = ""
        self._wm_output_path       = ""
        self._wm_page_index        = 0
        self._wm_page_count        = 0
        self._wm_preview_timer     = None   # created after _build_ui
        self._split_input_path     = ""
        self._split_output_dir     = ""
        self._p2w_input_path       = ""
        self._p2w_output_path      = ""
        self._w2p_input_path       = ""
        self._w2p_output_path      = ""
        self._p2i_input_path       = ""
        self._p2i_output_dir       = ""
        self._i2p_image_paths: list = []
        self._i2p_output_path      = ""

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

        # Debounce timer for watermark live preview (fires 400 ms after last change)
        self._wm_preview_timer = QTimer(self)
        self._wm_preview_timer.setSingleShot(True)
        self._wm_preview_timer.setInterval(400)
        self._wm_preview_timer.timeout.connect(self._start_wm_preview)

        # Poll every 3 s for OS dark/light mode changes and re-theme if needed
        self._theme_timer = QTimer(self)
        self._theme_timer.setInterval(3000)
        self._theme_timer.timeout.connect(self._check_theme_change)
        self._theme_timer.start()

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
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Stacked widget: page 0 = home, page 1 = tools ────────────────────
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # Page 0 — home view
        from .home_view import HomeView
        self._home_view = HomeView()
        self._home_view.tool_selected.connect(self._open_tool)
        self._stack.addWidget(self._home_view)

        # Page 1 — tools view (constellation background + tabs)
        from .home_view import _ConstellationBg
        tools_page = QWidget()
        tools_page.setObjectName("toolsPage")
        tpl = QVBoxLayout(tools_page)
        tpl.setContentsMargins(0, 0, 0, 0)
        tpl.setSpacing(0)

        # Constellation background for tools page
        self._tools_bg = _ConstellationBg(tools_page)
        self._tools_bg.lower()

        # Home button strip
        home_strip = QWidget()
        home_strip.setObjectName("homeStrip")
        home_strip.setFixedHeight(40)
        home_strip.setAutoFillBackground(False)
        hs_layout = QHBoxLayout(home_strip)
        hs_layout.setContentsMargins(16, 4, 16, 4)
        hs_layout.setSpacing(0)

        home_btn = QPushButton("  Home")
        home_btn.setObjectName("homeBtn")
        home_btn.setFixedHeight(28)
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        hs_layout.addWidget(home_btn)
        hs_layout.addStretch()

        tpl.addWidget(home_strip)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")

        self.tabs.addTab(self._build_merge_tab(),        "  Merge PDFs  ")
        self.tabs.addTab(self._build_protect_tab(),      "  Protect PDF  ")
        self.tabs.addTab(self._build_peep_tab(),         "  Peep  ")
        self.tabs.addTab(self._build_viewer_tab(),       "  View PDF  ")
        self.tabs.addTab(self._build_compress_tab(),     "  Compress PDF  ")
        self.tabs.addTab(self._build_watermark_tab(),    "  Watermark  ")
        self.tabs.addTab(self._build_split_tab(),        "  Split PDF  ")
        self.tabs.addTab(self._build_pdf_to_word_tab(),  "  PDF to Word  ")
        self.tabs.addTab(self._build_word_to_pdf_tab(),  "  Word to PDF  ")
        self.tabs.addTab(self._build_pdf_to_img_tab(),   "  PDF to Image  ")
        self.tabs.addTab(self._build_img_to_pdf_tab(),   "  Image to PDF  ")
        self.tabs.addTab(self._build_history_tab(),      "  History  ")
        self.tabs.addTab(self._build_help_tab(),         "  Help / FAQ  ")

        self.tabs.setUsesScrollButtons(True)
        self.tabs.currentChanged.connect(self._on_tab_change)

        tpl.addWidget(self.tabs)
        self._stack.addWidget(tools_page)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, '_tools_bg') and self._tools_bg.parent():
            self._tools_bg.resize(self._tools_bg.parent().size())

    def _open_tool(self, tab_index: int):
        self.tabs.setCurrentIndex(tab_index)
        self._stack.setCurrentIndex(1)

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

        # Sort order
        sort_row = QHBoxLayout()
        sort_row.setSpacing(8)
        sort_lbl = self._field_label("Order:")
        sort_row.addWidget(sort_lbl)
        self._sort_combo = QComboBox()
        self._sort_combo.setObjectName("sortCombo")
        self._sort_combo.addItems(["Custom Order", "A to Z", "Z to A"])
        self._sort_combo.currentIndexChanged.connect(self._apply_sort)
        sort_row.addWidget(self._sort_combo)
        sort_row.addStretch()
        layout.addLayout(sort_row)

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
        self._up_btn = self._secondary_btn("Up", SP.SP_ArrowUp)
        self._up_btn.setFixedWidth(96)
        self._up_btn.clicked.connect(self._move_up)
        self._dn_btn = self._secondary_btn("Down", SP.SP_ArrowDown)
        self._dn_btn.setFixedWidth(96)
        self._dn_btn.clicked.connect(self._move_down)
        reorder_col.addWidget(self._up_btn)
        reorder_col.addWidget(self._dn_btn)
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
        self._protect_input.setPlaceholderText("Select a PDF with Browse...")
        self._protect_input.setReadOnly(True)
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
        self._protect_output.setReadOnly(True)
        self._protect_output.setPlaceholderText("Output filename (auto-filled on browse)...")
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
        self._peep_input.setPlaceholderText("Select a PDF with Browse...")
        self._peep_input.setReadOnly(True)
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

    # -- View PDF tab ──────────────────────────────────────────────────────────

    def _build_viewer_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        self._viewer = PDFViewerWidget(tab)
        self._viewer.annotate_requested.connect(self._open_annotate_dialog)
        layout.addWidget(self._viewer)
        return tab

    def _open_annotate_dialog(self, pdf_path: str) -> None:
        if not pdf_path:
            return
        dlg = _AnnotateDialog(
            parent    = self,
            input_path = pdf_path,
            profiles  = self.annotation_profiles,
            annotator = self.annotator,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.output_path:
            self.history.add_annotate(dlg.output_path)
            self._refresh_history()
            reply = QMessageBox.question(
                self,
                "Annotation Complete",
                f"Saved as: {os.path.basename(dlg.output_path)}\n\nOpen in viewer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._viewer.load_pdf(dlg.output_path)

    # -- Compress PDF tab ──────────────────────────────────────────────────────

    def _build_compress_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        desc = QLabel("Reduce the file size of any PDF.")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)
        layout.addSpacing(8)

        # Input
        layout.addWidget(self._field_label("Select PDF:"))
        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self._compress_input = QLineEdit()
        self._compress_input.setObjectName("inputField")
        self._compress_input.setPlaceholderText("Select a PDF with Browse...")
        self._compress_input.setReadOnly(True)
        in_row.addWidget(self._compress_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_compress_input)
        in_row.addWidget(b_in)
        layout.addLayout(in_row)

        # Output
        layout.addWidget(self._field_label("Save Compressed PDF As:"))
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self._compress_output = QLineEdit()
        self._compress_output.setObjectName("inputField")
        self._compress_output.setReadOnly(True)
        self._compress_output.setPlaceholderText("Output filename (auto-filled on browse)...")
        out_row.addWidget(self._compress_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_compress_output)
        out_row.addWidget(b_out)
        layout.addLayout(out_row)

        # Compression level radio buttons
        layout.addSpacing(6)
        layout.addWidget(self._field_label("Compression Level:"))

        self._compress_level_group = QButtonGroup(self)
        self._compress_desc_lbl    = QLabel(LEVEL_DESCRIPTIONS[LEVEL_MEDIUM])
        self._compress_desc_lbl.setObjectName("cautionLabel")
        self._compress_desc_lbl.setWordWrap(True)

        radio_data = [
            (LEVEL_LIGHT,  "Light  -- lossless, 10-30% reduction"),
            (LEVEL_MEDIUM, "Medium  -- lossless, 20-50% reduction  (recommended)"),
            (LEVEL_HIGH,   "High  -- images compressed, 40-80% reduction"),
        ]
        for level, label_text in radio_data:
            rb = QRadioButton(label_text)
            rb.setChecked(level == LEVEL_MEDIUM)
            rb.setObjectName("radioBtn")
            rb.toggled.connect(
                lambda checked, lv=level: (
                    self._compress_desc_lbl.setText(LEVEL_DESCRIPTIONS[lv])
                    if checked else None
                )
            )
            self._compress_level_group.addButton(rb, level)
            layout.addWidget(rb)

        layout.addWidget(self._compress_desc_lbl)

        # Progress + status
        layout.addSpacing(4)
        self._compress_progress = self._make_progress()
        layout.addWidget(self._compress_progress)

        self._compress_status = QLabel("")
        self._compress_status.setObjectName("statusLabel")
        layout.addWidget(self._compress_status)

        layout.addStretch()

        self._compress_btn = self._primary_btn("Compress PDF")
        self._compress_btn.setFixedHeight(52)
        self._compress_btn.clicked.connect(self._do_compress)
        layout.addWidget(self._compress_btn)

        return tab

    # -- Compress callbacks ────────────────────────────────────────────────────

    def _browse_compress_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF to Compress", "", "PDF Files (*.pdf)"
        )
        if path:
            self._compress_input_path = path
            self._compress_input.setText(os.path.basename(path))
            self._compress_input.setToolTip(path)
            if not self._compress_output_path:
                stem = path[:-4] if path.lower().endswith(".pdf") else path
                self._compress_output_path = stem + "_compressed.pdf"
                self._compress_output.setText(os.path.basename(self._compress_output_path))
                self._compress_output.setToolTip(self._compress_output_path)

    def _browse_compress_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._compress_output_path = path
            self._compress_output.setText(os.path.basename(path))
            self._compress_output.setToolTip(path)

    def _do_compress(self):
        input_path  = self._compress_input_path
        output_path = self._compress_output_path
        level       = self._compress_level_group.checkedId()

        def err(msg):
            self._compress_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._compress_status.setText(msg)

        if not input_path or not os.path.isfile(input_path):
            return err("Please select a valid PDF file.")
        if not output_path:
            return err("Please set an output file path.")
        if level == -1:
            return err("Please select a compression level.")

        if not self._check_output_dir(output_path):
            return

        if (os.path.realpath(output_path) != os.path.realpath(input_path)
                and os.path.exists(output_path)):
            reply = QMessageBox.question(
                self, "File Already Exists",
                f"'{os.path.basename(output_path)}' already exists.\nOverwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if level == LEVEL_HIGH:
            reply = QMessageBox.warning(
                self, "Lossy Compression",
                "Level 3 (High) compression converts each page into a JPEG image.\n\n"
                "Text will no longer be selectable or searchable, and visual quality "
                "may be reduced.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._compress_btn.setEnabled(False)
        self._compress_progress.setValue(0)
        self._compress_status.setStyleSheet("")
        self._compress_status.setText("Compressing...")

        self._compress_worker = _CompressWorker(
            self.compressor, input_path, output_path, level
        )
        self._compress_worker.progress_changed.connect(
            self._compress_progress.setValue
        )
        self._compress_worker.compress_done.connect(
            lambda ok, msg: self._compress_done(ok, msg, output_path, level)
        )
        self._compress_worker.finished.connect(self._compress_worker.deleteLater)
        self._compress_worker.start()

    def _compress_done(self, success: bool, message: str, output_path: str, level: int):
        self._compress_btn.setEnabled(True)
        self._compress_progress.setValue(100 if success else 0)
        if success:
            self._compress_status.setStyleSheet(
                f"color: {self.theme.get_color('success')};"
            )
            self._compress_status.setText(
                f"Saved: {os.path.basename(output_path)}"
            )
            self.history.add_compress(output_path, LEVEL_LABELS[level])
            QMessageBox.information(self, "Compressed", message)
            self._ask_open_in_viewer(output_path)
        else:
            self._compress_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._compress_status.setText("Compression failed.")
            QMessageBox.critical(self, "Error", message)

    # -- Split PDF tab ─────────────────────────────────────────────────────────

    def _build_split_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        desc = QLabel(
            "Split a PDF into multiple files by individual pages, custom page ranges, "
            "or fixed-size chunks."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Input
        layout.addWidget(self._field_label("Select PDF:"))
        in_row = QHBoxLayout(); in_row.setSpacing(8)
        self._split_input = QLineEdit()
        self._split_input.setObjectName("inputField")
        self._split_input.setPlaceholderText("Select a PDF with Browse...")
        self._split_input.setReadOnly(True)
        in_row.addWidget(self._split_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_split_input)
        in_row.addWidget(b_in)
        layout.addLayout(in_row)

        # Output folder
        layout.addWidget(self._field_label("Output Folder:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._split_output = QLineEdit()
        self._split_output.setObjectName("inputField")
        self._split_output.setPlaceholderText("Choose destination folder...")
        self._split_output.setReadOnly(True)
        out_row.addWidget(self._split_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_split_output)
        out_row.addWidget(b_out)
        layout.addLayout(out_row)

        # Mode
        layout.addSpacing(4)
        layout.addWidget(self._field_label("Split Mode:"))
        self._split_mode_group = QButtonGroup(self)

        rb_all = QRadioButton("Every page  (one PDF per page)")
        rb_all.setChecked(True)
        rb_all.setObjectName("radioBtn")
        self._split_mode_group.addButton(rb_all, 0)
        layout.addWidget(rb_all)

        rb_ranges = QRadioButton("Custom ranges  (e.g. 1-3, 4-7, 8)")
        rb_ranges.setObjectName("radioBtn")
        self._split_mode_group.addButton(rb_ranges, 1)
        layout.addWidget(rb_ranges)

        self._split_ranges_edit = QLineEdit()
        self._split_ranges_edit.setObjectName("inputField")
        self._split_ranges_edit.setPlaceholderText("e.g.  1-3, 4-7, 8")
        self._split_ranges_edit.setEnabled(False)
        layout.addWidget(self._split_ranges_edit)

        rb_every = QRadioButton("Every N pages")
        rb_every.setObjectName("radioBtn")
        self._split_mode_group.addButton(rb_every, 2)
        layout.addWidget(rb_every)

        every_row = QHBoxLayout(); every_row.setSpacing(8)
        every_row.addWidget(QLabel("Pages per chunk:"))
        self._split_every_spin = QSpinBox()
        self._split_every_spin.setObjectName("spinBox")
        self._split_every_spin.setRange(1, 9999)
        self._split_every_spin.setValue(2)
        self._split_every_spin.setFixedWidth(80)
        self._split_every_spin.setEnabled(False)
        every_row.addWidget(self._split_every_spin)
        every_row.addStretch()
        layout.addLayout(every_row)

        def _update_split_mode():
            mid = self._split_mode_group.checkedId()
            self._split_ranges_edit.setEnabled(mid == 1)
            self._split_every_spin.setEnabled(mid == 2)

        rb_ranges.toggled.connect(lambda _: _update_split_mode())
        rb_every.toggled.connect(lambda _: _update_split_mode())
        rb_all.toggled.connect(lambda _: _update_split_mode())

        # Progress + status
        layout.addSpacing(4)
        self._split_progress = self._make_progress()
        layout.addWidget(self._split_progress)
        self._split_status = QLabel("")
        self._split_status.setObjectName("statusLabel")
        layout.addWidget(self._split_status)

        layout.addStretch()

        self._split_btn = self._primary_btn("Split PDF")
        self._split_btn.setFixedHeight(52)
        self._split_btn.clicked.connect(self._do_split)
        layout.addWidget(self._split_btn)

        return tab

    def _browse_split_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF to Split", "", "PDF Files (*.pdf)"
        )
        if path:
            self._split_input_path = path
            self._split_input.setText(os.path.basename(path))
            self._split_input.setToolTip(path)
            if not self._split_output_dir:
                default_dir = os.path.join(
                    os.path.dirname(path),
                    os.path.splitext(os.path.basename(path))[0] + "_split",
                )
                self._split_output_dir = default_dir
                self._split_output.setText(os.path.basename(default_dir))
                self._split_output.setToolTip(default_dir)

    def _browse_split_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._split_output_dir = d
            self._split_output.setText(os.path.basename(d))
            self._split_output.setToolTip(d)

    def _do_split(self):
        def err(msg):
            self._split_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._split_status.setText(msg)

        if not self._split_input_path or not os.path.isfile(self._split_input_path):
            return err("Please select a valid PDF file.")
        if not self._split_output_dir:
            return err("Please select an output folder.")
        if not self._check_output_folder(self._split_output_dir):
            return

        mid = self._split_mode_group.checkedId()
        if mid == 0:
            mode, ranges_str, every_n = "all", "", 1
        elif mid == 1:
            mode = "ranges"
            ranges_str = self._split_ranges_edit.text().strip()
            every_n = 1
            if not ranges_str:
                return err("Please enter at least one page range.")
        else:
            mode = "every_n"
            ranges_str = ""
            every_n = self._split_every_spin.value()

        self._split_btn.setEnabled(False)
        self._split_progress.setValue(0)
        self._split_status.setStyleSheet("")
        self._split_status.setText("Splitting...")

        self._split_worker = _SplitWorker(
            self.splitter, self._split_input_path, self._split_output_dir,
            mode, ranges_str, every_n,
        )
        self._split_worker.progress_changed.connect(self._split_progress.setValue)
        self._split_worker.split_done.connect(
            lambda ok, msg: self._split_done(ok, msg)
        )
        self._split_worker.finished.connect(self._split_worker.deleteLater)
        self._split_worker.start()

    def _split_done(self, success: bool, message: str):
        self._split_btn.setEnabled(True)
        self._split_progress.setValue(100 if success else 0)
        if success:
            self._split_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self._split_status.setText(message)
            self.history.add_split(self._split_output_dir, 0)
            QMessageBox.information(self, "Split Complete", message)
            self._ask_reveal_folder(self._split_output_dir)
        else:
            self._split_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._split_status.setText("Split failed.")
            QMessageBox.critical(self, "Error", message)

    # -- PDF to Word tab ───────────────────────────────────────────────────────

    def _build_pdf_to_word_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        desc = QLabel(
            "Convert a PDF to an editable Word document (.docx). "
            "Requires the pdf2docx library (pip install pdf2docx)."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(self._field_label("Select PDF:"))
        in_row = QHBoxLayout(); in_row.setSpacing(8)
        self._p2w_input = QLineEdit()
        self._p2w_input.setObjectName("inputField")
        self._p2w_input.setPlaceholderText("Select a PDF with Browse...")
        self._p2w_input.setReadOnly(True)
        in_row.addWidget(self._p2w_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_p2w_input)
        in_row.addWidget(b_in)
        layout.addLayout(in_row)

        layout.addWidget(self._field_label("Save Word Document As:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._p2w_output = QLineEdit()
        self._p2w_output.setObjectName("inputField")
        self._p2w_output.setPlaceholderText("Output filename (auto-filled on browse)...")
        self._p2w_output.setReadOnly(True)
        out_row.addWidget(self._p2w_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_p2w_output)
        out_row.addWidget(b_out)
        layout.addLayout(out_row)

        self._p2w_progress = self._make_progress()
        layout.addWidget(self._p2w_progress)
        self._p2w_status = QLabel("")
        self._p2w_status.setObjectName("statusLabel")
        layout.addWidget(self._p2w_status)

        layout.addStretch()

        self._p2w_btn = self._primary_btn("Convert to Word")
        self._p2w_btn.setFixedHeight(52)
        self._p2w_btn.clicked.connect(self._do_p2w)
        layout.addWidget(self._p2w_btn)

        return tab

    def _browse_p2w_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._p2w_input_path = path
            self._p2w_input.setText(os.path.basename(path))
            self._p2w_input.setToolTip(path)
            if not self._p2w_output_path:
                self._p2w_output_path = os.path.splitext(path)[0] + ".docx"
                self._p2w_output.setText(os.path.basename(self._p2w_output_path))
                self._p2w_output.setToolTip(self._p2w_output_path)

    def _browse_p2w_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Word Document As", "", "Word Documents (*.docx)"
        )
        if path:
            self._p2w_output_path = path
            self._p2w_output.setText(os.path.basename(path))
            self._p2w_output.setToolTip(path)

    def _do_p2w(self):
        def err(msg):
            self._p2w_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._p2w_status.setText(msg)

        if not self._p2w_input_path or not os.path.isfile(self._p2w_input_path):
            return err("Please select a valid PDF file.")
        if not self._p2w_output_path:
            return err("Please set an output file path.")
        if not self._check_output_dir(self._p2w_output_path):
            return

        self._p2w_btn.setEnabled(False)
        self._p2w_progress.setValue(0)
        self._p2w_status.setStyleSheet("")
        self._p2w_status.setText("Converting...")

        self._p2w_worker = _PdfToWordWorker(
            self.pdf_to_word, self._p2w_input_path, self._p2w_output_path
        )
        self._p2w_worker.progress_changed.connect(self._p2w_progress.setValue)
        self._p2w_worker.convert_done.connect(
            lambda ok, msg: self._p2w_done(ok, msg)
        )
        self._p2w_worker.finished.connect(self._p2w_worker.deleteLater)
        self._p2w_worker.start()

    def _p2w_done(self, success: bool, message: str):
        self._p2w_btn.setEnabled(True)
        self._p2w_progress.setValue(100 if success else 0)
        if success:
            self._p2w_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self._p2w_status.setText(message)
            self.history.add_pdf_to_word(self._p2w_output_path)
            QMessageBox.information(self, "Conversion Complete", message)
            self._ask_reveal_folder(self._p2w_output_path)
        else:
            self._p2w_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._p2w_status.setText("Conversion failed.")
            QMessageBox.critical(self, "Error", message)

    # -- Word to PDF tab ───────────────────────────────────────────────────────

    def _build_word_to_pdf_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        desc = QLabel(
            "Convert a Word document (.docx / .doc) to PDF. "
            "Requires Microsoft Word or LibreOffice to be installed."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(self._field_label("Select Word Document:"))
        in_row = QHBoxLayout(); in_row.setSpacing(8)
        self._w2p_input = QLineEdit()
        self._w2p_input.setObjectName("inputField")
        self._w2p_input.setPlaceholderText("Select a .docx file with Browse...")
        self._w2p_input.setReadOnly(True)
        in_row.addWidget(self._w2p_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_w2p_input)
        in_row.addWidget(b_in)
        layout.addLayout(in_row)

        layout.addWidget(self._field_label("Save PDF As:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._w2p_output = QLineEdit()
        self._w2p_output.setObjectName("inputField")
        self._w2p_output.setPlaceholderText("Output filename (auto-filled on browse)...")
        self._w2p_output.setReadOnly(True)
        out_row.addWidget(self._w2p_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_w2p_output)
        out_row.addWidget(b_out)
        layout.addLayout(out_row)

        self._w2p_progress = self._make_progress()
        layout.addWidget(self._w2p_progress)
        self._w2p_status = QLabel("")
        self._w2p_status.setObjectName("statusLabel")
        layout.addWidget(self._w2p_status)

        layout.addStretch()

        self._w2p_btn = self._primary_btn("Convert to PDF")
        self._w2p_btn.setFixedHeight(52)
        self._w2p_btn.clicked.connect(self._do_w2p)
        layout.addWidget(self._w2p_btn)

        return tab

    def _browse_w2p_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Word Document", "",
            "Word Documents (*.docx *.doc)"
        )
        if path:
            self._w2p_input_path = path
            self._w2p_input.setText(os.path.basename(path))
            self._w2p_input.setToolTip(path)
            if not self._w2p_output_path:
                self._w2p_output_path = os.path.splitext(path)[0] + ".pdf"
                self._w2p_output.setText(os.path.basename(self._w2p_output_path))
                self._w2p_output.setToolTip(self._w2p_output_path)

    def _browse_w2p_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._w2p_output_path = path
            self._w2p_output.setText(os.path.basename(path))
            self._w2p_output.setToolTip(path)

    def _do_w2p(self):
        def err(msg):
            self._w2p_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._w2p_status.setText(msg)

        if not self._w2p_input_path or not os.path.isfile(self._w2p_input_path):
            return err("Please select a valid Word document.")
        if not self._w2p_output_path:
            return err("Please set an output file path.")
        if not self._check_output_dir(self._w2p_output_path):
            return

        self._w2p_btn.setEnabled(False)
        self._w2p_progress.setValue(0)
        self._w2p_status.setStyleSheet("")
        self._w2p_status.setText("Converting...")

        self._w2p_worker = _WordToPdfWorker(
            self.word_to_pdf, self._w2p_input_path, self._w2p_output_path
        )
        self._w2p_worker.progress_changed.connect(self._w2p_progress.setValue)
        self._w2p_worker.convert_done.connect(
            lambda ok, msg: self._w2p_done(ok, msg)
        )
        self._w2p_worker.finished.connect(self._w2p_worker.deleteLater)
        self._w2p_worker.start()

    def _w2p_done(self, success: bool, message: str):
        self._w2p_btn.setEnabled(True)
        self._w2p_progress.setValue(100 if success else 0)
        if success:
            self._w2p_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self._w2p_status.setText(message)
            self.history.add_word_to_pdf(self._w2p_output_path)
            QMessageBox.information(self, "Conversion Complete", message)
            self._ask_open_in_viewer(self._w2p_output_path)
        else:
            self._w2p_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._w2p_status.setText("Conversion failed.")
            QMessageBox.critical(self, "Error", message)

    # -- PDF to Image tab ──────────────────────────────────────────────────────

    def _build_pdf_to_img_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        desc = QLabel(
            "Export PDF pages as image files (PNG, JPEG, or TIFF). "
            "Leave pages blank to export all pages."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(self._field_label("Select PDF:"))
        in_row = QHBoxLayout(); in_row.setSpacing(8)
        self._p2i_input = QLineEdit()
        self._p2i_input.setObjectName("inputField")
        self._p2i_input.setPlaceholderText("Select a PDF with Browse...")
        self._p2i_input.setReadOnly(True)
        in_row.addWidget(self._p2i_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_p2i_input)
        in_row.addWidget(b_in)
        layout.addLayout(in_row)

        layout.addWidget(self._field_label("Output Folder:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._p2i_output = QLineEdit()
        self._p2i_output.setObjectName("inputField")
        self._p2i_output.setPlaceholderText("Choose destination folder...")
        self._p2i_output.setReadOnly(True)
        out_row.addWidget(self._p2i_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_p2i_output)
        out_row.addWidget(b_out)
        layout.addLayout(out_row)

        # Options row: format + DPI + pages
        opts = QHBoxLayout(); opts.setSpacing(20)

        fmt_col = QVBoxLayout(); fmt_col.setSpacing(4)
        fmt_col.addWidget(self._field_label("Format:"))
        self._p2i_fmt = QComboBox()
        self._p2i_fmt.setObjectName("comboBox")
        for fmt in ("PNG", "JPEG", "TIFF"):
            self._p2i_fmt.addItem(fmt)
        fmt_col.addWidget(self._p2i_fmt)
        opts.addLayout(fmt_col)

        dpi_col = QVBoxLayout(); dpi_col.setSpacing(4)
        dpi_col.addWidget(self._field_label("DPI:"))
        self._p2i_dpi = QSpinBox()
        self._p2i_dpi.setObjectName("spinBox")
        self._p2i_dpi.setRange(72, 600)
        self._p2i_dpi.setValue(150)
        self._p2i_dpi.setFixedWidth(90)
        dpi_col.addWidget(self._p2i_dpi)
        opts.addLayout(dpi_col)

        pg_col = QVBoxLayout(); pg_col.setSpacing(4)
        pg_col.addWidget(self._field_label("Pages (blank = all):"))
        self._p2i_pages = QLineEdit()
        self._p2i_pages.setObjectName("inputField")
        self._p2i_pages.setPlaceholderText("e.g.  1, 3, 5-7")
        pg_col.addWidget(self._p2i_pages)
        opts.addLayout(pg_col, 1)

        layout.addLayout(opts)

        self._p2i_progress = self._make_progress()
        layout.addWidget(self._p2i_progress)
        self._p2i_status = QLabel("")
        self._p2i_status.setObjectName("statusLabel")
        layout.addWidget(self._p2i_status)

        layout.addStretch()

        self._p2i_btn = self._primary_btn("Export Images")
        self._p2i_btn.setFixedHeight(52)
        self._p2i_btn.clicked.connect(self._do_p2i)
        layout.addWidget(self._p2i_btn)

        return tab

    def _browse_p2i_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._p2i_input_path = path
            self._p2i_input.setText(os.path.basename(path))
            self._p2i_input.setToolTip(path)
            if not self._p2i_output_dir:
                default_dir = os.path.join(
                    os.path.dirname(path),
                    os.path.splitext(os.path.basename(path))[0] + "_images",
                )
                self._p2i_output_dir = default_dir
                self._p2i_output.setText(os.path.basename(default_dir))
                self._p2i_output.setToolTip(default_dir)

    def _browse_p2i_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._p2i_output_dir = d
            self._p2i_output.setText(os.path.basename(d))
            self._p2i_output.setToolTip(d)

    def _do_p2i(self):
        def err(msg):
            self._p2i_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._p2i_status.setText(msg)

        if not self._p2i_input_path or not os.path.isfile(self._p2i_input_path):
            return err("Please select a valid PDF file.")
        if not self._p2i_output_dir:
            return err("Please select an output folder.")
        if not self._check_output_folder(self._p2i_output_dir):
            return

        self._p2i_btn.setEnabled(False)
        self._p2i_progress.setValue(0)
        self._p2i_status.setStyleSheet("")
        self._p2i_status.setText("Exporting images...")

        self._p2i_worker = _PdfToImagesWorker(
            self.pdf_to_images,
            self._p2i_input_path,
            self._p2i_output_dir,
            self._p2i_fmt.currentText(),
            self._p2i_dpi.value(),
            self._p2i_pages.text().strip(),
        )
        self._p2i_worker.progress_changed.connect(self._p2i_progress.setValue)
        self._p2i_worker.convert_done.connect(
            lambda ok, msg: self._p2i_done(ok, msg)
        )
        self._p2i_worker.finished.connect(self._p2i_worker.deleteLater)
        self._p2i_worker.start()

    def _p2i_done(self, success: bool, message: str):
        self._p2i_btn.setEnabled(True)
        self._p2i_progress.setValue(100 if success else 0)
        if success:
            self._p2i_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self._p2i_status.setText(message)
            self.history.add_pdf_to_images(self._p2i_output_dir, 0)
            QMessageBox.information(self, "Export Complete", message)
            self._ask_reveal_folder(self._p2i_output_dir)
        else:
            self._p2i_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._p2i_status.setText("Export failed.")
            QMessageBox.critical(self, "Error", message)

    # -- Image to PDF tab ──────────────────────────────────────────────────────

    def _build_img_to_pdf_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        # Left: file list + controls
        left = QVBoxLayout()
        left.setSpacing(8)
        outer.addLayout(left, 1)

        desc = QLabel(
            "Combine images (PNG, JPEG, TIFF, BMP, GIF) into a single PDF. "
            "Use the Up / Down buttons to set the page order."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        left.addWidget(desc)

        left.addWidget(self._field_label("Images:"))
        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        for label, slot, icon_sp in [
            ("Add Images...",  self._add_i2p_images,  SP.SP_FileIcon),
            ("Add Folder",     self._add_i2p_folder,  SP.SP_DirOpenIcon),
            ("Remove",         self._remove_i2p,      SP.SP_DialogDiscardButton),
            ("Clear All",      self._clear_i2p_images, SP.SP_DialogResetButton),
        ]:
            b = self._secondary_btn(label, icon_sp)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        btn_row.addStretch()
        left.addLayout(btn_row)

        # List + move buttons side by side
        list_row = QHBoxLayout(); list_row.setSpacing(6)
        self._i2p_list = QTreeWidget()
        self._i2p_list.setObjectName("historyList")
        self._i2p_list.setColumnCount(2)
        self._i2p_list.setHeaderLabels(["Image File", "Folder"])
        self._i2p_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._i2p_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._i2p_list.setRootIsDecorated(False)
        self._i2p_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        list_row.addWidget(self._i2p_list, 1)

        move_col = QVBoxLayout(); move_col.setSpacing(4)
        self._i2p_up_btn   = self._secondary_btn("Up",   SP.SP_ArrowUp)
        self._i2p_down_btn = self._secondary_btn("Down", SP.SP_ArrowDown)
        self._i2p_up_btn.setFixedWidth(68)
        self._i2p_down_btn.setFixedWidth(68)
        self._i2p_up_btn.clicked.connect(self._move_i2p_up)
        self._i2p_down_btn.clicked.connect(self._move_i2p_down)
        move_col.addStretch()
        move_col.addWidget(self._i2p_up_btn)
        move_col.addWidget(self._i2p_down_btn)
        move_col.addStretch()
        list_row.addLayout(move_col)
        left.addLayout(list_row)

        count_lbl = QLabel("0 image(s)")
        count_lbl.setObjectName("hintLabel")
        self._i2p_count_lbl = count_lbl
        left.addWidget(count_lbl)

        left.addWidget(self._field_label("Save PDF As:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._i2p_output = QLineEdit()
        self._i2p_output.setObjectName("inputField")
        self._i2p_output.setPlaceholderText("Choose output file...")
        self._i2p_output.setReadOnly(True)
        out_row.addWidget(self._i2p_output)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_i2p_output)
        out_row.addWidget(b_out)
        left.addLayout(out_row)

        self._i2p_progress = self._make_progress()
        left.addWidget(self._i2p_progress)
        self._i2p_status = QLabel("")
        self._i2p_status.setObjectName("statusLabel")
        left.addWidget(self._i2p_status)

        left.addStretch()

        self._i2p_btn = self._primary_btn("Convert to PDF")
        self._i2p_btn.setFixedHeight(52)
        self._i2p_btn.clicked.connect(self._do_i2p)
        left.addWidget(self._i2p_btn)

        return tab

    # -- Image-to-PDF list helpers ─────────────────────────────────────────────

    def _i2p_refresh_list(self) -> None:
        self._i2p_list.clear()
        for p in self._i2p_image_paths:
            item = QTreeWidgetItem([
                os.path.basename(p),
                os.path.basename(os.path.dirname(p)),
            ])
            self._i2p_list.addTopLevelItem(item)
        n = len(self._i2p_image_paths)
        self._i2p_count_lbl.setText(f"{n} image(s)")

    def _add_i2p_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif)"
        )
        if paths:
            self._i2p_image_paths.extend(paths)
            self._i2p_refresh_list()

    def _add_i2p_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Images")
        if not folder:
            return
        _EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}
        added = 0
        for fname in sorted(os.listdir(folder)):
            if os.path.splitext(fname)[1].lower() in _EXTS:
                self._i2p_image_paths.append(os.path.join(folder, fname))
                added += 1
        if added:
            self._i2p_refresh_list()
        else:
            QMessageBox.information(self, "No Images Found",
                                    "No supported image files were found in that folder.")

    def _remove_i2p(self):
        row = self._i2p_list.currentIndex().row()
        if 0 <= row < len(self._i2p_image_paths):
            del self._i2p_image_paths[row]
            self._i2p_refresh_list()

    def _clear_i2p_images(self):
        self._i2p_image_paths = []
        self._i2p_list.clear()
        self._i2p_count_lbl.setText("0 image(s)")

    def _move_i2p_up(self):
        row = self._i2p_list.currentIndex().row()
        if row > 0:
            self._i2p_image_paths[row - 1], self._i2p_image_paths[row] = (
                self._i2p_image_paths[row], self._i2p_image_paths[row - 1]
            )
            self._i2p_refresh_list()
            self._i2p_list.setCurrentItem(self._i2p_list.topLevelItem(row - 1))

    def _move_i2p_down(self):
        row = self._i2p_list.currentIndex().row()
        if 0 <= row < len(self._i2p_image_paths) - 1:
            self._i2p_image_paths[row], self._i2p_image_paths[row + 1] = (
                self._i2p_image_paths[row + 1], self._i2p_image_paths[row]
            )
            self._i2p_refresh_list()
            self._i2p_list.setCurrentItem(self._i2p_list.topLevelItem(row + 1))

    def _browse_i2p_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._i2p_output_path = path
            self._i2p_output.setText(os.path.basename(path))
            self._i2p_output.setToolTip(path)

    def _do_i2p(self):
        def err(msg):
            self._i2p_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._i2p_status.setText(msg)

        if not self._i2p_image_paths:
            return err("Please add at least one image.")
        if not self._i2p_output_path:
            return err("Please set an output file path.")
        if not self._check_output_dir(self._i2p_output_path):
            return

        self._i2p_btn.setEnabled(False)
        self._i2p_progress.setValue(0)
        self._i2p_status.setStyleSheet("")
        self._i2p_status.setText("Converting...")

        self._i2p_worker = _ImagesToPdfWorker(
            self.images_to_pdf, list(self._i2p_image_paths), self._i2p_output_path
        )
        self._i2p_worker.progress_changed.connect(self._i2p_progress.setValue)
        self._i2p_worker.convert_done.connect(
            lambda ok, msg: self._i2p_done(ok, msg)
        )
        self._i2p_worker.finished.connect(self._i2p_worker.deleteLater)
        self._i2p_worker.start()

    def _i2p_done(self, success: bool, message: str):
        self._i2p_btn.setEnabled(True)
        self._i2p_progress.setValue(100 if success else 0)
        if success:
            self._i2p_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self._i2p_status.setText(message)
            self.history.add_images_to_pdf(self._i2p_output_path, len(self._i2p_image_paths))
            QMessageBox.information(self, "Conversion Complete", message)
            self._ask_open_in_viewer(self._i2p_output_path)
        else:
            self._i2p_status.setStyleSheet(f"color: {self.theme.get_color('error')};")
            self._i2p_status.setText("Conversion failed.")
            QMessageBox.critical(self, "Error", message)

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
        outer   = QWidget()
        outer.setObjectName("tabPage")
        vlayout = QVBoxLayout(outer)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        # Transfer license button at the top of the Help tab
        if self._license_mgr:
            bar = QWidget()
            bar.setObjectName("tabPage")
            bar_row = QHBoxLayout(bar)
            bar_row.setContentsMargins(16, 10, 16, 4)
            bar_row.addStretch()
            transfer_btn = QPushButton("Transfer License to New Device")
            transfer_btn.setObjectName("secondaryBtn")
            transfer_btn.clicked.connect(self._open_transfer_dialog)
            bar_row.addWidget(transfer_btn)
            vlayout.addWidget(bar)

        vlayout.addWidget(build_faq_widget(self))
        return outer

    def _open_transfer_dialog(self):
        from .transfer_dialog import TransferDialog
        dlg = TransferDialog(self._license_mgr, parent=self)
        dlg.exec()

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

    # -- Post-operation helpers ────────────────────────────────────────────────

    def _open_in_viewer(self, pdf_path: str) -> None:
        """Load pdf_path into the built-in viewer and switch to it."""
        self._viewer.load_pdf(pdf_path)
        self.tabs.setCurrentIndex(3)   # View PDF is always tab 3

    def _reveal_in_explorer(self, path: str) -> None:
        """Highlight path in the OS file manager (non-blocking)."""
        import platform as _plt
        import subprocess
        try:
            if _plt.system() == "Darwin":
                subprocess.Popen(["open", "-R", path])
            elif _plt.system() == "Windows":
                subprocess.Popen(["explorer", "/select,", path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception:
            pass

    def _ask_open_in_viewer(self, pdf_path: str, title: str = "Open in Viewer?") -> None:
        """Offer to open pdf_path in the built-in viewer."""
        reply = QMessageBox.question(
            self, title,
            f"Open  {os.path.basename(pdf_path)}  in the built-in viewer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._open_in_viewer(pdf_path)

    def _ask_reveal_folder(self, folder_path: str) -> None:
        """Offer to reveal the output folder in the OS file manager."""
        reply = QMessageBox.question(
            self, "Reveal Output Folder?",
            "Open the output folder in your file manager?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._reveal_in_explorer(folder_path)

    def _check_output_dir(self, path: str) -> bool:
        """Return True if the directory for path exists and is writable.

        Shows an error dialog and returns False otherwise.
        Output-directory validation prevents cryptic OS errors deep inside
        worker threads when the destination folder was deleted or is read-only.
        """
        out_dir = os.path.dirname(os.path.abspath(path)) if path else ""
        if not out_dir:
            QMessageBox.critical(self, "Invalid Output", "No output path specified.")
            return False
        if not os.path.isdir(out_dir):
            QMessageBox.critical(
                self, "Output Folder Not Found",
                f"The destination folder does not exist:\n{out_dir}\n\n"
                "Please choose a different output path.",
            )
            return False
        if not os.access(out_dir, os.W_OK):
            QMessageBox.critical(
                self, "Output Folder Not Writable",
                f"No write permission for:\n{out_dir}\n\n"
                "Please choose a different output path.",
            )
            return False
        return True

    def _check_output_folder(self, folder: str) -> bool:
        """Like _check_output_dir but for when the output IS a directory."""
        if not folder:
            QMessageBox.critical(self, "Invalid Output", "No output folder specified.")
            return False
        # The folder may not exist yet (will be created by the engine).
        # Validate the parent instead.
        parent = os.path.dirname(os.path.abspath(folder))
        if not os.path.isdir(parent):
            QMessageBox.critical(
                self, "Output Folder Not Found",
                f"The parent directory does not exist:\n{parent}\n\n"
                "Please choose a different output folder.",
            )
            return False
        if not os.access(parent, os.W_OK):
            QMessageBox.critical(
                self, "Output Folder Not Writable",
                f"No write permission for:\n{parent}\n\n"
                "Please choose a different output folder.",
            )
            return False
        return True

    # -- Stylesheet / theme ────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(
            build_stylesheet(self.theme.colors, self.theme.get_font("font_family"))
        )

    def _check_theme_change(self):
        """Detect OS dark/light mode changes and re-apply the stylesheet."""
        is_dark = PlatformInfo.is_dark_mode()
        if is_dark != self.theme.is_dark:
            self.theme.is_dark    = is_dark
            self.theme.theme_name = "dark" if is_dark else "light"
            self.theme.colors     = self.theme._get_theme()
            self._apply_stylesheet()

    # -- Merge callbacks ───────────────────────────────────────────────────────

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if not paths:
            return
        count = self.merger.add_files(paths)
        skipped = len(paths) - count
        self._refresh_file_tree()
        if skipped:
            self._set_status(
                f"Added {count} file(s). {skipped} skipped (not a valid PDF or duplicate).",
                error=skipped > 0 and count == 0,
            )
        else:
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
        all_items = [
            self.file_tree.topLevelItem(i)
            for i in range(self.file_tree.topLevelItemCount())
        ]
        # Prefer checked items; fall back to click-selection
        indices = [
            i for i, it in enumerate(all_items)
            if it.checkState(0) == Qt.CheckState.Checked
        ]
        if not indices:
            indices = [all_items.index(it) for it in self.file_tree.selectedItems()]
        if not indices:
            return
        for idx in sorted(indices, reverse=True):
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
        self._sort_combo.blockSignals(True)
        self._sort_combo.setCurrentIndex(0)
        self._sort_combo.blockSignals(False)
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
        self._sort_combo.blockSignals(True)
        self._sort_combo.setCurrentIndex(0)
        self._sort_combo.blockSignals(False)
        self._refresh_file_tree(restore_selection=new_sel)

    def _apply_sort(self, index: int):
        if index == 0:
            return  # Custom — no automatic reorder
        reverse = (index == 2)
        self.merger.pdf_files.sort(
            key=lambda p: os.path.basename(p).lower(), reverse=reverse
        )
        self._refresh_file_tree()

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
            self._protect_input_path = path
            self._protect_input.setText(os.path.basename(path))
            self._protect_input.setToolTip(path)
            if not self._protect_output_path:
                stem = path[:-4] if path.lower().endswith(".pdf") else path
                self._protect_output_path = stem + "_protected.pdf"
                self._protect_output.setText(os.path.basename(self._protect_output_path))
                self._protect_output.setToolTip(self._protect_output_path)

    def _browse_protect_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Protected PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._protect_output_path = path
            self._protect_output.setText(os.path.basename(path))
            self._protect_output.setToolTip(path)

    def _do_protect(self):
        input_path  = self._protect_input_path
        output_path = self._protect_output_path
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

        if not self._check_output_dir(output_path):
            return

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
        self._protect_worker.finished.connect(self._protect_worker.deleteLater)
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
            self._ask_open_in_viewer(output_path)
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
        self._peep_input_path = path
        self._peep_input.setText(os.path.basename(path))
        self._peep_input.setToolTip(path)

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
        input_path = self._peep_input_path
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

    # -- Watermark tab ─────────────────────────────────────────────────────────

    _WM_PREVIEW_W = 340   # logical-pixel width for the preview card

    def _build_watermark_tab(self) -> QWidget:
        SP  = QStyle.StandardPixmap
        tab = QWidget()
        tab.setObjectName("tabPage")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        desc = QLabel(
            "Overlay a PNG or JPG image on every page of a PDF. "
            "Adjust position, scale, and opacity, then preview before applying."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        outer.addWidget(desc)

        # Split: controls (left) | live preview (right)
        split = QHBoxLayout()
        split.setSpacing(16)
        outer.addLayout(split, 1)

        # ── LEFT: controls ────────────────────────────────────────────────────
        ctrl = QVBoxLayout()
        ctrl.setSpacing(8)
        split.addLayout(ctrl, 55)

        # Input PDF
        ctrl.addWidget(self._field_label("Select PDF:"))
        in_row = QHBoxLayout(); in_row.setSpacing(8)
        self._wm_input = QLineEdit()
        self._wm_input.setObjectName("inputField")
        self._wm_input.setPlaceholderText("Select a PDF with Browse...")
        self._wm_input.setReadOnly(True)
        in_row.addWidget(self._wm_input)
        b_in = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_in.setFixedWidth(120)
        b_in.clicked.connect(self._browse_wm_input)
        in_row.addWidget(b_in)
        ctrl.addLayout(in_row)

        # Watermark image
        ctrl.addWidget(self._field_label("Watermark Image (PNG or JPG):"))
        img_row = QHBoxLayout(); img_row.setSpacing(8)
        self._wm_image_field = QLineEdit()
        self._wm_image_field.setObjectName("inputField")
        self._wm_image_field.setPlaceholderText("Select an image with Browse...")
        self._wm_image_field.setReadOnly(True)
        img_row.addWidget(self._wm_image_field)
        b_img = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_img.setFixedWidth(120)
        b_img.clicked.connect(self._browse_wm_image)
        img_row.addWidget(b_img)
        ctrl.addLayout(img_row)

        # Settings row: position picker | sliders + frequency
        settings = QHBoxLayout()
        settings.setSpacing(20)
        ctrl.addLayout(settings)

        # 3x3 position picker
        pos_col = QVBoxLayout()
        pos_col.setSpacing(6)
        pos_col.addWidget(self._field_label("Position:"))
        self._wm_pos_btns:  dict = {}
        self._wm_pos_group = QButtonGroup(self)
        self._wm_pos_group.setExclusive(True)
        pos_grid = QGridLayout()
        pos_grid.setSpacing(4)
        for r, row_positions in enumerate(POSITION_GRID):
            for c, pos in enumerate(row_positions):
                btn = QPushButton()
                btn.setObjectName("posBtn")
                btn.setCheckable(True)
                btn.setChecked(pos == POS_MID_CENTER)
                btn.setFixedSize(32, 32)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._wm_pos_group.addButton(btn)
                self._wm_pos_btns[pos] = btn
                pos_grid.addWidget(btn, r, c)
        pos_col.addLayout(pos_grid)
        self._wm_pos_lbl = QLabel(POSITION_LABELS[POS_MID_CENTER])
        self._wm_pos_lbl.setObjectName("hintLabel")
        self._wm_pos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pos_col.addWidget(self._wm_pos_lbl)
        pos_col.addStretch()
        settings.addLayout(pos_col)
        self._wm_pos_group.buttonClicked.connect(self._on_wm_pos_clicked)

        # Sliders + frequency
        sliders_col = QVBoxLayout()
        sliders_col.setSpacing(4)

        sliders_col.addWidget(self._field_label("Opacity:"))
        sliders_col.addSpacing(4)
        op_row = QHBoxLayout(); op_row.setSpacing(8)
        self._wm_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._wm_opacity_slider.setObjectName("wmSlider")
        self._wm_opacity_slider.setRange(10, 100)
        self._wm_opacity_slider.setValue(50)
        self._wm_opacity_lbl = QLabel("50%")
        self._wm_opacity_lbl.setObjectName("hintLabel")
        self._wm_opacity_lbl.setFixedWidth(36)
        op_row.addWidget(self._wm_opacity_slider)
        op_row.addWidget(self._wm_opacity_lbl)
        sliders_col.addLayout(op_row)
        self._wm_opacity_slider.valueChanged.connect(
            lambda v: (self._wm_opacity_lbl.setText(f"{v}%"),
                       self._wm_schedule_preview())
        )

        sliders_col.addSpacing(10)
        sliders_col.addWidget(self._field_label("Scale (% of page width):"))
        sliders_col.addSpacing(4)
        sc_row = QHBoxLayout(); sc_row.setSpacing(8)
        self._wm_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._wm_scale_slider.setObjectName("wmSlider")
        self._wm_scale_slider.setRange(5, 100)
        self._wm_scale_slider.setValue(30)
        self._wm_scale_lbl = QLabel("30%")
        self._wm_scale_lbl.setObjectName("hintLabel")
        self._wm_scale_lbl.setFixedWidth(36)
        sc_row.addWidget(self._wm_scale_slider)
        sc_row.addWidget(self._wm_scale_lbl)
        sliders_col.addLayout(sc_row)
        self._wm_scale_slider.valueChanged.connect(
            lambda v: (self._wm_scale_lbl.setText(f"{v}%"),
                       self._wm_schedule_preview())
        )

        sliders_col.addSpacing(10)
        sliders_col.addWidget(self._field_label("Frequency:"))
        self._wm_freq_btns: dict = {}
        for freq, label in FREQ_LABELS.items():
            rb = QRadioButton(label)
            rb.setChecked(freq == FREQ_ALL)
            rb.setObjectName("radioBtn")
            rb.toggled.connect(
                lambda checked: self._wm_schedule_preview() if checked else None
            )
            self._wm_freq_btns[freq] = rb
            sliders_col.addWidget(rb)

        sliders_col.addStretch()
        settings.addLayout(sliders_col)

        # Output path
        ctrl.addWidget(self._field_label("Save Watermarked PDF As:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._wm_output_field = QLineEdit()
        self._wm_output_field.setObjectName("inputField")
        self._wm_output_field.setReadOnly(True)
        self._wm_output_field.setPlaceholderText("Output filename (auto-filled on browse)...")
        out_row.addWidget(self._wm_output_field)
        b_out = self._secondary_btn("Browse...", SP.SP_DirOpenIcon)
        b_out.setFixedWidth(120)
        b_out.clicked.connect(self._browse_wm_output)
        out_row.addWidget(b_out)
        ctrl.addLayout(out_row)

        # Progress + status
        self._wm_progress = self._make_progress()
        ctrl.addWidget(self._wm_progress)
        self._wm_status = QLabel("")
        self._wm_status.setObjectName("statusLabel")
        ctrl.addWidget(self._wm_status)

        # Apply button
        self._wm_btn = self._primary_btn("Apply Watermark")
        self._wm_btn.setFixedHeight(52)
        self._wm_btn.clicked.connect(self._do_watermark)
        ctrl.addWidget(self._wm_btn)

        # ── RIGHT: live preview ───────────────────────────────────────────────
        prev_col = QVBoxLayout()
        prev_col.setSpacing(8)
        split.addLayout(prev_col, 45)

        prev_hdr = QLabel("Preview")
        prev_hdr.setObjectName("sectionTitle")
        prev_col.addWidget(prev_hdr)

        nav_row = QHBoxLayout(); nav_row.setSpacing(8)
        self._wm_prev_btn = self._secondary_btn("<")
        self._wm_prev_btn.setFixedWidth(36)
        self._wm_prev_btn.clicked.connect(self._wm_prev_page)
        self._wm_page_nav_lbl = QLabel("No PDF loaded")
        self._wm_page_nav_lbl.setObjectName("hintLabel")
        self._wm_page_nav_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._wm_next_btn = self._secondary_btn(">")
        self._wm_next_btn.setFixedWidth(36)
        self._wm_next_btn.clicked.connect(self._wm_next_page)
        nav_row.addWidget(self._wm_prev_btn)
        nav_row.addWidget(self._wm_page_nav_lbl, 1)
        nav_row.addWidget(self._wm_next_btn)
        prev_col.addLayout(nav_row)

        self._wm_preview_scroll = QScrollArea()
        self._wm_preview_scroll.setObjectName("viewerScroll")
        self._wm_preview_scroll.setWidgetResizable(True)
        self._wm_preview_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._wm_preview_lbl = QLabel(
            "Select a PDF and watermark image\nto see the live preview."
        )
        self._wm_preview_lbl.setObjectName("pageCard")
        self._wm_preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._wm_preview_lbl.setWordWrap(True)
        self._wm_preview_lbl.setMinimumSize(200, 260)
        self._wm_preview_scroll.setWidget(self._wm_preview_lbl)
        prev_col.addWidget(self._wm_preview_scroll, 1)

        self._wm_rendering_lbl = QLabel("Rendering preview...")
        self._wm_rendering_lbl.setObjectName("hintLabel")
        self._wm_rendering_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._wm_rendering_lbl.setVisible(False)
        prev_col.addWidget(self._wm_rendering_lbl)

        return tab

    # -- Watermark callbacks ───────────────────────────────────────────────────

    def _browse_wm_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF to Watermark", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._wm_input_path = path
        self._wm_input.setText(os.path.basename(path))
        self._wm_input.setToolTip(path)

        # Count pages for navigation
        try:
            import fitz
            doc = fitz.open(path)
            self._wm_page_count = len(doc)
            doc.close()
        except Exception:
            self._wm_page_count = 1
        self._wm_page_index = 0
        self._wm_update_nav_label()

        # Auto-fill output path
        if not self._wm_output_path:
            stem = path[:-4] if path.lower().endswith(".pdf") else path
            self._wm_output_path = stem + "_watermarked.pdf"
            self._wm_output_field.setText(os.path.basename(self._wm_output_path))
            self._wm_output_field.setToolTip(self._wm_output_path)

        self._wm_schedule_preview()

    def _browse_wm_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", "",
            "Images (*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG)"
        )
        if path:
            self._wm_image_path = path
            self._wm_image_field.setText(os.path.basename(path))
            self._wm_image_field.setToolTip(path)
            self._wm_schedule_preview()

    def _browse_wm_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Watermarked PDF As", "", "PDF Files (*.pdf)"
        )
        if path:
            self._wm_output_path = path
            self._wm_output_field.setText(os.path.basename(path))
            self._wm_output_field.setToolTip(path)

    def _on_wm_pos_clicked(self, btn: QPushButton):
        for pos, b in self._wm_pos_btns.items():
            if b is btn:
                self._wm_pos_lbl.setText(POSITION_LABELS[pos])
                break
        self._wm_schedule_preview()

    def _get_wm_position(self) -> str:
        for pos, btn in self._wm_pos_btns.items():
            if btn.isChecked():
                return pos
        return POS_MID_CENTER

    def _get_wm_frequency(self) -> str:
        for freq, rb in self._wm_freq_btns.items():
            if rb.isChecked():
                return freq
        return FREQ_ALL

    def _wm_update_nav_label(self):
        if self._wm_page_count > 0:
            self._wm_page_nav_lbl.setText(
                f"Page {self._wm_page_index + 1} of {self._wm_page_count}"
            )
        else:
            self._wm_page_nav_lbl.setText("No PDF loaded")

    def _wm_prev_page(self):
        if self._wm_page_index > 0:
            self._wm_page_index -= 1
            self._wm_update_nav_label()
            self._wm_schedule_preview()

    def _wm_next_page(self):
        if self._wm_page_index < self._wm_page_count - 1:
            self._wm_page_index += 1
            self._wm_update_nav_label()
            self._wm_schedule_preview()

    def _wm_schedule_preview(self):
        """Restart the debounce timer; preview renders when user stops changing."""
        if self._wm_preview_timer and self._wm_input_path and self._wm_image_path:
            self._wm_preview_timer.start()

    def _start_wm_preview(self):
        if not self._wm_input_path or not self._wm_image_path:
            return
        if self._wm_preview_worker and self._wm_preview_worker.isRunning():
            self._wm_preview_worker.stop()
            self._wm_preview_worker.wait(300)

        self._wm_rendering_lbl.setVisible(True)
        self._wm_preview_worker = _WatermarkPreviewWorker(
            self.watermarker,
            self._wm_input_path,
            self._wm_image_path,
            self._get_wm_position(),
            self._wm_scale_slider.value() / 100.0,
            self._wm_opacity_slider.value() / 100.0,
            self._wm_page_index,
            self._get_wm_frequency(),
        )
        self._wm_preview_worker.preview_ready.connect(self._on_wm_preview_ready)
        self._wm_preview_worker.start()

    def _on_wm_preview_ready(self, qimg):
        self._wm_rendering_lbl.setVisible(False)
        if qimg is None:
            self._wm_preview_lbl.setText(
                "Preview failed.\nMake sure Pillow is installed:\n"
                "pip install Pillow"
            )
            return

        screen = QApplication.primaryScreen()
        dpr    = screen.devicePixelRatio() if screen else 1.0
        px     = QPixmap.fromImage(qimg)
        target = int(self._WM_PREVIEW_W * dpr)
        scaled = px.scaledToWidth(target, Qt.TransformationMode.SmoothTransformation)
        scaled.setDevicePixelRatio(dpr)

        logical_h = int(scaled.height() / dpr)
        self._wm_preview_lbl.setPixmap(scaled)
        self._wm_preview_lbl.setFixedSize(self._WM_PREVIEW_W, logical_h)

    def _do_watermark(self):
        input_path  = self._wm_input_path
        image_path  = self._wm_image_path
        output_path = self._wm_output_path

        def err(msg):
            self._wm_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._wm_status.setText(msg)

        if not input_path or not os.path.isfile(input_path):
            return err("Please select a valid PDF file.")
        if not image_path or not os.path.isfile(image_path):
            return err("Please select a valid watermark image.")
        if not output_path:
            return err("Please set an output file path.")

        if not self._check_output_dir(output_path):
            return

        if (os.path.realpath(output_path) != os.path.realpath(input_path)
                and os.path.exists(output_path)):
            reply = QMessageBox.question(
                self, "File Already Exists",
                f"'{os.path.basename(output_path)}' already exists.\nOverwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._wm_btn.setEnabled(False)
        self._wm_progress.setValue(0)
        self._wm_status.setStyleSheet("")
        self._wm_status.setText("Applying watermark...")

        self._wm_worker = _WatermarkWorker(
            self.watermarker, input_path, output_path, image_path,
            self._get_wm_position(), self._get_wm_frequency(),
            self._wm_scale_slider.value() / 100.0,
            self._wm_opacity_slider.value() / 100.0,
        )
        self._wm_worker.progress_changed.connect(self._wm_progress.setValue)
        self._wm_worker.watermark_done.connect(
            lambda ok, msg: self._wm_done(ok, msg, output_path)
        )
        self._wm_worker.finished.connect(self._wm_worker.deleteLater)
        self._wm_worker.start()

    def _wm_done(self, success: bool, message: str, output_path: str):
        self._wm_btn.setEnabled(True)
        self._wm_progress.setValue(100 if success else 0)
        if success:
            self._wm_status.setStyleSheet(
                f"color: {self.theme.get_color('success')};"
            )
            self._wm_status.setText(f"Saved: {os.path.basename(output_path)}")
            self.history.add_watermark(output_path)
            QMessageBox.information(self, "Watermark Applied", message)
            self._ask_open_in_viewer(output_path)
        else:
            self._wm_status.setStyleSheet(
                f"color: {self.theme.get_color('error')};"
            )
            self._wm_status.setText("Watermark failed.")
            QMessageBox.critical(self, "Error", message)

    # -- History callbacks ─────────────────────────────────────────────────────

    def _on_tab_change(self, index: int):
        if index == 11:
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

        if not self._check_output_dir(output):
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
        self._merge_worker.finished.connect(self._merge_worker.deleteLater)
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
            self._set_status(f"Done! Saved: {os.path.basename(self._output_path)}")
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
                self._ask_open_in_viewer(self._output_path)
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
            self._ask_open_in_viewer(self._output_path)
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
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
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

    # ── License gate ──────────────────────────────────────────────────────────
    # Must be checked before the main window is shown.
    # If no valid license is found, show the activation dialog.
    # The dialog is modal and cannot be dismissed — app quits if user cancels.
    from .license import LicenseManager
    from .activation_dialog import ActivationDialog

    license_mgr = LicenseManager()
    if not license_mgr.is_activated():
        dlg = ActivationDialog(license_mgr)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
    # ─────────────────────────────────────────────────────────────────────────

    window = PDFMergerApp(license_mgr=license_mgr)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
