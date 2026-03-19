"""
PDF Merger core logic.
Handles PDF merging operations with error handling.
"""
import datetime
import os
from collections import Counter
from typing import Callable, Dict, List, Optional, Tuple

from pypdf import PdfWriter


# -- file-info helpers ─────────────────────────────────────────────────────────

def _fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 ** 3:
        return f"{b / 1024 ** 2:.1f} MB"
    return f"{b / 1024 ** 3:.1f} GB"


def _fmt_date(ts: float) -> str:
    if not ts:
        return "-"
    return datetime.datetime.fromtimestamp(ts).strftime("%b %d, %Y %I:%M %p")


# -- main class ────────────────────────────────────────────────────────────────

class PDFMerger:
    """Handles PDF merging operations."""

    def __init__(self):
        self.pdf_files: List[str] = []

    def add_file(self, filepath: str) -> bool:
        if filepath not in self.pdf_files and os.path.isfile(filepath):
            self.pdf_files.append(filepath)
            return True
        return False

    def add_files(self, filepaths: List[str]) -> int:
        return sum(1 for fp in filepaths if self.add_file(fp))

    def add_folder(self, folder_path: str) -> int:
        if not os.path.isdir(folder_path):
            return 0
        added = 0
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                if self.add_file(os.path.join(folder_path, filename)):
                    added += 1
        return added

    def remove_file(self, index: int) -> bool:
        if 0 <= index < len(self.pdf_files):
            self.pdf_files.pop(index)
            return True
        return False

    def move_file_up(self, index: int) -> bool:
        if 0 < index < len(self.pdf_files):
            self.pdf_files[index - 1], self.pdf_files[index] = (
                self.pdf_files[index], self.pdf_files[index - 1]
            )
            return True
        return False

    def move_file_down(self, index: int) -> bool:
        if 0 <= index < len(self.pdf_files) - 1:
            self.pdf_files[index + 1], self.pdf_files[index] = (
                self.pdf_files[index], self.pdf_files[index + 1]
            )
            return True
        return False

    def clear(self) -> None:
        self.pdf_files.clear()

    def get_file_count(self) -> int:
        return len(self.pdf_files)

    def get_file_info(self) -> List[Dict[str, str]]:
        """Return display metadata for each file: display_name, size_str, created_str."""
        basenames = [os.path.basename(p) for p in self.pdf_files]
        counts = Counter(basenames)
        result = []
        for path, name in zip(self.pdf_files, basenames):
            if counts[name] > 1:
                parent = os.path.basename(os.path.dirname(path))
                display = f"{name}  [{parent}]"
            else:
                display = name
            try:
                stat = os.stat(path)
                size_bytes = stat.st_size
                ts = getattr(stat, "st_birthtime", stat.st_ctime)
            except OSError:
                size_bytes = 0
                ts = 0.0
            result.append({
                "display_name": display,
                "size_str": _fmt_size(size_bytes),
                "created_str": _fmt_date(ts),
            })
        return result

    def merge(
        self,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Merge PDF files to output_path.
        progress_callback receives int values 0-100.
        Returns (success: bool, message: str).
        """
        if not self.pdf_files:
            return False, "No PDF files to merge."
        if not output_path or not output_path.strip():
            return False, "No output path specified."

        try:
            writer = PdfWriter()
            errors = []
            total = len(self.pdf_files)

            for i, filepath in enumerate(self.pdf_files):
                try:
                    writer.append(filepath)
                except Exception as e:
                    errors.append((os.path.basename(filepath), str(e)))
                if progress_callback:
                    progress_callback(int((i + 1) / total * 90))

            if len(writer.pages) == 0:
                return False, "No pages could be read. All files may be corrupted or empty."

            with open(output_path, "wb") as f:
                writer.write(f)

            if progress_callback:
                progress_callback(100)

            successful = total - len(errors)
            message = f"Successfully merged {successful} of {total} files."
            if errors:
                details = "\n".join(f"  - {n}: {e}" for n, e in errors)
                message += f"\n\nSkipped {len(errors)} file(s):\n{details}"
            return True, message

        except Exception as e:
            return False, f"Failed to merge PDFs: {str(e)}"
