"""
PDF Merger core logic.
Handles PDF merging operations with error handling.
"""
import datetime
import os
import stat
import tempfile
from collections import Counter
from typing import Callable, Dict, List, Optional, Tuple

from pypdf import PdfReader, PdfWriter


# -- Security helpers ──────────────────────────────────────────────────────────

def _is_valid_pdf(filepath: str) -> bool:
    """Return True only if the file starts with the PDF magic bytes %PDF-."""
    try:
        with open(filepath, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def _validate_output(path: str) -> None:
    """
    Raise ValueError if the written file is missing, suspiciously small,
    or does not start with the PDF magic bytes.
    Called after every write to catch mid-write crashes or corrupt output.
    """
    if not os.path.exists(path):
        raise ValueError("Output file was not created.")
    if os.path.getsize(path) < 64:
        raise ValueError("Output file is too small to be a valid PDF.")
    with open(path, "rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError("Output file does not have a valid PDF header.")


def _secure_file(path: str) -> None:
    """
    Set file permissions to owner read/write only (600).
    Prevents other users on the same machine reading sensitive merged output.
    On Windows, os.chmod only affects the read-only flag so the effect is
    partial but still better than leaving default permissions.
    """
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


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
        """
        Add a file to the list. Returns False if it is a duplicate, does not
        exist, or fails the PDF header check (not a real PDF).
        """
        if filepath in self.pdf_files or not os.path.isfile(filepath):
            return False
        if not _is_valid_pdf(filepath):
            return False
        self.pdf_files.append(filepath)
        return True

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
                st = os.stat(path)
                size_bytes = st.st_size
                ts = getattr(st, "st_birthtime", st.st_ctime)
            except OSError:
                size_bytes = 0
                ts = 0.0
            result.append({
                "display_name": display,
                "size_str": _fmt_size(size_bytes),
                "created_str": _fmt_date(ts),
            })
        return result

    def check_encrypted_files(self) -> List[str]:
        """Return list of file paths that are password-protected."""
        encrypted = []
        for fp in self.pdf_files:
            try:
                reader = PdfReader(fp)
                if reader.is_encrypted:
                    encrypted.append(fp)
            except Exception:
                pass
        return encrypted

    def merge(
        self,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        passwords: Optional[Dict[str, str]] = None,
        output_password: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Merge PDF files to output_path.
        passwords: dict mapping filepath -> password for encrypted inputs.
        output_password: optional password to apply to the merged output.
        progress_callback receives int values 0-100.

        Writes to a temp file first, validates the output, then atomically
        replaces the final path. Sets owner-only file permissions on success.
        Returns (success: bool, message: str).
        """
        if not self.pdf_files:
            return False, "No PDF files to merge."
        if not output_path or not output_path.strip():
            return False, "No output path specified."

        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        tmp_path = None

        try:
            writer = PdfWriter()
            errors = []
            total = len(self.pdf_files)

            for i, filepath in enumerate(self.pdf_files):
                try:
                    pwd = (passwords or {}).get(filepath)
                    if pwd:
                        reader = PdfReader(filepath)
                        reader.decrypt(pwd)
                        writer.append(reader)
                        del pwd
                    else:
                        writer.append(filepath)
                except Exception as e:
                    errors.append((os.path.basename(filepath), str(e)))
                if progress_callback:
                    progress_callback(int((i + 1) / total * 85))

            if len(writer.pages) == 0:
                return False, "No pages could be read. All files may be corrupted or empty."

            if output_password:
                writer.encrypt(output_password)
                del output_password

            # Write to temp file in the same directory for atomic rename
            fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
            with os.fdopen(fd, "wb") as f:
                writer.write(f)

            if progress_callback:
                progress_callback(92)

            # Integrity check before committing
            _validate_output(tmp_path)

            # Atomic replace
            os.replace(tmp_path, output_path)
            tmp_path = None

            # Restrict permissions to owner only
            _secure_file(output_path)

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
        finally:
            # Clean up temp file if rename did not happen
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def protect_pdf(
        self, input_path: str, output_path: str, password: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply password protection to a PDF file.
        Writes to a temp file first, validates, then atomically replaces the
        final path. Handles in-place protection (input == output) safely.
        """
        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        tmp_path = None

        try:
            if progress_callback: progress_callback(10)
            reader = PdfReader(input_path)
            if progress_callback: progress_callback(40)

            writer = PdfWriter()
            writer.append(reader)
            if progress_callback: progress_callback(70)

            writer.encrypt(password)
            del password
            if progress_callback: progress_callback(85)

            fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
            with os.fdopen(fd, "wb") as f:
                writer.write(f)

            _validate_output(tmp_path)
            os.replace(tmp_path, output_path)
            tmp_path = None

            _secure_file(output_path)
            if progress_callback: progress_callback(100)
            return True, f"PDF protected and saved to: {output_path}"

        except Exception as e:
            return False, f"Failed to protect PDF: {str(e)}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def create_peep(
        self,
        input_path: str,
        free_page_count: int,
        output_preview: str,
        output_full: str,
        password: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Create a peep pair from input_path:
        - output_preview: first free_page_count pages, no password (freely shareable)
        - output_full: all pages, password-protected (full content)

        Both outputs are written to temp files first. If either fails, both
        temps are cleaned up so no partial output is left on disk.
        """
        preview_dir = os.path.dirname(os.path.abspath(output_preview)) or "."
        full_dir    = os.path.dirname(os.path.abspath(output_full)) or "."
        tmp_preview = None
        tmp_full    = None

        try:
            if progress_callback: progress_callback(5)
            reader = PdfReader(input_path)
            total = len(reader.pages)
            if total == 0:
                return False, "The selected PDF has no pages."

            free = min(max(1, free_page_count), total)
            if progress_callback: progress_callback(15)

            # Preview: first N pages, no encryption
            preview_writer = PdfWriter()
            for i in range(free):
                preview_writer.add_page(reader.pages[i])
            if progress_callback: progress_callback(35)

            fd, tmp_preview = tempfile.mkstemp(dir=preview_dir, suffix=".tmp")
            with os.fdopen(fd, "wb") as f:
                preview_writer.write(f)
            _validate_output(tmp_preview)
            if progress_callback: progress_callback(50)

            # Full: all pages, encrypted
            full_writer = PdfWriter()
            full_writer.append(reader)
            full_writer.encrypt(password)
            del password
            if progress_callback: progress_callback(75)

            fd, tmp_full = tempfile.mkstemp(dir=full_dir, suffix=".tmp")
            with os.fdopen(fd, "wb") as f:
                full_writer.write(f)
            _validate_output(tmp_full)
            if progress_callback: progress_callback(88)

            # Both valid — atomic replace both
            os.replace(tmp_preview, output_preview)
            tmp_preview = None
            os.replace(tmp_full, output_full)
            tmp_full = None

            _secure_file(output_preview)
            _secure_file(output_full)
            if progress_callback: progress_callback(100)

            locked = total - free
            return True, (
                f"Peep files created successfully.\n\n"
                f"Preview: {os.path.basename(output_preview)}\n"
                f"  {free} page(s) freely viewable\n\n"
                f"Full: {os.path.basename(output_full)}\n"
                f"  {total} page(s) total, {locked} page(s) password-protected"
            )

        except Exception as e:
            return False, f"Failed to create peep files: {str(e)}"
        finally:
            for tmp in (tmp_preview, tmp_full):
                if tmp and os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass
