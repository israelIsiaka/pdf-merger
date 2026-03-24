"""
Collapsible, searchable FAQ widget for PDF Merger Help tab.

Usage:
    from .faq import build_faq_widget
    tab = build_faq_widget(parent)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

# ---------------------------------------------------------------------------
# FAQ content
# ---------------------------------------------------------------------------

_FAQ_DATA = [
    {
        "section": "General",
        "items": [
            {
                "q": "What is PDF Merger?",
                "a": "PDF Merger is a desktop app for combining, password-protecting, "
                     "previewing, compressing, and viewing PDFs, entirely offline.",
            },
            {
                "q": "Are my files safe and private?",
                "a": "Yes. Every operation runs entirely on your computer. Your PDFs are "
                     "never uploaded, transmitted, or shared with any server.",
            },
            {
                "q": "What operating systems are supported?",
                "a": "macOS, Windows, and Linux are all supported. The app automatically "
                     "adapts its fonts and colours to match your platform.",
            },
        ],
    },
    {
        "section": "Merge PDFs",
        "items": [
            {
                "q": "How many PDFs can I merge at once?",
                "a": "There is no limit.",
            },
            {
                "q": "How do I change the order of files before merging?",
                "a": "Select a file in the list and use the Up and Down buttons on the "
                     "right. You can select multiple files at once to move them together.",
            },
            {
                "q": "What happens if one of my PDFs is password-protected?",
                "a": "The app detects locked files before the merge starts and asks you "
                     "for the password for each one individually. A wrong password causes "
                     "that file to be skipped; the rest are still merged.",
            },
            {
                "q": "Can I merge PDFs from different folders?",
                "a": "Yes. Use Add PDFs to pick individual files, or Add Folder to add "
                     "every PDF inside a folder at once.",
            },
            {
                "q": "Will the app warn me before overwriting an existing file?",
                "a": "Yes. A confirmation dialog appears if the output path already exists. "
                     "The merge will not proceed until you confirm or choose a different path.",
            },
            {
                "q": "Can the output file be the same as one of the input files?",
                "a": "No. The app blocks this and shows an error. Overwriting a source "
                     "file mid-read would corrupt it. Choose a different output path.",
            },
        ],
    },
    {
        "section": "Protect PDF",
        "items": [
            {
                "q": "What kind of encryption is applied?",
                "a": "pypdf applies 128-bit RC4 encryption, the standard PDF password "
                     "protection format compatible with Adobe Acrobat and most PDF readers.",
            },
            {
                "q": "Can I password-protect the merged output right after merging?",
                "a": "Yes. After a successful merge the app asks if you want to add a "
                     "password to the output.",
            },
            {
                "q": "What happens if I forget the password?",
                "a": "There is no recovery option. Store the password somewhere safe. "
                     "The encryption is designed to make the file unreadable without it.",
            },
        ],
    },
    {
        "section": "Peep",
        "items": [
            {
                "q": "What is Peep?",
                "a": "Peep creates two files from one PDF: a freely viewable preview "
                     "containing the first N pages, and a full password-protected version "
                     "with all pages. Readers get a genuine preview before deciding "
                     "whether to unlock the full content.",
            },
            {
                "q": "What are the two files it creates?",
                "a": "A _peep_preview.pdf (no password, first N pages only) and a "
                     "_peep_full.pdf (all pages, password-protected). Both are saved "
                     "alongside your source PDF and named automatically.",
            },
            {
                "q": "How do I decide how many free pages to allow?",
                "a": "Set the Free View Pages number before clicking Create Peep Files. "
                     "A value of 1 to 3 pages is typical.",
            },
            {
                "q": "Can I share the preview file freely?",
                "a": "Yes. The preview has no password and opens in any PDF reader. "
                     "Only the full file requires the password you set.",
            },
        ],
    },
    {
        "section": "View PDF",
        "items": [
            {
                "q": "What is the View PDF tab?",
                "a": "An in-app PDF viewer. Regular PDFs open fully with no restrictions. "
                     "PDFs created with the Peep feature show only the free pages and lock "
                     "the rest until the correct password is entered.",
            },
            {
                "q": "How does the app recognise a peep-locked file?",
                "a": "When you create peep files, this app embeds a hidden marker in the "
                     "preview PDF. The viewer reads that marker automatically. Third-party "
                     "PDFs are never gated.",
            },
            {
                "q": "Can I unlock a peep PDF in the viewer?",
                "a": "Yes. Click Unlock Remaining Pages, enter the password you set when "
                     "creating the peep files, and all pages will be rendered from the "
                     "companion full PDF. Click Re-lock to return to the gated view.",
            },
        ],
    },
    {
        "section": "Compress PDF",
        "items": [
            {
                "q": "What compression levels are available?",
                "a": "Light (lossless, 10-30% reduction), Medium (lossless with image "
                     "deflation, 20-50% reduction), and High (page re-rendering at "
                     "120 DPI JPEG 80, 40-80% reduction). Light and Medium are fully "
                     "lossless. High is lossy.",
            },
            {
                "q": "Will compression affect text quality?",
                "a": "Light and Medium are completely lossless. High re-renders each page "
                     "as a JPEG image, so text becomes part of the image and is no longer "
                     "selectable, though it remains clearly readable.",
            },
            {
                "q": "Which level should I choose?",
                "a": "Medium is the best default. Use Light for guaranteed zero quality "
                     "change. Use High only for image-heavy PDFs where file size is the "
                     "top priority.",
            },
        ],
    },
    {
        "section": "Watermark",
        "items": [
            {
                "q": "What is the Watermark feature?",
                "a": "Watermark lets you overlay any PNG or JPG image on every page "
                     "(or a chosen subset) of a PDF. You control the position on the "
                     "page, how large the image appears relative to the page width, "
                     "and how transparent it is.",
            },
            {
                "q": "What image formats are supported?",
                "a": "PNG and JPG are both supported. PNG images with a transparent "
                     "background work best because the transparency is preserved when "
                     "the opacity is set to 100%. JPG images have no transparency "
                     "channel, so they will appear as a solid rectangle unless you "
                     "reduce the opacity.",
            },
            {
                "q": "What does opacity control?",
                "a": "Opacity sets how see-through the watermark is. At 100% the "
                     "watermark is fully visible and opaque. At 10% it is nearly "
                     "invisible. 40-60% is a typical range for a subtle but readable "
                     "watermark.",
            },
            {
                "q": "What does scale control?",
                "a": "Scale sets the width of the watermark as a percentage of the "
                     "page width. At 30% the watermark spans roughly one third of the "
                     "page. The height scales automatically to preserve the image's "
                     "aspect ratio.",
            },
            {
                "q": "What does frequency control?",
                "a": "Frequency lets you apply the watermark to All Pages, Odd Pages "
                     "Only, Even Pages Only, the First Page Only, or the Last Page "
                     "Only.",
            },
            {
                "q": "How does the interactive preview work?",
                "a": "Once a PDF and watermark image are both selected, a live preview "
                     "renders automatically whenever you change position, opacity, "
                     "scale, or frequency. Use the < and > buttons to step through "
                     "different pages of the document before applying.",
            },
            {
                "q": "Does watermarking alter the original PDF?",
                "a": "No. The app writes the watermarked copy to a new file. The "
                     "original PDF is never modified.",
            },
        ],
    },
    {
        "section": "History",
        "items": [
            {
                "q": "What does the History tab track?",
                "a": "Every merge, protect, peep, and compress operation is recorded with "
                     "the output filename, date, time, and whether it was password-protected.",
            },
            {
                "q": "Where is the history stored?",
                "a": "Locally on your computer only. It is never sent anywhere.",
            },
            {
                "q": "Is my history stored in the cloud?",
                "a": "No. The file is local only and never leaves your computer.",
            },
        ],
    },
    {
        "section": "Troubleshooting",
        "items": [
            {
                "q": "A file was skipped during merge — why?",
                "a": "The file may be corrupted, have an incompatible structure, or be "
                     "encrypted without a password provided. The result dialog lists every "
                     "skipped file and the reason.",
            },
            {
                "q": "The merged PDF has fewer pages than expected.",
                "a": "One or more input files were skipped (see above). Check the result "
                     "message for details.",
            },
            {
                "q": "The progress bar stopped — is it frozen?",
                "a": "All operations run on a background thread so the UI stays responsive. "
                     "If the bar stops, a very large file is likely being processed. "
                     "Give it time before assuming something is wrong.",
            },
            {
                "q": "Two input files share the same filename — how do I tell them apart?",
                "a": "The parent folder is shown in brackets next to the filename, "
                     "e.g. report.pdf  [folder-a].",
            },
            {
                "q": "What if a source file is moved or deleted after being added?",
                "a": "That file is skipped during the operation with a note in the result "
                     "message. Re-add it from its new location.",
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class _FAQItem(QWidget):
    """A single collapsible question / answer pair."""

    def __init__(self, question: str, answer: str, parent=None):
        super().__init__(parent)
        self._q_lower = question.lower()
        self._a_lower = answer.lower()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toggle = QPushButton("+  " + question)
        self._toggle.setObjectName("faqToggle")
        self._toggle.setCheckable(True)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setChecked(False)
        self._toggle.clicked.connect(self._on_toggle)
        layout.addWidget(self._toggle)

        self._body = QLabel(answer)
        self._body.setObjectName("faqAnswer")
        self._body.setWordWrap(True)
        self._body.setVisible(False)
        layout.addWidget(self._body)

    def _on_toggle(self, checked: bool) -> None:
        self._body.setVisible(checked)
        text = self._toggle.text()[3:]          # strip "+  " or "-  "
        self._toggle.setText(("-  " if checked else "+  ") + text)

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return q in self._q_lower or q in self._a_lower

    def apply_filter(self, query: str) -> bool:
        """Show/hide based on query. Returns True when visible."""
        visible = self.matches(query)
        self.setVisible(visible)
        return visible


class _FAQSection(QWidget):
    """A labelled group of _FAQItems."""

    def __init__(self, title: str, items: list[dict], parent=None):
        super().__init__(parent)
        self._items: list[_FAQItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 18, 0, 4)
        layout.setSpacing(0)

        hdr = QLabel(title)
        hdr.setObjectName("helpSection")
        layout.addWidget(hdr)
        layout.addSpacing(4)

        for data in items:
            item = _FAQItem(data["q"], data["a"], self)
            layout.addWidget(item)
            self._items.append(item)

    def apply_filter(self, query: str) -> bool:
        """
        Filter all child items. Hides the whole section when nothing matches.
        Returns True when at least one item is visible.
        """
        any_visible = any(item.apply_filter(query) for item in self._items)
        self.setVisible(any_visible)
        return any_visible


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_faq_widget(parent=None) -> QWidget:
    """Build and return the complete Help / FAQ tab widget."""
    outer = QWidget(parent)
    outer.setObjectName("tabPage")
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)

    # Search bar
    search_bar = QWidget()
    search_bar.setObjectName("faqSearchBar")
    sb_outer = QVBoxLayout(search_bar)
    sb_outer.setContentsMargins(28, 16, 28, 16)
    sb_outer.setSpacing(0)

    # Inner card that holds the label + input
    inner = QWidget()
    inner.setObjectName("faqSearchInner")
    sb_row = QHBoxLayout(inner)
    sb_row.setContentsMargins(14, 10, 14, 10)
    sb_row.setSpacing(10)

    search_lbl = QLabel("Search FAQ:")
    search_lbl.setObjectName("fieldLabel")
    sb_row.addWidget(search_lbl)

    search_edit = QLineEdit()
    search_edit.setObjectName("inputField")
    search_edit.setPlaceholderText("Type to search questions and answers...")
    search_edit.setClearButtonEnabled(True)
    sb_row.addWidget(search_edit)

    sb_outer.addWidget(inner)
    outer_layout.addWidget(search_bar)

    # Scrollable FAQ content
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setObjectName("helpScroll")
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)

    content = QWidget()
    content.setObjectName("tabPage")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(28, 4, 28, 32)
    content_layout.setSpacing(0)

    sections: list[_FAQSection] = []
    for sec_data in _FAQ_DATA:
        sec = _FAQSection(sec_data["section"], sec_data["items"], content)
        content_layout.addWidget(sec)
        sections.append(sec)

    content_layout.addStretch()
    scroll.setWidget(content)
    outer_layout.addWidget(scroll, 1)

    # Wire search
    def _on_search(text: str) -> None:
        for sec in sections:
            sec.apply_filter(text)

    search_edit.textChanged.connect(_on_search)

    return outer
