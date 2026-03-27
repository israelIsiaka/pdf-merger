"""
PDF Compressor -- three-level compression engine.

Level 1  Light    Lossless stream compression + garbage collection.
                  Removes redundant objects; no quality change.
                  Typical reduction: 10-30 %

Level 2  Medium   Maximum lossless compression.
                  Deflates all streams, images, and fonts; full garbage
                  collection; linearises output.
                  Typical reduction: 20-50 %

Level 3  High     Page re-rendering at lower resolution (120 DPI, JPEG 80).
                  Images are noticeably compressed; text remains readable
                  but is no longer selectable.
                  Typical reduction: 40-80 % (image-heavy PDFs benefit most)

All levels write to a temp file first, validate the output, then atomically
replace the final path so partial writes never corrupt the destination.
"""

import os
import tempfile
from typing import Callable, Optional, Tuple

from .merger import _fmt_size, _validate_output, _secure_file


# Compression level constants
LEVEL_LIGHT  = 1
LEVEL_MEDIUM = 2
LEVEL_HIGH   = 3

LEVEL_LABELS = {
    LEVEL_LIGHT:  "Light",
    LEVEL_MEDIUM: "Medium",
    LEVEL_HIGH:   "High",
}

LEVEL_DESCRIPTIONS = {
    LEVEL_LIGHT: (
        "Removes unused data and compresses text streams. "
        "No quality change whatsoever."
    ),
    LEVEL_MEDIUM: (
        "Maximum lossless compression. Deflates all content including "
        "images and fonts. Best choice for most PDFs."
    ),
    LEVEL_HIGH: (
        "Re-renders every page at 120 DPI (JPEG 80). "
        "Produces the smallest file. Images are compressed but "
        "text stays readable. Note: text will not be selectable."
    ),
}

_HIGH_DPI        = 120
_HIGH_JPEG_QUAL  = 80


class PDFCompressor:
    """Handles PDF compression at three quality levels using PyMuPDF."""

    def compress(
        self,
        input_path: str,
        output_path: str,
        level: int = LEVEL_MEDIUM,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Compress input_path and write the result to output_path.
        Returns (success, message).
        """
        if not os.path.isfile(input_path):
            return False, "Input file not found."
        if not output_path or not output_path.strip():
            return False, "No output path specified."
        if level not in (LEVEL_LIGHT, LEVEL_MEDIUM, LEVEL_HIGH):
            return False, f"Invalid compression level: {level}."

        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        tmp_path   = None

        try:
            import fitz  # PyMuPDF

            original_size = os.path.getsize(input_path)
            if progress_callback:
                progress_callback(5)

            doc = fitz.open(input_path)
            if progress_callback:
                progress_callback(15)

            fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
            os.close(fd)

            if level == LEVEL_LIGHT:
                # Full garbage collection + compress text/font streams only.
                # Images are left untouched.
                doc.save(
                    tmp_path,
                    garbage=4,
                    deflate=True,
                    deflate_fonts=True,
                    clean=True,
                )
                if progress_callback:
                    progress_callback(85)

            elif level == LEVEL_MEDIUM:
                # Same as Light but also deflates image streams.
                doc.save(
                    tmp_path,
                    garbage=4,
                    deflate=True,
                    deflate_images=True,
                    deflate_fonts=True,
                    clean=True,
                )
                if progress_callback:
                    progress_callback(85)

            elif level == LEVEL_HIGH:
                doc.close()
                doc = None
                tmp_path = self._compress_high(
                    input_path, tmp_path, progress_callback
                )

            if doc is not None:
                doc.close()

            _validate_output(tmp_path)
            os.replace(tmp_path, output_path)
            tmp_path = None

            _secure_file(output_path)
            if progress_callback:
                progress_callback(100)

            new_size  = os.path.getsize(output_path)
            reduction = (1.0 - new_size / original_size) * 100 if original_size else 0.0

            label = LEVEL_LABELS[level]
            return True, (
                f"Compressed successfully ({label} level).\n\n"
                f"Original:   {_fmt_size(original_size)}\n"
                f"Compressed: {_fmt_size(new_size)}\n"
                f"Reduction:  {reduction:.1f}%"
            )

        except Exception as e:
            return False, f"Failed to compress PDF: {e}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # -- Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _compress_high(
        input_path: str,
        tmp_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> str:
        """
        Re-render every page as a JPEG image at _HIGH_DPI / _HIGH_JPEG_QUAL
        into a new PDF.  Returns tmp_path (unchanged) so the caller can
        proceed with validation and atomic rename.
        """
        import fitz

        src = fitz.open(input_path)
        out = fitz.open()
        total = len(src)
        mat   = fitz.Matrix(_HIGH_DPI / 72.0, _HIGH_DPI / 72.0)

        for i, page in enumerate(src):
            if progress_callback:
                progress_callback(int(15 + (i / total) * 65))

            pix       = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("jpeg", jpg_quality=_HIGH_JPEG_QUAL)
            del pix                                           # free RGBA bitmap immediately
            new_page  = out.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=img_bytes)
            del img_bytes                                     # free JPEG bytes after insert

        src.close()

        out.save(
            tmp_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
        )
        out.close()

        if progress_callback:
            progress_callback(85)

        return tmp_path
