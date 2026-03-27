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
# FAQ / Help content
# ---------------------------------------------------------------------------

_FAQ_DATA = [
    # ── Your Data, Your Privacy ─────────────────────────────────────────────
    {
        "section": "Your Data, Your Privacy",
        "items": [
            {
                "q": "Does this app upload my files to the internet?",
                "a": (
                    "Never. Every single operation — merging, splitting, compressing, "
                    "converting, watermarking, annotating — runs entirely on your device "
                    "using local libraries. No file, page, or byte is ever sent to a "
                    "server, cloud service, or third party.\n\n"
                    "You do not need an account, a licence key, or an internet connection "
                    "to use any feature."
                ),
            },
            {
                "q": "Is it safe to process confidential or sensitive documents?",
                "a": (
                    "Yes. Because nothing leaves your machine, confidential contracts, "
                    "financial records, medical reports, legal documents, and creative "
                    "work are all safe to process here.\n\n"
                    "Your organisation's data-protection policies are not affected — "
                    "there is no upload, no third-party processor, and no data retention "
                    "outside your own computer."
                ),
            },
            {
                "q": "What data does the app store locally?",
                "a": (
                    "Two lightweight JSON files are written to your home folder:\n\n"
                    "  ~/.pdf_merger_history.json — a log of past operations (filenames "
                    "and timestamps only, never file contents).\n\n"
                    "  ~/.pdf_merger_annotation_profiles.json — saved annotation "
                    "profiles (name, title, date fields you typed in).\n\n"
                    "Both files stay on your machine and can be deleted at any time."
                ),
            },
            {
                "q": "Does the app collect analytics or crash reports?",
                "a": (
                    "No. There is zero telemetry. The app has no network code at all — "
                    "it cannot phone home even if it wanted to."
                ),
            },
        ],
    },

    # ── Getting Started ─────────────────────────────────────────────────────
    {
        "section": "Getting Started",
        "items": [
            {
                "q": "What can this app do?",
                "a": (
                    "PDF Merger is an all-in-one offline PDF toolkit:\n\n"
                    "  Merge — combine multiple PDFs into one.\n"
                    "  Protect — add a password to any PDF.\n"
                    "  Peep — create a free-preview + locked-full pair.\n"
                    "  View — read any PDF inside the app.\n"
                    "  Compress — shrink PDF file size.\n"
                    "  Watermark — stamp an image on every page.\n"
                    "  Annotate / Sign — add text, a date, and a signature.\n"
                    "  Split — divide a PDF into multiple files.\n"
                    "  PDF to Word — export a PDF as an editable .docx.\n"
                    "  Word to PDF — convert a .docx to PDF.\n"
                    "  PDF to Image — export pages as PNG/JPEG/TIFF.\n"
                    "  Image to PDF — combine photos into a PDF."
                ),
            },
            {
                "q": "How do I merge PDFs?",
                "a": (
                    "1. Go to the Merge PDFs tab.\n"
                    "2. Click Add PDFs to pick individual files, or Add Folder to add "
                    "every PDF inside a folder.\n"
                    "3. Reorder files with the Up / Down buttons on the right, or use "
                    "the Sort dropdown.\n"
                    "4. Set the output file path in the Save Merged PDF As field.\n"
                    "5. Click Merge PDFs. A progress bar tracks the work.\n"
                    "6. When done you can open the result in the built-in viewer."
                ),
            },
            {
                "q": "How do I split a PDF?",
                "a": (
                    "1. Go to the Split PDF tab.\n"
                    "2. Browse to select the PDF you want to split.\n"
                    "3. Choose a split mode:\n"
                    "     Every page — one PDF per page.\n"
                    "     Custom ranges — enter ranges like  1-3, 4-7, 8  to create "
                    "specific groups.\n"
                    "     Every N pages — fixed-size chunks.\n"
                    "4. Choose an output folder.\n"
                    "5. Click Split PDF. After completion you can reveal the output "
                    "folder in your file manager."
                ),
            },
            {
                "q": "How do I compress a PDF?",
                "a": (
                    "1. Go to the Compress PDF tab.\n"
                    "2. Browse to select your PDF.\n"
                    "3. Choose a compression level:\n"
                    "     Light — lossless, fastest, 10-30% smaller.\n"
                    "     Medium — lossless, recommended, 20-50% smaller.\n"
                    "     High — lossy (images re-rendered), 40-80% smaller.\n"
                    "4. Set an output path.\n"
                    "5. Click Compress PDF. The result shows original vs. compressed size."
                ),
            },
            {
                "q": "How do I add a watermark?",
                "a": (
                    "1. Go to the Watermark tab.\n"
                    "2. Select a PDF and a PNG or JPG watermark image.\n"
                    "3. Use the 3x3 position grid to pick placement.\n"
                    "4. Adjust opacity (how see-through) and scale (how large).\n"
                    "5. Choose which pages to watermark with the Frequency option.\n"
                    "6. The live preview updates as you adjust settings.\n"
                    "7. Click Apply Watermark when satisfied."
                ),
            },
            {
                "q": "How do I annotate or sign a PDF?",
                "a": (
                    "1. Open a PDF in the View PDF tab.\n"
                    "2. Click the Annotate / Sign button.\n"
                    "3. Fill in any text fields (name, title, date, custom text).\n"
                    "4. Optionally add a signature by drawing with your mouse/trackpad "
                    "or importing a PNG/JPG image.\n"
                    "5. Drag the T (text) and S (signature) handles in the canvas to "
                    "place annotations exactly where you need them.\n"
                    "6. Save a profile for re-use, then click Apply.\n"
                    "7. You can open the annotated PDF in the viewer when done."
                ),
            },
            {
                "q": "How do I convert a PDF to images?",
                "a": (
                    "1. Go to the PDF to Image tab.\n"
                    "2. Browse to select your PDF.\n"
                    "3. Choose the output folder.\n"
                    "4. Select format (PNG, JPEG, or TIFF), DPI, and optionally a page "
                    "range (e.g. 1, 3, 5-7).\n"
                    "5. Click Export Images. After completion you can reveal the folder."
                ),
            },
            {
                "q": "How do I combine images into a PDF?",
                "a": (
                    "1. Go to the Image to PDF tab.\n"
                    "2. Click Add Images to pick individual files, or Add Folder to add "
                    "every image inside a folder.\n"
                    "3. Use the Up / Down buttons to arrange the page order.\n"
                    "4. Remove unwanted images with Remove Selected or Clear All.\n"
                    "5. Set an output path and click Convert to PDF."
                ),
            },
            {
                "q": "How do I convert a PDF to a Word document?",
                "a": (
                    "1. Go to the PDF to Word tab.\n"
                    "2. Browse to select your PDF.\n"
                    "3. The output .docx path is filled automatically — change it if "
                    "needed.\n"
                    "4. Click Convert to Word. The process preserves text, tables, "
                    "and basic layout."
                ),
            },
            {
                "q": "How do I convert a Word document to PDF?",
                "a": (
                    "1. Go to the Word to PDF tab.\n"
                    "2. Browse to select a .docx or .doc file.\n"
                    "3. Set the output PDF path.\n"
                    "4. Click Convert to PDF.\n\n"
                    "Note: This feature requires Microsoft Word (macOS/Windows) or "
                    "LibreOffice (Linux) to be installed."
                ),
            },
        ],
    },

    # ── General ─────────────────────────────────────────────────────────────
    {
        "section": "General",
        "items": [
            {
                "q": "What is PDF Merger?",
                "a": (
                    "PDF Merger is a fully offline desktop PDF toolkit. It runs entirely "
                    "on your computer — no uploads, no accounts, no subscriptions. "
                    "Your files stay yours."
                ),
            },
            {
                "q": "What operating systems are supported?",
                "a": (
                    "macOS, Windows, and Linux are all fully supported. "
                    "The app adapts its fonts, colours, and dark/light theme to match "
                    "your platform automatically."
                ),
            },
            {
                "q": "Does the app need an internet connection?",
                "a": (
                    "No. Every feature works completely offline. The app never makes "
                    "any network requests."
                ),
            },
        ],
    },

    # ── Merge PDFs ──────────────────────────────────────────────────────────
    {
        "section": "Merge PDFs",
        "items": [
            {
                "q": "How many PDFs can I merge at once?",
                "a": "There is no built-in limit.",
            },
            {
                "q": "How do I change the order of files before merging?",
                "a": (
                    "Select a file in the list and use the Up / Down buttons on the right. "
                    "You can select multiple files to move them together. "
                    "The Sort dropdown offers A-Z and Z-A quick ordering."
                ),
            },
            {
                "q": "What happens if one of my PDFs is password-protected?",
                "a": (
                    "The app detects locked files before the merge starts and asks for "
                    "the password for each one individually. A wrong password causes "
                    "that file to be skipped; the rest are still merged."
                ),
            },
            {
                "q": "Can I merge PDFs from different folders?",
                "a": (
                    "Yes. Use Add PDFs to pick individual files, or Add Folder to add "
                    "every PDF inside a folder at once. Mix and match freely."
                ),
            },
            {
                "q": "Will the app warn me before overwriting an existing file?",
                "a": (
                    "Yes. A confirmation dialog appears if the output path already exists. "
                    "The merge will not proceed until you confirm or choose a different path."
                ),
            },
            {
                "q": "Can I open the merged PDF immediately after?",
                "a": (
                    "Yes. After a successful merge a dialog offers to open the result "
                    "in the built-in PDF Viewer so you can review it right away."
                ),
            },
        ],
    },

    # ── Protect PDF ─────────────────────────────────────────────────────────
    {
        "section": "Protect PDF",
        "items": [
            {
                "q": "What kind of encryption is applied?",
                "a": (
                    "pypdf applies 128-bit RC4 encryption — the standard PDF password "
                    "protection format, compatible with Adobe Acrobat and most PDF readers."
                ),
            },
            {
                "q": "Can I password-protect the merged output right after merging?",
                "a": (
                    "Yes. After a successful merge the app offers to add a password to "
                    "the output."
                ),
            },
            {
                "q": "What happens if I forget the password?",
                "a": (
                    "There is no recovery option. Store the password somewhere safe. "
                    "The encryption is designed to make the file unreadable without it."
                ),
            },
        ],
    },

    # ── Peep ────────────────────────────────────────────────────────────────
    {
        "section": "Peep",
        "items": [
            {
                "q": "What is Peep?",
                "a": (
                    "Peep creates two files from one PDF: a freely viewable preview "
                    "containing the first N pages, and a full password-protected version "
                    "with all pages. Readers get a genuine preview before deciding "
                    "whether to unlock the full content."
                ),
            },
            {
                "q": "What are the two files it creates?",
                "a": (
                    "A _peep_preview.pdf (no password, first N pages only) and a "
                    "_peep_full.pdf (all pages, password-protected). Both are saved "
                    "alongside your source PDF and named automatically."
                ),
            },
            {
                "q": "Can I share the preview file freely?",
                "a": (
                    "Yes. The preview has no password and opens in any PDF reader. "
                    "Only the full file requires the password you set."
                ),
            },
        ],
    },

    # ── View PDF ────────────────────────────────────────────────────────────
    {
        "section": "View PDF",
        "items": [
            {
                "q": "What is the View PDF tab?",
                "a": (
                    "An in-app PDF viewer. Regular PDFs open fully with no restrictions. "
                    "PDFs created with Peep show only the free pages and lock the rest "
                    "until the correct password is entered."
                ),
            },
            {
                "q": "Can I open the result of any operation in the viewer?",
                "a": (
                    "Yes. After every operation that produces a PDF output, the app "
                    "offers to open the result in the built-in viewer so you can "
                    "review it immediately."
                ),
            },
            {
                "q": "Can I annotate a PDF from the viewer?",
                "a": (
                    "Yes. Once a PDF is open, click the Annotate / Sign button to "
                    "open the annotation dialog."
                ),
            },
        ],
    },

    # ── Compress PDF ────────────────────────────────────────────────────────
    {
        "section": "Compress PDF",
        "items": [
            {
                "q": "What compression levels are available?",
                "a": (
                    "Light (lossless, 10-30% reduction), Medium (lossless with image "
                    "deflation, 20-50% reduction), and High (page re-rendering at "
                    "120 DPI JPEG 80, 40-80% reduction). Light and Medium are fully "
                    "lossless. High is lossy but produces the smallest files."
                ),
            },
            {
                "q": "Will compression affect text quality?",
                "a": (
                    "Light and Medium are completely lossless — text, images, and "
                    "fonts are unchanged. High re-renders each page as a JPEG image, "
                    "so text becomes part of the image and is no longer selectable, "
                    "though it stays clearly readable."
                ),
            },
            {
                "q": "Which level should I choose?",
                "a": (
                    "Medium is the best default for most documents. Use Light for "
                    "guaranteed zero quality change. Use High only for image-heavy "
                    "PDFs where file size is the top priority."
                ),
            },
        ],
    },

    # ── Watermark ───────────────────────────────────────────────────────────
    {
        "section": "Watermark",
        "items": [
            {
                "q": "What image formats are supported?",
                "a": (
                    "PNG and JPG are both supported. PNG images with a transparent "
                    "background work best. JPG images have no transparency channel, "
                    "so reduce the opacity to avoid a solid rectangle."
                ),
            },
            {
                "q": "How does the live preview work?",
                "a": (
                    "Once a PDF and watermark image are selected, a preview renders "
                    "automatically whenever you change position, opacity, scale, or "
                    "frequency. Use the < and > buttons to step through pages."
                ),
            },
            {
                "q": "Does watermarking alter the original PDF?",
                "a": (
                    "No. The app writes the watermarked copy to a new file. The "
                    "original is never modified."
                ),
            },
        ],
    },

    # ── Annotate / Sign ─────────────────────────────────────────────────────
    {
        "section": "Annotate / Sign",
        "items": [
            {
                "q": "What can I add with the Annotate feature?",
                "a": (
                    "You can stamp any combination of text lines (name, title, date, "
                    "custom text) and a signature image onto a PDF. Both the text block "
                    "and signature can be dragged anywhere on the page."
                ),
            },
            {
                "q": "How do I add a signature?",
                "a": (
                    "Click Draw Signature to open the signature pad and sign with your "
                    "mouse or trackpad, just like on a tablet. Alternatively, click "
                    "Import Image to use a PNG or JPG of your existing signature."
                ),
            },
            {
                "q": "Can I save my details so I don't retype them every time?",
                "a": (
                    "Yes. Type a profile name and click Save Profile. Next time you open "
                    "the dialog, select the profile from the dropdown. Your last-used "
                    "details are also auto-filled automatically."
                ),
            },
            {
                "q": "Can I apply annotations to specific pages only?",
                "a": (
                    "Yes. In the Apply To dropdown choose Custom pages and enter a "
                    "page range such as  1, 3, 5-7. You can also choose All pages, "
                    "First page only, Last page only, Odd pages, or Even pages."
                ),
            },
            {
                "q": "Is the original PDF modified?",
                "a": (
                    "No. The annotation is written to a new output file. Your original "
                    "PDF is never changed."
                ),
            },
        ],
    },

    # ── Split PDF ───────────────────────────────────────────────────────────
    {
        "section": "Split PDF",
        "items": [
            {
                "q": "What split modes are available?",
                "a": (
                    "Every page — extracts each page into its own PDF.\n"
                    "Custom ranges — you specify groups like  1-3, 4-7, 8  and each "
                    "group becomes one output file.\n"
                    "Every N pages — splits into fixed-size chunks of N pages."
                ),
            },
            {
                "q": "Where are the split files saved?",
                "a": (
                    "All output files go into the folder you choose. They are named "
                    "automatically using the source filename plus a part number, "
                    "e.g. report_part_001.pdf, report_part_002.pdf."
                ),
            },
            {
                "q": "Can I view the output folder when done?",
                "a": (
                    "Yes. After a successful split you are offered the option to reveal "
                    "the output folder in Finder (macOS), File Explorer (Windows), or "
                    "your file manager (Linux)."
                ),
            },
        ],
    },

    # ── PDF to Word ─────────────────────────────────────────────────────────
    {
        "section": "PDF to Word",
        "items": [
            {
                "q": "How accurate is the PDF to Word conversion?",
                "a": (
                    "Conversion quality depends on the PDF structure. Text-based PDFs "
                    "with clear layouts convert very well. Scanned image PDFs or highly "
                    "complex multi-column layouts may need manual clean-up in Word."
                ),
            },
            {
                "q": "What library is used?",
                "a": (
                    "pdf2docx — an open-source Python library that converts PDF content "
                    "to .docx format without any external application."
                ),
            },
            {
                "q": "Do I need Microsoft Word installed?",
                "a": (
                    "No. The PDF to Word conversion is handled entirely by the pdf2docx "
                    "library and does not require Word."
                ),
            },
        ],
    },

    # ── Word to PDF ─────────────────────────────────────────────────────────
    {
        "section": "Word to PDF",
        "items": [
            {
                "q": "Does Word to PDF require an internet connection?",
                "a": (
                    "No. The conversion runs entirely on your machine using docx2pdf, "
                    "which calls the locally-installed Word or LibreOffice."
                ),
            },
            {
                "q": "What applications are required?",
                "a": (
                    "LibreOffice (free, libreoffice.org) works on macOS, Windows, "
                    "and Linux — no Microsoft Office needed.\n\n"
                    "Microsoft Word also works on macOS and Windows if already installed.\n\n"
                    "The app tries LibreOffice first, then falls back to Word automatically."
                ),
            },
            {
                "q": "I selected a .pdf file and got an error — why?",
                "a": (
                    "This tab converts Word documents (.docx / .doc) to PDF — not PDFs "
                    "to Word. If you want to convert a PDF to Word, use the "
                    "PDF to Word tab instead."
                ),
            },
        ],
    },

    # ── PDF to Image ────────────────────────────────────────────────────────
    {
        "section": "PDF to Image",
        "items": [
            {
                "q": "What image formats can I export?",
                "a": "PNG (lossless, best quality), JPEG (compressed, smaller), and TIFF.",
            },
            {
                "q": "What DPI should I use?",
                "a": (
                    "150 DPI is the default and gives clear images for screen use. "
                    "Use 300 DPI for print-quality output. Higher DPI means larger files "
                    "and longer processing time."
                ),
            },
            {
                "q": "Can I export specific pages only?",
                "a": (
                    "Yes. Enter a page range in the Pages field, e.g.  1, 3, 5-7. "
                    "Leave it blank to export all pages."
                ),
            },
        ],
    },

    # ── Image to PDF ────────────────────────────────────────────────────────
    {
        "section": "Image to PDF",
        "items": [
            {
                "q": "What image formats are supported as input?",
                "a": "PNG, JPEG, TIFF, BMP, and GIF are all accepted.",
            },
            {
                "q": "Can I control the page order?",
                "a": (
                    "Yes. Select an image in the list and use the Up / Down buttons to "
                    "reorder it. You can also add an entire folder of images at once."
                ),
            },
            {
                "q": "Can I add images from multiple folders?",
                "a": (
                    "Yes. Click Add Images to pick individual files, or Add Folder to "
                    "add every image in a folder. Repeat as many times as needed."
                ),
            },
        ],
    },

    # ── History ─────────────────────────────────────────────────────────────
    {
        "section": "History",
        "items": [
            {
                "q": "What does the History tab track?",
                "a": (
                    "Every operation — merge, protect, peep, compress, watermark, "
                    "annotate, split, and all conversions — is recorded with the output "
                    "filename, date, time, and whether it was password-protected."
                ),
            },
            {
                "q": "Where is the history stored?",
                "a": (
                    "Locally on your computer only, in ~/.pdf_merger_history.json. "
                    "It is never sent anywhere."
                ),
            },
        ],
    },

    # ── Troubleshooting ─────────────────────────────────────────────────────
    {
        "section": "Troubleshooting",
        "items": [
            {
                "q": "A file was skipped during merge — why?",
                "a": (
                    "The file may be corrupted, have an incompatible structure, or be "
                    "encrypted without a password provided. The result dialog lists every "
                    "skipped file and the reason."
                ),
            },
            {
                "q": "The progress bar stopped — is it frozen?",
                "a": (
                    "All operations run on a background thread so the UI stays responsive. "
                    "If the bar stops, a very large file is likely being processed. "
                    "Give it time before assuming something is wrong."
                ),
            },
            {
                "q": "Word to PDF fails even though Word is installed.",
                "a": (
                    "Make sure Microsoft Word is fully opened at least once so its "
                    "AppleScript (macOS) or COM (Windows) bridge is registered. "
                    "If the problem persists on macOS, check that Word has Automation "
                    "permission in System Settings > Privacy & Security > Automation."
                ),
            },
            {
                "q": "PDF to Word output looks wrong.",
                "a": (
                    "Complex PDFs — especially scanned documents, PDFs with unusual "
                    "fonts, or multi-column magazine-style layouts — may not convert "
                    "perfectly. The resulting .docx can be manually cleaned up in Word "
                    "or any compatible editor."
                ),
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

    inner = QWidget()
    inner.setObjectName("faqSearchInner")
    sb_row = QHBoxLayout(inner)
    sb_row.setContentsMargins(14, 10, 14, 10)
    sb_row.setSpacing(10)

    search_lbl = QLabel("Search Help:")
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
