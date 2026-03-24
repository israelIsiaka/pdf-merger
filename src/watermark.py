"""
PDF Watermark engine.
Applies an image watermark to PDF pages at a configurable position, scale,
and opacity.  Uses PyMuPDF for PDF manipulation and Pillow for image
preprocessing (opacity channel).
"""
import io
import os
import tempfile
from typing import Callable, Optional, Tuple

from .merger import _validate_output, _secure_file


# -- Position constants ────────────────────────────────────────────────────────

POS_TOP_LEFT   = "top-left"
POS_TOP_CENTER = "top-center"
POS_TOP_RIGHT  = "top-right"
POS_MID_LEFT   = "middle-left"
POS_MID_CENTER = "middle-center"
POS_MID_RIGHT  = "middle-right"
POS_BOT_LEFT   = "bottom-left"
POS_BOT_CENTER = "bottom-center"
POS_BOT_RIGHT  = "bottom-right"

# 3x3 layout order for the position-picker grid widget
POSITION_GRID = [
    [POS_TOP_LEFT,  POS_TOP_CENTER,  POS_TOP_RIGHT],
    [POS_MID_LEFT,  POS_MID_CENTER,  POS_MID_RIGHT],
    [POS_BOT_LEFT,  POS_BOT_CENTER,  POS_BOT_RIGHT],
]

POSITION_LABELS = {
    POS_TOP_LEFT:   "Top Left",
    POS_TOP_CENTER: "Top Center",
    POS_TOP_RIGHT:  "Top Right",
    POS_MID_LEFT:   "Middle Left",
    POS_MID_CENTER: "Center",
    POS_MID_RIGHT:  "Middle Right",
    POS_BOT_LEFT:   "Bottom Left",
    POS_BOT_CENTER: "Bottom Center",
    POS_BOT_RIGHT:  "Bottom Right",
}


# -- Frequency constants ───────────────────────────────────────────────────────

FREQ_ALL   = "all"
FREQ_ODD   = "odd"
FREQ_EVEN  = "even"
FREQ_FIRST = "first"
FREQ_LAST  = "last"

FREQ_LABELS = {
    FREQ_ALL:   "All Pages",
    FREQ_ODD:   "Odd Pages Only",
    FREQ_EVEN:  "Even Pages Only",
    FREQ_FIRST: "First Page Only",
    FREQ_LAST:  "Last Page Only",
}


# -- Internal helpers ──────────────────────────────────────────────────────────

def _image_bytes_with_opacity(image_path: str, opacity: float) -> bytes:
    """Return PNG bytes of image_path with opacity (0.0–1.0) applied to alpha."""
    from PIL import Image
    img = Image.open(image_path).convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda x: int(x * opacity))
    img.putalpha(a)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _image_aspect(image_path: str) -> float:
    """Return the width/height aspect ratio of the image."""
    from PIL import Image
    with Image.open(image_path) as img:
        w, h = img.size
        return w / h if h > 0 else 1.0


def _wm_rect(page_rect, scale: float, aspect: float, position: str):
    """Return the fitz.Rect for placing the watermark on the given page."""
    import fitz
    pw, ph = page_rect.width, page_rect.height
    wm_w   = pw * scale
    wm_h   = wm_w / aspect
    margin = pw * 0.04

    x0 = (margin                 if "left"   in position else
          pw - wm_w - margin     if "right"  in position else
          (pw - wm_w) / 2)

    y0 = (margin                 if "top"    in position else
          ph - wm_h - margin     if "bottom" in position else
          (ph - wm_h) / 2)

    return fitz.Rect(x0, y0, x0 + wm_w, y0 + wm_h)


def _applies_to(page_index: int, total: int, frequency: str) -> bool:
    n = page_index + 1
    return {
        FREQ_ALL:   True,
        FREQ_ODD:   n % 2 == 1,
        FREQ_EVEN:  n % 2 == 0,
        FREQ_FIRST: page_index == 0,
        FREQ_LAST:  page_index == total - 1,
    }.get(frequency, True)


# -- Main class ────────────────────────────────────────────────────────────────

class PDFWatermarker:
    """Applies image watermarks to PDF pages using PyMuPDF and Pillow."""

    def apply(
        self,
        input_path: str,
        output_path: str,
        image_path: str,
        position: str = POS_MID_CENTER,
        frequency: str = FREQ_ALL,
        scale: float = 0.30,
        opacity: float = 0.50,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply a watermark to every applicable page of input_path and write
        the result to output_path.

        scale:   fraction of page width occupied by the watermark (0.05–1.0).
        opacity: watermark transparency (0.0 = invisible, 1.0 = opaque).

        Writes to a temp file first, validates the output, then atomically
        replaces the final path.  Sets owner-only permissions on success.
        """
        if not os.path.isfile(input_path):
            return False, "Input PDF not found."
        if not os.path.isfile(image_path):
            return False, "Watermark image not found."
        if not output_path or not output_path.strip():
            return False, "No output path specified."

        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        tmp_path   = None

        try:
            import fitz

            if progress_callback: progress_callback(5)
            img_bytes = _image_bytes_with_opacity(image_path, opacity)
            aspect    = _image_aspect(image_path)
            if progress_callback: progress_callback(10)

            doc   = fitz.open(input_path)
            total = len(doc)

            for i, page in enumerate(doc):
                if _applies_to(i, total, frequency):
                    rect = _wm_rect(page.rect, scale, aspect, position)
                    page.insert_image(rect, stream=img_bytes, overlay=True)
                if progress_callback:
                    progress_callback(int(10 + (i + 1) / total * 75))

            fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
            os.close(fd)
            doc.save(tmp_path, garbage=3, deflate=True)
            doc.close()

            if progress_callback: progress_callback(90)
            _validate_output(tmp_path)
            os.replace(tmp_path, output_path)
            tmp_path = None
            _secure_file(output_path)
            if progress_callback: progress_callback(100)

            return True, f"Watermark applied. Saved as: {os.path.basename(output_path)}"

        except ImportError:
            return False, "Pillow is required for watermarking. Run: pip install Pillow"
        except Exception as e:
            return False, f"Failed to apply watermark: {e}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def render_preview(
        self,
        pdf_path: str,
        image_path: str,
        position: str,
        scale: float,
        opacity: float,
        page_index: int = 0,
        frequency: str = FREQ_ALL,
        dpi: int = 100,
    ) -> Optional[object]:
        """
        Render one page of pdf_path with the watermark applied in-memory.
        Respects frequency — if this page would not receive the watermark when
        applying for real, the preview renders it without the watermark too.
        No file is written to disk.  Returns a QImage, or None on failure.
        """
        try:
            import fitz
            from PyQt6.QtGui import QImage

            src = fitz.open(pdf_path)
            total = len(src)
            if page_index >= total:
                page_index = 0

            # Copy the single target page into a temporary in-memory document
            tmp = fitz.open()
            tmp.insert_pdf(src, from_page=page_index, to_page=page_index)
            src.close()

            page = tmp[0]

            # Only overlay the watermark if this page would receive it
            if _applies_to(page_index, total, frequency):
                img_bytes = _image_bytes_with_opacity(image_path, opacity)
                aspect    = _image_aspect(image_path)
                page.insert_image(_wm_rect(page.rect, scale, aspect, position),
                                  stream=img_bytes, overlay=True)

            mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            tmp.close()

            qimg = QImage(
                bytes(pix.samples),
                pix.width, pix.height, pix.stride,
                QImage.Format.Format_RGB888,
            )
            return qimg.copy()

        except Exception:
            return None
