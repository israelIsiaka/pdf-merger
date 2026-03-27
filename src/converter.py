"""
PDF conversion engines.
  PDF  -> Word  (.docx)  using pdf2docx
  Word -> PDF           using docx2pdf
  PDF  -> Images        using PyMuPDF
  Images -> PDF         using PyMuPDF / Pillow
"""
import os
import tempfile
from typing import Callable, List, Optional, Tuple

from .merger import _secure_file, _validate_output
from .annotator import parse_custom_pages     # page-range parser reuse


# ── PDF -> Word ────────────────────────────────────────────────────────────────

class PDFToWordConverter:

    def convert(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        if not os.path.isfile(input_path):
            return False, "Input PDF not found."
        if not output_path:
            return False, "No output path specified."

        try:
            from pdf2docx import Converter

            if progress_callback:
                progress_callback(5)

            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()

            if progress_callback:
                progress_callback(100)

            return True, f"Saved: {os.path.basename(output_path)}"

        except ImportError:
            return False, "pdf2docx is required. Run: pip install pdf2docx"
        except Exception as exc:
            return False, f"Conversion failed: {exc}"


# ── Word -> PDF ────────────────────────────────────────────────────────────────

class WordToPDFConverter:
    """
    Converts .docx / .doc to PDF without requiring Microsoft Office.

    Strategy (tried in order):
      1. LibreOffice headless  — free, cross-platform, no Office needed.
      2. docx2pdf              — uses Word (macOS/Windows) as a fallback.
    """

    # Known LibreOffice executable locations per platform
    _LO_PATHS = {
        "Darwin": [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/OpenOffice.app/Contents/MacOS/soffice",
        ],
        "Windows": [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ],
    }

    def convert(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        import platform as _plt
        import shutil
        import subprocess

        if not os.path.isfile(input_path):
            return False, "Input Word document not found."
        if not output_path:
            return False, "No output path specified."

        ext = os.path.splitext(input_path)[1].lower()
        if ext not in (".docx", ".doc"):
            return (
                False,
                f"The selected file is a '{ext or 'unknown'}' file, not a Word document.\n"
                "Please select a .docx or .doc file.\n\n"
                "If you want to convert a PDF to Word, use the 'PDF to Word' tab instead.",
            )

        if progress_callback:
            progress_callback(10)

        out_dir = os.path.dirname(os.path.abspath(output_path)) or "."

        # ── Strategy 1: LibreOffice headless ──────────────────────────────────
        soffice = self._find_libreoffice(_plt.system(), shutil)
        if soffice:
            try:
                result = subprocess.run(
                    [soffice, "--headless", "--convert-to", "pdf",
                     "--outdir", out_dir, input_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    stem   = os.path.splitext(os.path.basename(input_path))[0]
                    lo_out = os.path.join(out_dir, stem + ".pdf")
                    if os.path.isfile(lo_out):
                        if os.path.abspath(lo_out) != os.path.abspath(output_path):
                            os.replace(lo_out, output_path)
                        _secure_file(output_path)
                        if progress_callback:
                            progress_callback(100)
                        return True, f"Saved: {os.path.basename(output_path)}"
            except Exception:
                pass  # Fall through to next strategy

        if progress_callback:
            progress_callback(40)

        # ── Strategy 2: docx2pdf (uses Word on macOS/Windows) ─────────────────
        try:
            from docx2pdf import convert as _d2p_convert

            tmp_name = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
            tmp_pdf  = os.path.join(out_dir, tmp_name)
            _d2p_convert(input_path, tmp_pdf)

            if progress_callback:
                progress_callback(90)

            if os.path.abspath(tmp_pdf) != os.path.abspath(output_path):
                os.replace(tmp_pdf, output_path)
            _secure_file(output_path)

            if progress_callback:
                progress_callback(100)

            return True, f"Saved: {os.path.basename(output_path)}"

        except ImportError:
            pass
        except Exception:
            pass

        # ── Nothing worked — give actionable guidance ──────────────────────────
        system = _plt.system()
        if system == "Darwin":
            tip = (
                "To enable Word to PDF conversion, install LibreOffice (free):\n"
                "  https://www.libreoffice.org/download/download-libreoffice/\n\n"
                "Alternatively, install Microsoft Word."
            )
        elif system == "Windows":
            tip = (
                "To enable Word to PDF conversion, install LibreOffice (free):\n"
                "  https://www.libreoffice.org/download/download-libreoffice/\n\n"
                "Alternatively, install Microsoft Word."
            )
        else:
            tip = (
                "To enable Word to PDF conversion, install LibreOffice:\n"
                "  sudo apt install libreoffice\n"
                "  (or your distro's equivalent)"
            )
        return False, f"Conversion requires LibreOffice or Microsoft Word.\n\n{tip}"

    @staticmethod
    def _find_libreoffice(system: str, shutil_mod) -> Optional[str]:
        """Return the soffice executable path, or None if not found."""
        # Check PATH first (works on Linux and when LO is in PATH on macOS/Windows)
        for name in ("soffice", "libreoffice"):
            found = shutil_mod.which(name)
            if found:
                return found
        # Check known fixed locations
        for path in WordToPDFConverter._LO_PATHS.get(system, []):
            if os.path.isfile(path):
                return path
        return None


# ── PDF -> Images ──────────────────────────────────────────────────────────────

_FMT_EXT = {"PNG": "png", "JPEG": "jpg", "TIFF": "tif"}

class PDFToImagesConverter:

    def convert(
        self,
        input_path: str,
        output_dir: str,
        fmt: str = "PNG",              # 'PNG' | 'JPEG' | 'TIFF'
        dpi: int = 150,
        pages_str: str = "",           # "" = all pages
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        if not os.path.isfile(input_path):
            return False, "Input PDF not found."
        if not output_dir:
            return False, "No output folder specified."
        os.makedirs(output_dir, exist_ok=True)

        try:
            import fitz

            doc   = fitz.open(input_path)
            total = len(doc)
            pages = (parse_custom_pages(pages_str, total)
                     if pages_str.strip() else set(range(total)))
            pages = sorted(pages)

            if not pages:
                return False, "No valid pages selected."

            stem = os.path.splitext(os.path.basename(input_path))[0]
            ext  = _FMT_EXT.get(fmt.upper(), "png")
            mat  = fitz.Matrix(dpi / 72.0, dpi / 72.0)

            for n, pg_idx in enumerate(pages):
                if progress_callback:
                    progress_callback(int((n / len(pages)) * 95))
                pix  = doc[pg_idx].get_pixmap(matrix=mat, alpha=False)
                digits = max(3, len(str(total)))
                name = f"{stem}_page_{str(pg_idx + 1).zfill(digits)}.{ext}"
                out  = os.path.join(output_dir, name)
                pix.save(out)

            doc.close()

            if progress_callback:
                progress_callback(100)

            return True, f"Exported {len(pages)} image(s) to: {os.path.basename(output_dir)}"

        except Exception as exc:
            return False, f"Export failed: {exc}"


# ── Images -> PDF ──────────────────────────────────────────────────────────────

class ImagesToPDFConverter:

    def convert(
        self,
        image_paths: List[str],
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        if not image_paths:
            return False, "No images selected."
        if not output_path:
            return False, "No output path specified."

        missing = [p for p in image_paths if not os.path.isfile(p)]
        if missing:
            return False, f"File not found: {os.path.basename(missing[0])}"

        out_dir  = os.path.dirname(os.path.abspath(output_path)) or "."
        tmp_path = None

        try:
            import fitz

            if progress_callback:
                progress_callback(5)

            doc   = fitz.open()
            total = len(image_paths)

            for i, img_path in enumerate(image_paths):
                if progress_callback:
                    progress_callback(int(5 + (i / total) * 85))
                img_doc   = fitz.open(img_path)
                pdf_bytes = img_doc.convert_to_pdf()
                img_doc.close()
                img_pdf   = fitz.open("pdf", pdf_bytes)
                doc.insert_pdf(img_pdf)
                img_pdf.close()
                del pdf_bytes   # release the intermediate bytes immediately

            if progress_callback:
                progress_callback(92)

            fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
            os.close(fd)
            doc.save(tmp_path, garbage=4, deflate=True)
            doc.close()

            _validate_output(tmp_path)
            os.replace(tmp_path, output_path)
            tmp_path = None
            _secure_file(output_path)

            if progress_callback:
                progress_callback(100)

            return True, f"Saved: {os.path.basename(output_path)}"

        except Exception as exc:
            return False, f"Conversion failed: {exc}"

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
