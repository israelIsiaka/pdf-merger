"""
Background worker threads for PDF Merger.
Each worker runs one operation on a QThread and emits signals for
progress updates and completion, keeping the UI fully responsive.
"""
from PyQt6.QtCore import QThread, pyqtSignal



class _MergeWorker(QThread):
    progress_changed = pyqtSignal(int)
    merge_done       = pyqtSignal(bool, str)

    def __init__(self, merger, output_path, passwords):
        super().__init__()
        self._merger      = merger
        self._output_path = output_path
        self._passwords   = passwords

    def run(self):
        success, msg = self._merger.merge(
            self._output_path,
            progress_callback=self.progress_changed.emit,
            passwords=self._passwords,
        )
        self.merge_done.emit(success, msg)


class _ProtectWorker(QThread):
    progress_changed = pyqtSignal(int)
    protect_done     = pyqtSignal(bool, str)

    def __init__(self, merger, input_path, output_path, password):
        super().__init__()
        self._merger = merger
        self._input  = input_path
        self._output = output_path
        self._pwd    = password

    def run(self):
        success, msg = self._merger.protect_pdf(
            self._input, self._output, self._pwd,
            progress_callback=self.progress_changed.emit,
        )
        self.protect_done.emit(success, msg)


class _PeepWorker(QThread):
    progress_changed = pyqtSignal(int)
    peep_done        = pyqtSignal(bool, str)

    def __init__(self, merger, input_path, free_pages, preview_path, full_path, password):
        super().__init__()
        self._merger  = merger
        self._input   = input_path
        self._free    = free_pages
        self._preview = preview_path
        self._full    = full_path
        self._pwd     = password

    def run(self):
        success, msg = self._merger.create_peep(
            self._input, self._free, self._preview, self._full, self._pwd,
            progress_callback=self.progress_changed.emit,
        )
        self.peep_done.emit(success, msg)


class _CompressWorker(QThread):
    progress_changed = pyqtSignal(int)
    compress_done    = pyqtSignal(bool, str)

    def __init__(self, compressor, input_path: str, output_path: str, level: int):
        super().__init__()
        self._compressor = compressor
        self._input      = input_path
        self._output     = output_path
        self._level      = level

    def run(self):
        success, msg = self._compressor.compress(
            self._input, self._output, self._level,
            progress_callback=self.progress_changed.emit,
        )
        self.compress_done.emit(success, msg)


class _WatermarkWorker(QThread):
    progress_changed = pyqtSignal(int)
    watermark_done   = pyqtSignal(bool, str)

    def __init__(self, watermarker, input_path: str, output_path: str,
                 image_path: str, position: str, frequency: str,
                 scale: float, opacity: float):
        super().__init__()
        self._wm        = watermarker
        self._input     = input_path
        self._output    = output_path
        self._image     = image_path
        self._position  = position
        self._frequency = frequency
        self._scale     = scale
        self._opacity   = opacity

    def run(self):
        success, msg = self._wm.apply(
            self._input, self._output, self._image,
            self._position, self._frequency, self._scale, self._opacity,
            progress_callback=self.progress_changed.emit,
        )
        self.watermark_done.emit(success, msg)


class _WatermarkPreviewWorker(QThread):
    """Render a single page with watermark in-memory and emit the QImage."""
    preview_ready = pyqtSignal(object)   # QImage or None

    def __init__(self, watermarker, pdf_path: str, image_path: str,
                 position: str, scale: float, opacity: float,
                 page_index: int, frequency: str = "all"):
        super().__init__()
        self._wm         = watermarker
        self._pdf        = pdf_path
        self._image      = image_path
        self._position   = position
        self._scale      = scale
        self._opacity    = opacity
        self._page_index = page_index
        self._frequency  = frequency
        self._stopped    = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        if self._stopped:
            return
        result = self._wm.render_preview(
            self._pdf, self._image, self._position,
            self._scale, self._opacity, self._page_index,
            self._frequency,
        )
        if not self._stopped:
            self.preview_ready.emit(result)


class _RenderWorker(QThread):
    """Render PDF pages to QImages in a background thread using PyMuPDF."""
    page_ready  = pyqtSignal(int, object)   # (page_index, QImage)
    render_done = pyqtSignal()

    def __init__(self, pdf_path: str, password: str,
                 start_page: int, end_page: int, dpi: int = 150):
        super().__init__()
        self._path    = pdf_path
        self._pwd     = password
        self._start   = start_page
        self._end     = end_page
        self._dpi     = dpi
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        try:
            import fitz                          # PyMuPDF
            from PyQt6.QtGui import QImage

            doc = fitz.open(self._path)
            if doc.needs_pass:
                doc.authenticate(self._pwd)

            mat   = fitz.Matrix(self._dpi / 72.0, self._dpi / 72.0)
            total = len(doc)

            for i in range(self._start, min(self._end, total)):
                if self._stopped:
                    break
                pix = doc[i].get_pixmap(matrix=mat, alpha=False)
                img = QImage(
                    bytes(pix.samples),
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_RGB888,
                )
                self.page_ready.emit(i, img.copy())

            doc.close()
        except Exception:
            pass
        finally:
            self.render_done.emit()
