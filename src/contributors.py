"""
Contributors page widget for PDF Merger.

Usage:
    from .contributors import build_contributors_widget
    tab = build_contributors_widget(parent)
"""

import webbrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget, QFrame,
)

# ---------------------------------------------------------------------------
# Contributors data
# ---------------------------------------------------------------------------

_CONTRIBUTORS_DATA = [
    {
        "name": "Israeli Isiaka",
        "links": {
            "github": "https://github.com/israelIsiaka",
            "linkedin": "https://linkedin.com/in/israelisiaka",
        },
    },
]

# ---------------------------------------------------------------------------
# Contributor Card Widget
# ---------------------------------------------------------------------------

class _ContributorCard(QFrame):
    """A single contributor card with name and social links."""

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("contributorCard")
        self.setStyleSheet("""
            QFrame#contributorCard {
                background-color: #0d1220;
                border: 1px solid #1e2a42;
                border-radius: 10px;
                padding: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Name
        name_lbl = QLabel(data["name"])
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(name_lbl)

        # Social links
        links_layout = QHBoxLayout()
        links_layout.setContentsMargins(0, 0, 0, 0)
        links_layout.setSpacing(8)

        if "links" in data and data["links"]:
            for platform, url in data["links"].items():
                if url and url.strip():  # Only show if URL is provided
                    btn = QPushButton(platform.capitalize())
                    btn.setObjectName("socialLink")
                    btn.setFixedHeight(28)
                    btn.setStyleSheet("""
                        QPushButton#socialLink {
                            background-color: #4f7ef722;
                            color: #4f7ef7;
                            border: 1px solid #4f7ef744;
                            border-radius: 6px;
                            font-size: 9px;
                            font-weight: bold;
                            padding: 4px 10px;
                        }
                        QPushButton#socialLink:hover {
                            background-color: #4f7ef744;
                            border: 1px solid #4f7ef7;
                        }
                    """)
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.clicked.connect(lambda checked=False, u=url: webbrowser.open(u))
                    links_layout.addWidget(btn)

        links_layout.addStretch()
        layout.addLayout(links_layout)


# ---------------------------------------------------------------------------
# Contributors Widget
# ---------------------------------------------------------------------------

def build_contributors_widget(parent=None) -> QWidget:
    """Build and return the contributors widget."""
    widget = QWidget(parent)
    widget.setObjectName("tabPage")
    
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)

    # Title
    title = QLabel("Meet the Contributors")
    title_font = QFont()
    title_font.setPointSize(14)
    title_font.setBold(True)
    title.setFont(title_font)
    title.setStyleSheet("color: #e2e8f0;")
    layout.addWidget(title)

    # Description
    desc = QLabel(
        "PDF Merger is built with ❤️ by talented developers and designers. "
        "Thank you for using our software!"
    )
    desc.setWordWrap(True)
    desc.setStyleSheet("color: #94a3b8; font-size: 11px; margin-bottom: 16px;")
    layout.addWidget(desc)

    # Scroll area for contributor cards
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setStyleSheet("""
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        QScrollBar:vertical {
            background-color: transparent;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background-color: #475569;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #64748b;
        }
    """)

    scroll_content = QWidget()
    scroll_content.setStyleSheet("background-color: transparent;")
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setContentsMargins(0, 0, 0, 0)
    scroll_layout.setSpacing(12)

    # Add contributor cards
    for contributor in _CONTRIBUTORS_DATA:
        card = _ContributorCard(contributor)
        scroll_layout.addWidget(card)

    scroll_layout.addStretch()
    scroll.setWidget(scroll_content)
    layout.addWidget(scroll)

    return widget
