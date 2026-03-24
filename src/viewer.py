"""
PDF Viewer widget -- peep-view gating.

Regular PDFs open fully with no restrictions.
PDFs created by this app's Peep feature carry a '/PeepApp' metadata
marker; those files show only the free pages and lock the rest until
the user enters the password to unlock the companion full PDF.

Uses PyMuPDF (_RenderWorker) for high-quality page rendering.
Retina / HiDPI displays are handled via device-pixel-ratio scaling.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QStyle,
    QVBoxLayout, QWidget,
)
from pypdf import PdfReader

from .dialogs import _PasswordDialog
from .workers import _RenderWorker

_PEEP_MARKER = "PDF-Merger-Peep"


class _PageCard(QWidget):
    """Displays one PDF page -- either a rendered image or a locked placeholder."""

    CARD_W = 620

    def __init__(self, page_num: int, locked: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setFixedWidth(self.CARD_W)

        h = int(self.CARD_W * 1.414)   # A4 aspect ratio placeholder height
        if locked:
            self._img_lbl.setObjectName("lockedPage")
            self._img_lbl.setPixmap(self._locked_pixmap(page_num + 1, self.CARD_W, h))
            self._img_lbl.setFixedHeight(h)
        else:
            self._img_lbl.setObjectName("pageCard")
            self._img_lbl.setFixedHeight(h)
            self._img_lbl.setText(f"Loading page {page_num + 1}...")

        layout.addWidget(self._img_lbl)

        num_lbl = QLabel(f"Page {page_num + 1}")
        num_lbl.setObjectName("pageNumLabel")
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num_lbl)

    @staticmethod
    def _locked_pixmap(page_num: int, w: int, h: int) -> QPixmap:
        px = QPixmap(w, h)
        px.fill(QColor("#2A2A3E"))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        f_big = QFont()
        f_big.setPointSize(20)
        f_big.setBold(True)
        p.setFont(f_big)
        p.setPen(QColor("#5A5A7A"))
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "LOCKED")

        f_small = QFont()
        f_small.setPointSize(11)
        p.setFont(f_small)
        p.setPen(QColor("#7A7A9A"))
        hint_rect = px.rect().adjusted(0, int(h * 0.55), 0, 0)
        p.drawText(
            hint_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            f"Page {page_num}  -  Enter password to unlock",
        )
        p.end()
        return px

    def set_image(self, img: QImage) -> None:
        """Display a rendered page image, scaled to CARD_W with Retina support."""
        screen = QApplication.primaryScreen()
        dpr    = screen.devicePixelRatio() if screen else 1.0

        pix    = QPixmap.fromImage(img)
        target = int(self.CARD_W * dpr)
        scaled = pix.scaledToWidth(target, Qt.TransformationMode.SmoothTransformation)
        scaled.setDevicePixelRatio(dpr)

        logical_h = int(scaled.height() / dpr)
        self._img_lbl.setFixedHeight(logical_h)
        self._img_lbl.setPixmap(scaled)
        self._img_lbl.setText("")
        self._img_lbl.setObjectName("pageCard")


class PDFViewerWidget(QWidget):
    """
    Scrollable PDF viewer.

    - Regular PDFs: all pages shown, no gating.
    - Peep PDFs (made by this app): free pages visible, rest locked.
      Unlocking loads the companion _peep_full.pdf with the password.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pdf_path    = ""     # file the user opened
        self._render_path = ""     # file we actually render from (may be full PDF)
        self._password    = ""
        self._total_pages = 0
        self._free_pages  = 0
        self._unlocked    = False
        self._is_peep     = False
        self._cards: list[_PageCard] = []
        self._worker: _RenderWorker | None = None
        self._build_ui()

    # -- UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # File open row
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self._path_edit = QLineEdit()
        self._path_edit.setObjectName("inputField")
        self._path_edit.setPlaceholderText("Select a PDF file to view...")
        self._path_edit.setReadOnly(True)
        file_row.addWidget(self._path_edit)

        SP       = QStyle.StandardPixmap
        open_btn = QPushButton("Open PDF")
        open_btn.setObjectName("secondaryBtn")
        open_btn.setIcon(QApplication.style().standardIcon(SP.SP_DirOpenIcon))
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_pdf)
        file_row.addWidget(open_btn)
        outer.addLayout(file_row)

        # Info / action row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self._info_lbl = QLabel("")
        self._info_lbl.setObjectName("hintLabel")
        action_row.addWidget(self._info_lbl)
        action_row.addStretch()

        self._unlock_btn = QPushButton("Unlock Remaining Pages")
        self._unlock_btn.setObjectName("primaryBtn")
        self._unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._unlock_btn.clicked.connect(self._unlock)
        self._unlock_btn.setVisible(False)
        action_row.addWidget(self._unlock_btn)

        self._relock_btn = QPushButton("Re-lock")
        self._relock_btn.setObjectName("secondaryBtn")
        self._relock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._relock_btn.clicked.connect(self._relock)
        self._relock_btn.setVisible(False)
        action_row.addWidget(self._relock_btn)

        outer.addLayout(action_row)

        # Scrollable page area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("viewerScroll")

        self._pages_widget = QWidget()
        self._pages_layout = QVBoxLayout(self._pages_widget)
        self._pages_layout.setContentsMargins(24, 24, 24, 24)
        self._pages_layout.setSpacing(20)
        self._pages_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        self._placeholder = QLabel("Open a PDF file to view its pages.")
        self._placeholder.setObjectName("descLabel")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pages_layout.addWidget(self._placeholder)

        self._scroll.setWidget(self._pages_widget)
        outer.addWidget(self._scroll, 1)

        # Status bar
        self._status = QLabel("")
        self._status.setObjectName("statusLabel")
        outer.addWidget(self._status)

    # -- File open ────────────────────────────────────────────────────────────

    def _open_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self.load_pdf(path)

    def load_pdf(self, path: str) -> None:
        """Public entry point -- called by the file picker or other tabs."""
        self._pdf_path    = path
        self._render_path = path
        self._password    = ""
        self._unlocked    = False
        self._is_peep     = False
        self._path_edit.setText(os.path.basename(path))
        self._path_edit.setToolTip(path)
        self._load_pdf()

    # -- Internal load ────────────────────────────────────────────────────────

    def _load_pdf(self) -> None:
        self._stop_worker()

        try:
            reader = PdfReader(self._pdf_path)

            # Check for app-specific peep marker
            meta = reader.metadata or {}
            if meta.get("/PeepApp") == _PEEP_MARKER:
                self._is_peep     = True
                self._free_pages  = int(meta.get("/PeepFreePages",  1))
                self._total_pages = int(meta.get("/PeepTotalPages", self._free_pages))
                self._render_path = self._pdf_path   # render from preview file
            else:
                self._is_peep = False
                if reader.is_encrypted:
                    if not self._password:
                        # Encrypted regular PDF -- ask for password
                        self._total_pages = 0
                        self._free_pages  = 0
                        self._status.setText(
                            "This PDF is password-protected. "
                            "Click 'Unlock PDF' to enter the password."
                        )
                        self._unlock_btn.setText("Unlock PDF")
                        self._unlock_btn.setVisible(True)
                        self._relock_btn.setVisible(False)
                        self._info_lbl.setText("")
                        self._rebuild_cards()
                        return
                    result = reader.decrypt(self._password)
                    if result == 0:
                        self._status.setText(
                            "Incorrect password. Click 'Unlock PDF' to try again."
                        )
                        self._password    = ""
                        self._total_pages = 0
                        self._free_pages  = 0
                        self._rebuild_cards()
                        self._unlock_btn.setText("Unlock PDF")
                        self._unlock_btn.setVisible(True)
                        return

                self._total_pages = len(reader.pages)
                self._free_pages  = self._total_pages   # no gating for regular PDFs

        except Exception as e:
            self._status.setText(f"Could not open PDF: {e}")
            return

        self._rebuild_cards()
        self._render_visible()

    def _rebuild_cards(self) -> None:
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        self._placeholder.setVisible(self._total_pages == 0)

        free = self._total_pages if self._unlocked else self._free_pages

        for i in range(self._total_pages):
            card = _PageCard(i, locked=(i >= free), parent=self._pages_widget)
            self._pages_layout.addWidget(card)
            self._cards.append(card)

        locked = max(0, self._total_pages - free)
        if self._total_pages:
            self._info_lbl.setText(
                f"{self._total_pages} page(s)"
                + (f"  |  {locked} locked" if self._is_peep and not self._unlocked else "")
            )
        else:
            self._info_lbl.setText("")

        # Unlock / re-lock buttons only for peep files
        self._unlock_btn.setText("Unlock Remaining Pages")
        self._unlock_btn.setVisible(self._is_peep and locked > 0 and not self._unlocked)
        self._relock_btn.setVisible(self._is_peep and self._unlocked)

    def _render_visible(self) -> None:
        end = self._total_pages if self._unlocked else self._free_pages
        if end == 0:
            return
        pwd = self._password if self._unlocked else ""
        self._worker = _RenderWorker(self._render_path, pwd, 0, end)
        self._worker.page_ready.connect(self._on_page_ready)
        self._worker.render_done.connect(self._on_render_done)
        self._worker.start()
        self._status.setText("Rendering pages...")

    def _on_page_ready(self, index: int, img: QImage) -> None:
        if 0 <= index < len(self._cards):
            self._cards[index].set_image(img)

    def _on_render_done(self) -> None:
        visible = self._total_pages if self._unlocked else self._free_pages
        locked  = max(0, self._total_pages - visible)
        self._status.setText(
            f"Showing {visible} of {self._total_pages} page(s)."
            + (f"  {locked} page(s) locked." if locked else "")
        )

    # -- Gate controls (peep files only) ──────────────────────────────────────

    def _unlock(self) -> None:
        if self._is_peep:
            # Find the companion full PDF by naming convention
            if not self._pdf_path.endswith("_peep_preview.pdf"):
                self._status.setText("Could not locate the companion full PDF.")
                return
            full_path = (
                self._pdf_path[: -len("_peep_preview.pdf")] + "_peep_full.pdf"
            )
            if not os.path.exists(full_path):
                self._status.setText(
                    f"Full PDF not found: {os.path.basename(full_path)}"
                )
                return

            dlg = _PasswordDialog(
                self,
                title="Unlock Full PDF",
                prompt="Enter the password you set when creating these peep files.",
            )
            if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.password:
                return

            try:
                reader = PdfReader(full_path)
                if reader.is_encrypted:
                    if reader.decrypt(dlg.password) == 0:
                        self._status.setText("Incorrect password. Please try again.")
                        return
            except Exception as e:
                self._status.setText(f"Could not unlock: {e}")
                return

            self._password    = dlg.password
            self._unlocked    = True
            self._render_path = full_path       # switch to full PDF for rendering
            self._stop_worker()
            self._rebuild_cards()
            self._render_visible()

        else:
            # Encrypted regular PDF
            dlg = _PasswordDialog(
                self, title="Unlock PDF",
                prompt="Enter the password for this PDF.",
            )
            if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.password:
                return

            try:
                reader = PdfReader(self._pdf_path)
                if reader.is_encrypted:
                    result = reader.decrypt(dlg.password)
                    if result == 0:
                        self._status.setText("Incorrect password. Please try again.")
                        return
                    self._total_pages = len(reader.pages)
                    self._free_pages  = self._total_pages
            except Exception as e:
                self._status.setText(f"Could not unlock: {e}")
                return

            self._password    = dlg.password
            self._unlocked    = True
            self._render_path = self._pdf_path
            self._stop_worker()
            self._rebuild_cards()
            self._render_visible()

    def _relock(self) -> None:
        self._unlocked    = False
        self._password    = ""
        self._render_path = self._pdf_path   # back to preview file
        self._stop_worker()
        self._rebuild_cards()
        self._render_visible()

    def _stop_worker(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()
