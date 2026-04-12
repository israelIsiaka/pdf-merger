"""
Annotate / Sign PDF dialog.

Features:
- Drag-to-position: text block and signature can each be dragged freely
  on a live canvas preview of the PDF page.
- Signature: draw with mouse/trackpad (like macOS signature) or import image.
- Saved detail profiles: name, title, date, custom stored per-profile.
- Apply to: All / First / Last / Custom page range (e.g. "1,3,5-7").
- Output path display: filename only (full path stored separately).
"""
import datetime
import os

from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QBuffer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QImage, QPainter, QPainterPath,
    QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QDialog,
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)

from .annotator import PDFAnnotator, _DEFAULT_TEXT_X, _DEFAULT_TEXT_Y, \
    _DEFAULT_SIG_X, _DEFAULT_SIG_Y
from .annotation_profiles import AnnotationProfilesManager
from .watermark import FREQ_ALL, FREQ_FIRST, FREQ_LAST
from .workers import _AnnotateWorker, _RenderWorker


_PLACEHOLDER = "-- Use saved details --"
_CANVAS_W    = 320   # logical width of the annotation canvas


# ── Signature drawing canvas ───────────────────────────────────────────────────

class _DrawCanvas(QWidget):
    """
    A drawing surface for capturing a freehand signature.
    Strokes are stored on a transparent QImage so the result can be
    overlaid on a PDF page without a white background box.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(480, 160)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._img = QImage(480, 160, QImage.Format.Format_ARGB32)
        self._img.fill(Qt.GlobalColor.transparent)
        self._last: QPoint | None = None
        self._drawing = False

    # -- Public ────────────────────────────────────────────────────────────────

    def clear(self) -> None:
        self._img.fill(Qt.GlobalColor.transparent)
        self.update()

    def is_empty(self) -> bool:
        """Return True when no strokes have been drawn."""
        for x in range(0, self._img.width(), 4):
            for y in range(0, self._img.height(), 4):
                if QColor(self._img.pixel(x, y)).alpha() > 0:
                    return False
        return True

    def get_png_bytes(self) -> bytes:
        """Return the signature as transparent-background PNG bytes."""
        buf = QBuffer()
        buf.open(QBuffer.OpenModeFlag.WriteOnly)
        QPixmap.fromImage(self._img).save(buf, "PNG")
        return bytes(buf.data())

    def get_pixmap(self) -> QPixmap:
        return QPixmap.fromImage(self._img)

    # -- Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("white"))
        p.drawImage(0, 0, self._img)
        # Subtle guide line
        p.setPen(QPen(QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
        y = int(self.height() * 0.72)
        p.drawLine(16, y, self.width() - 16, y)
        p.end()

    # -- Mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._last    = event.position().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if not self._drawing or self._last is None:
            return
        cur = event.position().toPoint()
        p = QPainter(self._img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#1a1a1a"), 2.2,
                   Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(self._last, cur)
        p.end()
        self._last = cur
        self.update()

    def mouseReleaseEvent(self, _event) -> None:
        self._drawing = False
        self._last    = None


# ── Signature pad dialog ───────────────────────────────────────────────────────

class _SignaturePadDialog(QDialog):
    """Modal dialog with a freehand drawing canvas for capturing a signature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Draw Signature")
        self.setModal(True)
        self.sig_pixmap: QPixmap | None = None
        self.sig_bytes: bytes = b""
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        hint = QLabel(
            "Sign below using your mouse or trackpad.  "
            "Use the guide line as a baseline."
        )
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # Canvas inside a frame
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setStyleSheet("border: 1px solid #c0c4cc; border-radius: 4px;")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        self._canvas = _DrawCanvas()
        fl.addWidget(self._canvas)
        lay.addWidget(frame)

        # Buttons
        row = QHBoxLayout()
        row.setSpacing(8)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._canvas.clear)
        row.addWidget(clear_btn)
        row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)
        done_btn = QPushButton("Use Signature")
        done_btn.setObjectName("primaryBtn")
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        done_btn.clicked.connect(self._done)
        row.addWidget(done_btn)
        lay.addLayout(row)

    def _done(self) -> None:
        if self._canvas.is_empty():
            return
        self.sig_pixmap = self._canvas.get_pixmap()
        self.sig_bytes  = self._canvas.get_png_bytes()
        self.accept()


# ── Interactive annotation canvas ──────────────────────────────────────────────

class _AnnotationCanvas(QWidget):
    """
    PDF page preview with independently draggable handles — one per field.

    Handles (index → label):
      0 N  Full Name
      1 T  Title / Role
      2 D  Date
      3 C  Custom text
      4 S  Signature image

    Each handle is visible only when its content is non-empty.
    Drag any handle to reposition it independently on the page.
    """

    handle_moved = pyqtSignal(int, float, float)  # (idx, x_frac, y_frac)

    # (label, color_hex, default_x, default_y)
    _HDEFS = [
        ("N", "#1a73e8", 0.12, 0.78),
        ("T", "#0f9d58", 0.12, 0.84),
        ("D", "#f4b400", 0.12, 0.89),
        ("C", "#ea4335", 0.12, 0.94),
        ("S", "#34a853", _DEFAULT_SIG_X, _DEFAULT_SIG_Y),
    ]
    _HANDLE = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page_px:   QPixmap | None = None
        self._sig_px:    QPixmap | None = None
        self._texts:     dict = {}
        self._active:    dict = {i: False for i in range(5)}
        self._positions: dict = {i: (h[2], h[3]) for i, h in enumerate(self._HDEFS)}
        self._font_sz:   int  = 11
        self._color:     str  = "#333333"
        self._dragging:  int  = -1
        self._drag_off:  tuple = (0.0, 0.0)

        self.setMinimumSize(240, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    # -- Setters ───────────────────────────────────────────────────────────────

    def set_page(self, px: QPixmap) -> None:
        self._page_px = px
        self.update()

    def set_font_style(self, size: int, color: str) -> None:
        self._font_sz = size
        self._color   = color
        self.update()

    def set_text(self, idx: int, text: str) -> None:
        """Set text for handle idx and auto-show/hide the handle."""
        self._texts[idx]  = text.strip()
        self._active[idx] = bool(text.strip())
        self.update()

    def set_signature(self, px: QPixmap | None) -> None:
        self._sig_px     = px
        self._active[4]  = px is not None
        self.update()

    def get_position(self, idx: int) -> tuple:
        return self._positions[idx]

    def set_position(self, idx: int, x: float, y: float) -> None:
        self._positions[idx] = (x, y)
        self.update()

    # -- Coordinate mapping ────────────────────────────────────────────────────

    def _page_rect(self) -> QRect:
        if not self._page_px:
            return self.rect()
        pw, ph = self._page_px.width(), self._page_px.height()
        ww, wh = self.width(), self.height()
        scale  = min(ww / pw, wh / ph)
        dw, dh = int(pw * scale), int(ph * scale)
        return QRect((ww - dw) // 2, (wh - dh) // 2, dw, dh)

    def _to_widget(self, xf: float, yf: float) -> tuple:
        r = self._page_rect()
        return int(r.x() + r.width() * xf), int(r.y() + r.height() * yf)

    def _to_frac(self, wx: int, wy: int) -> tuple:
        r = self._page_rect()
        x = (wx - r.x()) / max(r.width(),  1)
        y = (wy - r.y()) / max(r.height(), 1)
        return max(0.02, min(0.98, x)), max(0.02, min(0.98, y))

    def _hit(self, pos: QPoint) -> int:
        """Return the index of the handle under pos, or -1 if none."""
        h = self._HANDLE + 5
        for i in range(5):
            if not self._active[i]:
                continue
            wx, wy = self._to_widget(*self._positions[i])
            if abs(pos.x() - wx) <= h and abs(pos.y() - wy) <= h:
                return i
        return -1

    # -- Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()
        hit = self._hit(pos)
        if hit == -1:
            return
        self._dragging = hit
        wx, wy = self._to_widget(*self._positions[hit])
        self._drag_off = (pos.x() - wx, pos.y() - wy)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        pos = event.position().toPoint()
        if self._dragging != -1:
            nx = pos.x() - self._drag_off[0]
            ny = pos.y() - self._drag_off[1]
            xf, yf = self._to_frac(nx, ny)
            self._positions[self._dragging] = (xf, yf)
            self.update()
        else:
            hit = self._hit(pos)
            self.setCursor(
                Qt.CursorShape.OpenHandCursor if hit != -1
                else Qt.CursorShape.ArrowCursor
            )

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging == -1:
            return
        xf, yf = self._positions[self._dragging]
        self.handle_moved.emit(self._dragging, xf, yf)
        self._dragging = -1
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # -- Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pr = self._page_rect()

        # Background behind page
        p.fillRect(self.rect(), QColor("#d8dde6"))

        # Page
        if self._page_px:
            p.drawPixmap(pr, self._page_px)
        else:
            p.fillRect(pr, QColor("white"))
            p.setPen(QColor("#999999"))
            p.drawText(pr, Qt.AlignmentFlag.AlignCenter, "Loading page...")

        # Text items (N, T, D, C — indices 0-3)
        font = QFont()
        font.setPointSize(max(6, self._font_sz - 3))
        p.setFont(font)
        fm = QFontMetrics(font)
        for i in range(4):
            text = self._texts.get(i, "")
            if self._active[i] and text:
                wx, wy = self._to_widget(*self._positions[i])
                self._paint_text_item(p, wx, wy, text, i, pr, fm)

        # Signature overlay (index 4)
        if self._active[4] and self._sig_px:
            sx, sy = self._to_widget(*self._positions[4])
            self._paint_sig(p, sx, sy, pr.width())

        # Handles — drawn on top for all active items
        for i in range(5):
            if self._active[i]:
                wx, wy = self._to_widget(*self._positions[i])
                label, color_hex, _, _ = self._HDEFS[i]
                self._paint_handle(p, wx, wy, QColor(color_hex), label)

        p.end()

    def _paint_text_item(self, p: QPainter, cx: int, cy: int, text: str,
                         idx: int, pr: QRect, fm: QFontMetrics) -> None:
        lh = fm.height() + 1
        bw = fm.horizontalAdvance(text) + 8
        bh = lh + 6
        x0 = cx - bw // 2
        y0 = cy - bh // 2
        x0 = max(pr.left() + 2, min(x0, pr.right()  - bw - 2))
        y0 = max(pr.top()  + 2, min(y0, pr.bottom() - bh - 2))
        _, color_hex, _, _ = self._HDEFS[idx]
        bg = QColor(color_hex); bg.setAlpha(30)
        border = QColor(color_hex); border.setAlpha(160)
        p.fillRect(x0 - 2, y0 - 2, bw + 4, bh + 4, bg)
        p.setPen(QPen(border, 1))
        p.drawRect(x0 - 2, y0 - 2, bw + 4, bh + 4)
        p.setPen(QColor(self._color))
        p.drawText(x0 + 4, y0 + fm.ascent() + 3, text)

    def _paint_sig(self, p: QPainter, cx: int, cy: int, page_w: int) -> None:
        sw = max(60, int(page_w * 0.28))
        aspect = self._sig_px.width() / max(self._sig_px.height(), 1)
        sh = max(20, int(sw / aspect))
        x0, y0 = cx - sw // 2, cy - sh // 2
        p.drawPixmap(x0, y0, sw, sh, self._sig_px)
        p.setPen(QPen(QColor("#34a853"), 1, Qt.PenStyle.DashLine))
        p.drawRect(x0, y0, sw, sh)

    def _paint_handle(self, p: QPainter, cx: int, cy: int,
                      col: QColor, label: str) -> None:
        h = self._HANDLE
        p.fillRect(cx - h // 2, cy - h // 2, h, h, col)
        p.setPen(QColor("white"))
        f = QFont(); f.setPointSize(7); f.setBold(True)
        p.setFont(f)
        p.drawText(QRect(cx - h // 2, cy - h // 2, h, h),
                   Qt.AlignmentFlag.AlignCenter, label)


# ── Main dialog ────────────────────────────────────────────────────────────────

class _AnnotateDialog(QDialog):
    """
    Modal dialog for annotating / signing a PDF.

    On success ``self.output_path`` holds the saved file path and the
    dialog closes with ``QDialog.DialogCode.Accepted``.
    """

    def __init__(
        self,
        parent: QWidget,
        input_path: str,
        profiles: AnnotationProfilesManager,
        annotator: PDFAnnotator,
    ):
        super().__init__(parent)
        self._input_path   = input_path
        self._profiles     = profiles
        self._annotator    = annotator
        self._worker       = None
        self._render_worker = None
        self._color_hex    = "#333333"
        self._sig_bytes: bytes = b""
        self._sig_pixmap: QPixmap | None = None
        self._output_full  = ""   # full path (basename shown in field)
        self.output_path   = ""

        self.setWindowTitle("Annotate / Sign PDF")
        self.setModal(True)
        self.setMinimumWidth(880)
        self.setMinimumHeight(580)

        self._build_ui()
        self._refresh_profiles()
        self._load_last_used()     # pre-fill fields from last session
        self._suggest_output()
        self._load_page()          # kick off background page render

    # -- UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        # Profile row
        outer.addWidget(self._lbl("Saved details:"))
        pr = QHBoxLayout(); pr.setSpacing(8)
        self._profile_combo = self._combo()
        self._profile_combo.currentTextChanged.connect(self._on_profile_selected)
        pr.addWidget(self._profile_combo)
        self._del_btn = self._sec("Delete", 72)
        self._del_btn.clicked.connect(self._delete_profile)
        pr.addWidget(self._del_btn)
        outer.addLayout(pr)

        outer.addSpacing(4)

        # Main split
        split = QHBoxLayout(); split.setSpacing(18)
        outer.addLayout(split, 1)

        # ── Left panel ────────────────────────────────────────────────────────
        left = QVBoxLayout(); left.setSpacing(8)
        split.addLayout(left, 52)

        # Text fields
        fg = QGridLayout(); fg.setSpacing(6); fg.setColumnStretch(1, 1)
        self._name_f   = self._inp("e.g. Jane Smith")
        self._title_f  = self._inp("e.g. Director of Operations")
        self._custom_f = self._inp("Any additional text...")

        fg.addWidget(self._lbl("Full Name:"),    0, 0)
        fg.addWidget(self._name_f,               0, 1)
        fg.addWidget(self._lbl("Title / Role:"), 1, 0)
        fg.addWidget(self._title_f,              1, 1)

        dr = QHBoxLayout(); dr.setSpacing(6)
        self._date_f = self._inp("e.g. March 24, 2026")
        dr.addWidget(self._date_f)
        tb = self._sec("Today", 64); tb.clicked.connect(self._fill_today)
        dr.addWidget(tb)
        fg.addWidget(self._lbl("Date:"),         2, 0)
        fg.addLayout(dr,                         2, 1)

        fg.addWidget(self._lbl("Custom Text:"),  3, 0)
        fg.addWidget(self._custom_f,             3, 1)
        left.addLayout(fg)

        for f in (self._name_f, self._title_f, self._date_f, self._custom_f):
            f.textChanged.connect(self._update_canvas_content)

        # Signature section
        left.addSpacing(4)
        left.addWidget(self._lbl("Signature:"))
        sig_row = QHBoxLayout(); sig_row.setSpacing(8)
        draw_btn = self._sec("Draw...", 90)
        draw_btn.clicked.connect(self._draw_signature)
        sig_row.addWidget(draw_btn)
        import_btn = self._sec("Import Image...", 110)
        import_btn.clicked.connect(self._import_signature)
        sig_row.addWidget(import_btn)
        self._clear_sig_btn = self._sec("Clear", 60)
        self._clear_sig_btn.clicked.connect(self._clear_signature)
        self._clear_sig_btn.setEnabled(False)
        sig_row.addWidget(self._clear_sig_btn)
        left.addLayout(sig_row)

        # Signature thumbnail
        self._sig_thumb = QLabel("No signature added")
        self._sig_thumb.setObjectName("hintLabel")
        self._sig_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sig_thumb.setFixedHeight(48)
        self._sig_thumb.setStyleSheet(
            "border: 1px dashed #c0c4cc; border-radius: 4px;"
        )
        left.addWidget(self._sig_thumb)

        # Save as named profile
        left.addSpacing(4)
        sv = QHBoxLayout(); sv.setSpacing(8)
        sv.addWidget(self._lbl("Save as profile:"))
        self._prof_name_f = self._inp("Profile name (optional)...")
        sv.addWidget(self._prof_name_f)
        save_prof_btn = self._sec("Save", 56)
        save_prof_btn.setToolTip("Save current details as a named profile")
        save_prof_btn.clicked.connect(self._save_named_profile)
        sv.addWidget(save_prof_btn)
        left.addLayout(sv)

        left.addSpacing(4)

        # Apply-to + font + color
        opts = QHBoxLayout(); opts.setSpacing(20)
        left.addLayout(opts)

        freq_col = QVBoxLayout(); freq_col.setSpacing(4)
        freq_col.addWidget(self._lbl("Apply to:"))
        self._freq_grp   = QButtonGroup(self)
        self._freq_all   = QRadioButton("All pages")
        self._freq_first = QRadioButton("First page only")
        self._freq_last  = QRadioButton("Last page only")
        self._freq_custom = QRadioButton("Selected pages:")
        self._freq_all.setChecked(True)
        for rb in (self._freq_all, self._freq_first,
                   self._freq_last, self._freq_custom):
            self._freq_grp.addButton(rb)
            freq_col.addWidget(rb)
        self._custom_pages_f = self._inp('e.g. "1,3,5-7"')
        self._custom_pages_f.setEnabled(False)
        self._freq_custom.toggled.connect(self._custom_pages_f.setEnabled)
        freq_col.addWidget(self._custom_pages_f)
        freq_col.addStretch()
        opts.addLayout(freq_col)

        style_col = QVBoxLayout(); style_col.setSpacing(4)
        style_col.addWidget(self._lbl("Font size:"))
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 24); self._font_spin.setValue(11)
        self._font_spin.setFixedWidth(64)
        self._font_spin.valueChanged.connect(self._update_canvas_content)
        style_col.addWidget(self._font_spin)
        style_col.addSpacing(8)
        style_col.addWidget(self._lbl("Text color:"))
        self._color_btn = QPushButton()
        self._color_btn.setObjectName("secondaryBtn")
        self._color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_btn.setFixedSize(64, 28)
        self._color_btn.clicked.connect(self._pick_color)
        self._refresh_color_btn()
        style_col.addWidget(self._color_btn)
        style_col.addStretch()
        opts.addLayout(style_col)

        left.addStretch()

        # ── Right panel: canvas ───────────────────────────────────────────────
        right = QVBoxLayout(); right.setSpacing(6)
        split.addLayout(right, 48)

        hdr = QLabel("Drag handles to position each field")
        hdr.setObjectName("sectionTitle")
        right.addWidget(hdr)

        hint = QLabel(
            "N = Name   T = Title   D = Date   C = Custom   S = Signature  "
            "(handles appear after content is added)"
        )
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        right.addWidget(hint)

        # Page navigation
        nav = QHBoxLayout(); nav.setSpacing(6)
        self._prev_btn = self._sec("<", 32)
        self._prev_btn.clicked.connect(self._prev_page)
        self._page_lbl = QLabel(self._nav_text(0))
        self._page_lbl.setObjectName("hintLabel")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next_btn = self._sec(">", 32)
        self._next_btn.clicked.connect(self._next_page)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._page_lbl, 1)
        nav.addWidget(self._next_btn)
        right.addLayout(nav)

        self._canvas = _AnnotationCanvas()
        right.addWidget(self._canvas, 1)

        self._loading_lbl = QLabel("Rendering page...")
        self._loading_lbl.setObjectName("hintLabel")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.setVisible(False)
        right.addWidget(self._loading_lbl)

        # ── Bottom: output + progress + buttons ───────────────────────────────
        outer.addWidget(self._lbl("Save annotated PDF as:"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self._out_display = QLineEdit()
        self._out_display.setObjectName("inputField")
        self._out_display.setReadOnly(True)
        out_row.addWidget(self._out_display)
        br = self._sec("Browse...", 90)
        br.clicked.connect(self._browse_output)
        out_row.addWidget(br)
        outer.addLayout(out_row)

        self._progress = QProgressBar()
        self._progress.setObjectName("progressBar")
        self._progress.setRange(0, 100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setVisible(False)
        outer.addWidget(self._progress)

        self._status = QLabel("")
        self._status.setObjectName("hintLabel")
        self._status.setWordWrap(True)
        outer.addWidget(self._status)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel = self._sec("Cancel"); cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("primaryBtn")
        self._apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(self._apply_btn)
        outer.addLayout(btn_row)

    # -- Widget helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _lbl(t: str) -> QLabel:
        l = QLabel(t); l.setObjectName("fieldLabel"); return l

    @staticmethod
    def _inp(ph: str = "") -> QLineEdit:
        w = QLineEdit(); w.setObjectName("inputField")
        if ph: w.setPlaceholderText(ph)
        return w

    @staticmethod
    def _sec(t: str, w: int = 0) -> QPushButton:
        b = QPushButton(t); b.setObjectName("secondaryBtn")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if w: b.setFixedWidth(w)
        return b

    @staticmethod
    def _combo():
        from PyQt6.QtWidgets import QComboBox
        cb = QComboBox()
        cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return cb

    # -- Profile management ────────────────────────────────────────────────────

    def _refresh_profiles(self) -> None:
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        self._profile_combo.addItem(_PLACEHOLDER)
        for n in self._profiles.profile_names():
            if n != "_last_used_":          # hide internal auto-save entry
                self._profile_combo.addItem(n)
        self._profile_combo.setCurrentIndex(0)
        self._profile_combo.blockSignals(False)
        self._del_btn.setEnabled(False)

    def _on_profile_selected(self, name: str) -> None:
        if not name or name == _PLACEHOLDER:
            self._del_btn.setEnabled(False)
            return
        self._del_btn.setEnabled(True)
        d = self._profiles.get(name)
        self._name_f.setText(d.get("full_name", ""))
        self._title_f.setText(d.get("title", ""))
        self._date_f.setText(d.get("date", ""))
        self._custom_f.setText(d.get("custom", ""))

    def _delete_profile(self) -> None:
        n = self._profile_combo.currentText()
        if n and n != _PLACEHOLDER:
            self._profiles.delete(n)
            self._refresh_profiles()

    # -- Field helpers ─────────────────────────────────────────────────────────

    def _fill_today(self) -> None:
        self._date_f.setText(datetime.date.today().strftime("%B %d, %Y"))

    def _suggest_output(self) -> None:
        if not self._input_path:
            return
        base, ext = os.path.splitext(self._input_path)
        self._output_full = f"{base}_signed{ext}"
        self._out_display.setText(os.path.basename(self._output_full))

    # -- Color ─────────────────────────────────────────────────────────────────

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(QColor(self._color_hex), self, "Text Color")
        if c.isValid():
            self._color_hex = c.name()
            self._refresh_color_btn()
            self._update_canvas_content()

    def _refresh_color_btn(self) -> None:
        self._color_btn.setStyleSheet(
            f"background-color:{self._color_hex}; border-radius:4px;"
        )
        self._color_btn.setText("")

    # -- Signature ─────────────────────────────────────────────────────────────

    def _draw_signature(self) -> None:
        dlg = _SignaturePadDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.sig_bytes:
            self._set_signature(dlg.sig_pixmap, dlg.sig_bytes)

    def _import_signature(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Signature Image", "",
            "Images (*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG)"
        )
        if not path:
            return
        px = QPixmap(path)
        if px.isNull():
            self._status.setText("Could not load image.")
            return
        with open(path, "rb") as f:
            sig_bytes = f.read()
        self._set_signature(px, sig_bytes)

    def _set_signature(self, px: QPixmap, sig_bytes: bytes) -> None:
        self._sig_pixmap = px
        self._sig_bytes  = sig_bytes
        self._canvas.set_signature(px)
        self._clear_sig_btn.setEnabled(True)
        scaled = px.scaledToHeight(44, Qt.TransformationMode.SmoothTransformation)
        self._sig_thumb.setPixmap(scaled)
        self._sig_thumb.setText("")

    def _clear_signature(self) -> None:
        self._sig_pixmap = None
        self._sig_bytes  = b""
        self._canvas.set_signature(None)
        self._clear_sig_btn.setEnabled(False)
        self._sig_thumb.setText("No signature added")
        self._sig_thumb.setPixmap(QPixmap())

    # -- Output browse ─────────────────────────────────────────────────────────

    def _browse_output(self) -> None:
        start = self._output_full or os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotated PDF As", start, "PDF Files (*.pdf)"
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self._output_full = path
            self._out_display.setText(os.path.basename(path))

    # -- Page navigation ───────────────────────────────────────────────────────

    def _page_count(self) -> int:
        try:
            import fitz
            doc = fitz.open(self._input_path)
            n   = len(doc); doc.close(); return n
        except Exception:
            return 1

    def _nav_text(self, idx: int) -> str:
        n = getattr(self, "_total_pages", 0)
        return f"Page {idx + 1} of {n}" if n else "Loading..."

    def _prev_page(self) -> None:
        idx = getattr(self, "_cur_page", 0)
        if idx > 0:
            self._cur_page = idx - 1
            self._page_lbl.setText(self._nav_text(self._cur_page))
            self._load_page()

    def _next_page(self) -> None:
        idx   = getattr(self, "_cur_page",   0)
        total = getattr(self, "_total_pages", 1)
        if idx < total - 1:
            self._cur_page = idx + 1
            self._page_lbl.setText(self._nav_text(self._cur_page))
            self._load_page()

    def _load_page(self) -> None:
        """Render the current page in the background for the canvas."""
        if not hasattr(self, "_cur_page"):
            self._cur_page    = 0
            self._total_pages = self._page_count()
            self._page_lbl.setText(self._nav_text(0))

        if self._render_worker and self._render_worker.isRunning():
            self._render_worker.stop()
            self._render_worker.wait(200)

        self._loading_lbl.setVisible(True)
        idx = self._cur_page
        self._render_worker = _RenderWorker(
            self._input_path, "", idx, idx + 1, dpi=120
        )
        self._render_worker.page_ready.connect(self._on_page_ready)
        self._render_worker.render_done.connect(
            lambda: self._loading_lbl.setVisible(False)
        )
        self._render_worker.start()

    def _on_page_ready(self, _idx: int, qimg: QImage) -> None:
        screen = QApplication.primaryScreen()
        dpr    = screen.devicePixelRatio() if screen else 1.0
        px     = QPixmap.fromImage(qimg)
        px.setDevicePixelRatio(dpr)
        self._canvas.set_page(px)

    # -- Canvas sync ───────────────────────────────────────────────────────────

    def _update_canvas_content(self) -> None:
        self._canvas.set_text(0, self._name_f.text())
        self._canvas.set_text(1, self._title_f.text())
        self._canvas.set_text(2, self._date_f.text())
        self._canvas.set_text(3, self._custom_f.text())
        self._canvas.set_font_style(self._font_spin.value(), self._color_hex)

    # -- Collect fields ────────────────────────────────────────────────────────

    def _collect_lines(self) -> list:
        return [f.text().strip()
                for f in (self._name_f, self._title_f, self._date_f, self._custom_f)
                if f.text().strip()]

    def _get_frequency(self) -> str:
        if self._freq_first.isChecked():  return FREQ_FIRST
        if self._freq_last.isChecked():   return FREQ_LAST
        return FREQ_ALL

    def _get_custom_pages(self) -> str:
        if self._freq_custom.isChecked():
            return self._custom_pages_f.text().strip()
        return ""

    # -- Apply ─────────────────────────────────────────────────────────────────

    def _current_fields(self) -> dict:
        return {
            "full_name": self._name_f.text().strip(),
            "title":     self._title_f.text().strip(),
            "date":      self._date_f.text().strip(),
            "custom":    self._custom_f.text().strip(),
        }

    def _save_named_profile(self) -> None:
        """Save current fields under the typed profile name immediately."""
        pn = self._prof_name_f.text().strip()
        if not pn:
            self._status.setText("Enter a profile name first.")
            return
        self._profiles.save_profile(pn, self._current_fields())
        self._refresh_profiles()
        # Select the just-saved profile in the dropdown
        idx = self._profile_combo.findText(pn)
        if idx >= 0:
            self._profile_combo.setCurrentIndex(idx)
        self._status.setText(f'Profile "{pn}" saved.')

    def _load_last_used(self) -> None:
        """Pre-fill fields from the auto-saved last-used profile."""
        d = self._profiles.get("_last_used_")
        if not d:
            return
        self._name_f.setText(d.get("full_name", ""))
        self._title_f.setText(d.get("title", ""))
        self._date_f.setText(d.get("date", ""))
        self._custom_f.setText(d.get("custom", ""))

    def _apply(self) -> None:
        lines = self._collect_lines()
        if not lines and not self._sig_bytes:
            self._status.setText(
                "Add at least one text field or a signature before applying."
            )
            return

        if not self._output_full:
            self._status.setText("Choose an output file path first.")
            return

        # Always auto-save as "last used" so fields reappear next session
        self._profiles.save_profile("_last_used_", self._current_fields())

        self._set_busy(True)
        self._status.setText("Applying annotation...")

        # Build per-field text items: (text, x_frac, y_frac)
        field_texts = [
            self._name_f.text().strip(),
            self._title_f.text().strip(),
            self._date_f.text().strip(),
            self._custom_f.text().strip(),
        ]
        text_items = [
            (text, *self._canvas.get_position(i))
            for i, text in enumerate(field_texts)
            if text
        ]

        sx, sy = self._canvas.get_position(4)

        self._worker = _AnnotateWorker(
            annotator    = self._annotator,
            input_path   = self._input_path,
            output_path  = self._output_full,
            text_items   = text_items,
            frequency    = self._get_frequency(),
            custom_pages = self._get_custom_pages(),
            font_size    = self._font_spin.value(),
            color        = self._color_hex,
            sig_bytes    = self._sig_bytes,
            sig_pos_x    = sx,
            sig_pos_y    = sy,
            sig_scale    = 0.25,
        )
        self._worker.progress_changed.connect(self._progress.setValue)
        self._worker.annotate_done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, success: bool, msg: str) -> None:
        self._set_busy(False)
        if success:
            self.output_path = self._output_full
            self.accept()
        else:
            self._status.setText(msg)
            self._progress.setValue(0)

    def _set_busy(self, busy: bool) -> None:
        self._apply_btn.setEnabled(not busy)
        self._progress.setVisible(busy)
        for w in (self._name_f, self._title_f, self._date_f,
                  self._custom_f, self._font_spin, self._color_btn):
            w.setEnabled(not busy)
