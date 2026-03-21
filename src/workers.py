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
