"""
Home view for PDF Merger.
Card-based dashboard with constellation background.
Cross-platform: macOS, Windows, Linux.
"""
from __future__ import annotations

import math
import random

from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QScrollArea, QVBoxLayout, QWidget,
)

# ── Tool definitions ──────────────────────────────────────────────────────────
# (name, description, icon_symbol, accent_color, tab_index)
TOOLS = [
    ("Merge PDFs",    "Combine multiple PDFs\ninto one document",         "+",  "#4f7ef7", 0),
    ("Protect PDF",   "Password-protect and\nencrypt your PDF",           "P",  "#eab308", 1),
    ("Peep PDF",      "Unlock limited free\npages without password",      "?",  "#a78bfa", 2),
    ("View PDF",      "Browse and preview\nPDF documents in-app",         "V",  "#22d3ee", 3),
    ("Compress PDF",  "Reduce file size while\npreserving quality",       "Z",  "#8b5cf6", 4),
    ("Watermark",     "Add text or image\nwatermarks to your PDF",        "W",  "#06b6d4", 5),
    ("Split PDF",     "Extract pages or split\nby custom ranges",         "/",  "#f59e0b", 6),
    ("PDF to Word",   "Convert PDF documents\nto editable Word files",    "W",  "#ef4444", 7),
    ("Word to PDF",   "Convert Word documents\nto PDF format",            "W",  "#3b82f6", 8),
    ("PDF to Images", "Export each page as\na high-quality image",        "I",  "#22c55e", 9),
    ("Images to PDF", "Combine images into\na single PDF document",       "I",  "#ec4899", 10),
    ("Sign / Annotate", "Add signatures, stamps\nand drawings to PDFs",  "S",  "#f97316", 11),
    ("History",       "View and re-open\nrecently processed files",       "H",  "#64748b", 12),
    ("Help / FAQ",    "Tips, shortcuts and\nfrequently asked questions",  "~",  "#475569", 13),
    ("Contributors",  "Meet the talented people\nbehind PDF Merger",       "♥",  "#ec4899", 14),
]

_BG_COLOR = "#080c18"   # constellation base — also used as solid fallback


# ── Constellation background ──────────────────────────────────────────────────

class _ConstellationBg(QWidget):
    """Animated starfield background widget. Paints its own solid dark bg."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Mouse events pass through so cards beneath remain clickable
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Ensure paintEvent is used (required on Windows)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        random.seed(42)
        self._stars: list[tuple[float, float, float]] = []
        self._gen_stars()

        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _gen_stars(self, n: int = 90):
        self._stars = [
            (random.random(), random.random(), random.uniform(1.0, 2.8))
            for _ in range(n)
        ]

    def _tick(self):
        self._phase = (self._phase + 0.5) % 360
        self.update()

    def showEvent(self, e):
        self._timer.start(50)
        super().showEvent(e)

    def hideEvent(self, e):
        self._timer.stop()
        super().hideEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            p.end()
            return

        # Solid dark background (works on all platforms)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#080c18"))
        grad.setColorAt(1.0, QColor("#060a12"))
        p.fillRect(0, 0, w, h, grad)

        pts = [(sx * w, sy * h, sz) for sx, sy, sz in self._stars]

        # Connection lines
        p.setPen(QPen(QColor(60, 120, 255, 28), 0.8))
        dist2 = (min(w, h) * 0.18) ** 2
        for i, (ax, ay, _) in enumerate(pts):
            for bx, by, _ in pts[i + 1:]:
                if (ax - bx) ** 2 + (ay - by) ** 2 < dist2:
                    p.drawLine(int(ax), int(ay), int(bx), int(by))

        # Stars with gentle pulse
        phase_rad = math.radians(self._phase)
        for ax, ay, sz in pts:
            pulse = 0.7 + 0.3 * math.sin(phase_rad + ax * 0.01)
            r = sz * pulse
            alpha = int(180 * pulse)
            p.setBrush(QBrush(QColor(120, 180, 255, alpha)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(ax - r), int(ay - r), int(r * 2), int(r * 2))

        p.end()


# ── Tool card ─────────────────────────────────────────────────────────────────

class ToolCard(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, name: str, desc: str, symbol: str,
                 color: str, tab_index: int, parent=None):
        super().__init__(parent)
        self._color     = color
        self._tab_index = tab_index

        self.setObjectName("toolCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(QSize(210, 148))
        # Required on Windows so QSS background-color is honoured
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build(name, desc, symbol, color)
        self._set_style(False)

    def _build(self, name: str, desc: str, symbol: str, color: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 14, 14)
        outer.setSpacing(10)

        # Top row: icon + arrow
        top = QHBoxLayout()
        top.setSpacing(0)

        icon_box = QLabel(symbol)
        icon_box.setFixedSize(QSize(46, 46))
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icon_box.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                border: 1px solid {color}55;
                border-radius: 10px;
                color: {color};
                font-size: 20px;
                font-weight: 800;
            }}
        """)
        top.addWidget(icon_box)
        top.addStretch()

        self._arrow = QLabel("->")
        self._arrow.setStyleSheet("color: #3a4560; font-size: 13px; background: transparent;")
        self._arrow.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        top.addWidget(self._arrow, 0, Qt.AlignmentFlag.AlignTop)

        outer.addLayout(top)

        title_lbl = QLabel(name)
        f = QFont(); f.setPointSize(11); f.setBold(True)
        title_lbl.setFont(f)
        title_lbl.setStyleSheet("color: #e2e8f0; background: transparent;")
        outer.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        outer.addWidget(desc_lbl)

        outer.addStretch()

    def _set_style(self, hovered: bool):
        if hovered:
            self.setStyleSheet(f"""
                QFrame#toolCard {{
                    background-color: {self._color}12;
                    border: 1px solid {self._color}88;
                    border-radius: 12px;
                }}
            """)
            self._arrow.setStyleSheet(
                f"color: {self._color}; font-size: 13px; background: transparent;")
        else:
            self.setStyleSheet("""
                QFrame#toolCard {
                    background-color: #0d1220;
                    border: 1px solid #1e2a42;
                    border-radius: 12px;
                }
            """)
            self._arrow.setStyleSheet(
                "color: #3a4560; font-size: 13px; background: transparent;")

    def enterEvent(self, e):
        self._set_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._set_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._tab_index)
        super().mousePressEvent(e)


# ── Home view ─────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    tool_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self._bg = _ConstellationBg(self)
        self._bg.lower()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        # Windows: prevent viewport painting its own background
        scroll.viewport().setAutoFillBackground(False)
        root.addWidget(scroll)

        inner = QWidget()
        inner.setAutoFillBackground(False)
        inner.setStyleSheet("background: transparent;")
        scroll.setWidget(inner)

        vl = QVBoxLayout(inner)
        vl.setContentsMargins(40, 40, 40, 40)
        vl.setSpacing(0)

        title = QLabel("PDF Merger")
        ft = QFont(); ft.setPointSize(28); ft.setBold(True)
        title.setFont(ft)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e2e8f0; background: transparent;")
        vl.addWidget(title)

        sub = QLabel("Professional PDF Processing Suite")
        fs = QFont(); fs.setPointSize(12)
        sub.setFont(fs)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            "color: #4f7ef7; background: transparent; margin-bottom: 6px;")
        vl.addWidget(sub)

        priv = QLabel(
            "100% offline  |  Your files never leave your device  "
            "|  No uploads  |  No accounts  |  No tracking"
        )
        fp = QFont(); fp.setPointSize(9)
        priv.setFont(fp)
        priv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        priv.setStyleSheet(
            "color: #22c55e; background: transparent; margin-bottom: 32px;")
        vl.addWidget(priv)

        section = QLabel("Select a tool to get started")
        fsec = QFont(); fsec.setPointSize(10)
        section.setFont(fsec)
        section.setStyleSheet(
            "color: #475569; background: transparent; margin-bottom: 20px;")
        vl.addWidget(section)

        grid_widget = QWidget()
        grid_widget.setAutoFillBackground(False)
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)

        cols = 4
        for i, (name, desc, sym, color, tab_idx) in enumerate(TOOLS):
            card = ToolCard(name, desc, sym, color, tab_idx)
            card.clicked.connect(self.tool_selected)
            grid.addWidget(card, i // cols, i % cols)

        vl.addWidget(grid_widget)
        vl.addStretch()

    def resizeEvent(self, e):
        self._bg.resize(e.size())
        super().resizeEvent(e)
