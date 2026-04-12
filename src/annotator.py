"""
PDF text annotation engine.
Stamps text items and an optional signature image onto PDF pages.
Position is expressed as (x_frac, y_frac) — fractions of page dimensions
representing the center of each annotation block, so the user can drag
annotations to any precise location.
"""
import os
import tempfile
from typing import Callable, List, Optional, Set, Tuple

from .merger import _validate_output, _secure_file
from .watermark import FREQ_ALL, FREQ_ODD, FREQ_EVEN, FREQ_FIRST, FREQ_LAST

# Default position: bottom-right area
_DEFAULT_TEXT_X = 0.82
_DEFAULT_TEXT_Y = 0.88
_DEFAULT_SIG_X  = 0.50
_DEFAULT_SIG_Y  = 0.72


# -- Helpers ───────────────────────────────────────────────────────────────────

def _text_rect(page_rect, x_frac: float, y_frac: float,
               line_count: int, max_chars: int, font_size: int):
    """
    Return a fitz.Rect whose center sits at (x_frac, y_frac) of the page,
    sized to fit the given number of lines.
    """
    import fitz
    pw, ph = page_rect.width, page_rect.height
    block_w = min(max_chars * font_size * 0.56 + 16, pw * 0.45)
    block_h = line_count * font_size * 1.55 + 8
    x0 = pw * x_frac - block_w / 2
    y0 = ph * y_frac - block_h / 2
    margin = 4
    x0 = max(margin, min(x0, pw - block_w - margin))
    y0 = max(margin, min(y0, ph - block_h - margin))
    return fitz.Rect(x0, y0, x0 + block_w, y0 + block_h)


def _sig_rect(page_rect, x_frac: float, y_frac: float,
              scale: float, aspect: float):
    """Return fitz.Rect for the signature image centered at (x_frac, y_frac)."""
    import fitz
    pw, ph = page_rect.width, page_rect.height
    sig_w = pw * scale
    sig_h = sig_w / max(aspect, 0.01)
    x0 = pw * x_frac - sig_w / 2
    y0 = ph * y_frac - sig_h / 2
    margin = 4
    x0 = max(margin, min(x0, pw - sig_w - margin))
    y0 = max(margin, min(y0, ph - sig_h - margin))
    return fitz.Rect(x0, y0, x0 + sig_w, y0 + sig_h)


def _applies_to(page_idx: int, total: int, frequency: str,
                custom_pages: Optional[Set[int]] = None) -> bool:
    if custom_pages is not None:
        return page_idx in custom_pages
    n = page_idx + 1
    return {
        FREQ_ALL:   True,
        FREQ_FIRST: page_idx == 0,
        FREQ_LAST:  page_idx == total - 1,
        FREQ_ODD:   n % 2 == 1,
        FREQ_EVEN:  n % 2 == 0,
    }.get(frequency, True)


def parse_custom_pages(pages_str: str, total: int) -> Set[int]:
    """
    Parse a page-range string (1-indexed) into a set of 0-indexed page numbers.
    Accepts: "1,3,5-7" → {0, 2, 4, 5, 6}
    Silently ignores invalid tokens or out-of-range numbers.
    """
    result: Set[int] = set()
    for part in pages_str.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            try:
                a, b = int(bounds[0]), int(bounds[1])
                for i in range(a, b + 1):
                    if 1 <= i <= total:
                        result.add(i - 1)
            except ValueError:
                pass
        else:
            try:
                n = int(part)
                if 1 <= n <= total:
                    result.add(n - 1)
            except ValueError:
                pass
    return result


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255.0, g / 255.0, b / 255.0


def _sig_aspect_from_bytes(sig_bytes: bytes) -> float:
    """Return width/height aspect ratio from raw PNG/JPG bytes."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(sig_bytes))
        w, h = img.size
        return w / max(h, 1)
    except Exception:
        return 3.5   # typical signature is wide


# -- Main class ────────────────────────────────────────────────────────────────

class PDFAnnotator:
    """
    Stamps text and/or a signature image onto PDF pages using PyMuPDF.
    Positions are given as (x_frac, y_frac) fractions of the page size,
    representing the center of each annotation block.
    """

    def apply(
        self,
        input_path: str,
        output_path: str,
        text_items: List[Tuple[str, float, float]],
        frequency: str = FREQ_ALL,
        custom_pages: str = "",          # e.g. "1,3,5-7"  (overrides frequency)
        font_size: int = 11,
        color: str = "#333333",
        sig_bytes: bytes = b"",          # PNG/JPG bytes of signature image
        sig_pos_x: float = _DEFAULT_SIG_X,
        sig_pos_y: float = _DEFAULT_SIG_Y,
        sig_scale: float = 0.25,         # fraction of page width
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply annotation to all applicable pages and write to output_path.
        text_items is a list of (text, x_frac, y_frac) — one entry per field,
        each independently positioned.
        Returns (success, message).
        """
        if not os.path.isfile(input_path):
            return False, "Input PDF not found."
        if not output_path or not output_path.strip():
            return False, "No output path specified."

        items    = [(t, x, y) for t, x, y in text_items if t.strip()]
        has_text = bool(items)
        has_sig  = bool(sig_bytes)
        if not has_text and not has_sig:
            return False, "No annotation content provided."

        rgb        = _hex_to_rgb(color)
        sig_aspect = _sig_aspect_from_bytes(sig_bytes) if has_sig else 3.5
        tmp_path: Optional[str] = None
        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."

        try:
            import fitz

            if progress_callback:
                progress_callback(5)

            doc   = fitz.open(input_path)
            total = len(doc)
            pages = parse_custom_pages(custom_pages, total) if custom_pages.strip() else None

            for i in range(total):
                if progress_callback:
                    progress_callback(int(5 + i / total * 82))
                if not _applies_to(i, total, frequency, pages):
                    continue

                page = doc[i]

                if has_text:
                    for text, tx, ty in items:
                        rect = _text_rect(page.rect, tx, ty, 1, len(text), font_size)
                        page.insert_textbox(rect, text, fontsize=font_size,
                                            color=rgb,
                                            align=fitz.TEXT_ALIGN_LEFT)

                if has_sig:
                    srect = _sig_rect(page.rect, sig_pos_x, sig_pos_y,
                                      sig_scale, sig_aspect)
                    page.insert_image(srect, stream=sig_bytes, overlay=True)

            if progress_callback:
                progress_callback(90)

            fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
            os.close(fd)
            doc.save(tmp_path, garbage=4, deflate=True)
            doc.close()

            if progress_callback:
                progress_callback(95)

            _validate_output(tmp_path)
            os.replace(tmp_path, output_path)
            tmp_path = None
            _secure_file(output_path)

            if progress_callback:
                progress_callback(100)

            return True, f"Saved: {os.path.basename(output_path)}"

        except Exception as exc:
            return False, f"Annotation failed: {exc}"

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
