"""
PDF Splitter engine.
Splits a PDF into multiple output files using pypdf.
Three modes:
  'all'     – every page becomes its own PDF
  'ranges'  – user-supplied page-range string e.g. "1-3, 4-7, 8"
  'every_n' – split into chunks of N pages
"""
import os
from typing import Callable, List, Optional, Tuple

from pypdf import PdfReader, PdfWriter

from .merger import _secure_file


def _parse_ranges(ranges_str: str, total: int) -> List[Tuple[int, int]]:
    """
    Parse "1-3, 4-7, 8" (1-indexed) into a list of (start, end) 0-indexed
    inclusive tuples.  Skips invalid or out-of-range tokens.
    """
    result: List[Tuple[int, int]] = []
    for part in ranges_str.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            halves = part.split("-", 1)
            try:
                a, b = int(halves[0]) - 1, int(halves[1]) - 1
                a = max(0, min(a, total - 1))
                b = max(0, min(b, total - 1))
                if a <= b:
                    result.append((a, b))
            except ValueError:
                pass
        else:
            try:
                n = int(part) - 1
                if 0 <= n < total:
                    result.append((n, n))
            except ValueError:
                pass
    return result


def _stem(path: str) -> str:
    base = os.path.basename(path)
    root, _ = os.path.splitext(base)
    return root


def _write_chunk(reader: PdfReader, start: int, end: int,
                 out_path: str) -> None:
    writer = PdfWriter()
    for i in range(start, end + 1):
        writer.add_page(reader.pages[i])
    with open(out_path, "wb") as f:
        writer.write(f)
    _secure_file(out_path)


class PDFSplitter:
    """Splits a PDF into multiple output files."""

    def split(
        self,
        input_path: str,
        output_dir: str,
        mode: str,                            # 'all' | 'ranges' | 'every_n'
        ranges_str: str = "",
        every_n: int = 1,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Split input_path according to mode and write output files to output_dir.
        Returns (success, message).
        """
        if not os.path.isfile(input_path):
            return False, "Input PDF not found."
        if not output_dir:
            return False, "No output folder specified."
        os.makedirs(output_dir, exist_ok=True)

        try:
            reader = PdfReader(input_path)
            total  = len(reader.pages)
            stem   = _stem(input_path)

            if mode == "all":
                chunks = [(i, i) for i in range(total)]
            elif mode == "ranges":
                chunks = _parse_ranges(ranges_str, total)
                if not chunks:
                    return False, "No valid page ranges found. Use format: 1-3, 4-7"
            elif mode == "every_n":
                n      = max(1, every_n)
                chunks = [(i, min(i + n - 1, total - 1))
                          for i in range(0, total, n)]
            else:
                return False, f"Unknown split mode: {mode}"

            count = len(chunks)
            for idx, (start, end) in enumerate(chunks):
                if progress_callback:
                    progress_callback(int((idx / count) * 95))
                digits = max(3, len(str(count)))
                label  = str(idx + 1).zfill(digits)
                name   = f"{stem}_part_{label}.pdf"
                _write_chunk(reader, start, end,
                             os.path.join(output_dir, name))

            if progress_callback:
                progress_callback(100)

            return True, f"Split into {count} file(s) in: {os.path.basename(output_dir)}"

        except Exception as exc:
            return False, f"Split failed: {exc}"
