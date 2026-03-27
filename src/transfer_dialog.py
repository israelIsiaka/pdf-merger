"""
Device transfer request dialog for PDF Merger.

When a user replaces their computer, they can submit a transfer request here.
An admin will review it and reset the license so they can activate on the new device.
Access via: Help menu > Transfer License.
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox,
)

from .license import LicenseManager


class _TransferWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, manager: LicenseManager, key: str,
                 email: str, reason: str):
        super().__init__()
        self._manager = manager
        self._key     = key
        self._email   = email
        self._reason  = reason

    def run(self):
        ok, msg = self._manager.request_transfer(
            self._key, self._email, self._reason
        )
        self.done.emit(ok, msg)

    def __del__(self):
        self.wait()


class TransferDialog(QDialog):
    """
    Lets the user submit a device transfer request.
    Pre-fills email from the stored license token where available.
    """

    def __init__(self, manager: LicenseManager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._worker  = None

        self.setWindowTitle("Transfer License to New Device")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self._prefill()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        title = QLabel("Transfer License to New Device")
        f = QFont(); f.setPointSize(14); f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        info = QLabel(
            "Use this form if you have replaced your computer and need to "
            "move your lifetime license to a new device.\n\n"
            "An admin will review your request and contact you by email "
            "once it is approved. You can then activate on your new device."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("you@example.com")
        self._email_edit.setMinimumHeight(34)
        form.addRow("Email:", self._email_edit)

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._key_edit.setMaxLength(64)
        f2 = QFont("monospace"); f2.setPointSize(12)
        self._key_edit.setFont(f2)
        self._key_edit.setMinimumHeight(34)
        form.addRow("Activation Key:", self._key_edit)

        layout.addLayout(form)

        layout.addWidget(QLabel("Reason for transfer:"))
        self._reason_edit = QTextEdit()
        self._reason_edit.setPlaceholderText(
            "e.g. My old laptop stopped working and I bought a new one."
        )
        self._reason_edit.setMaximumHeight(90)
        layout.addWidget(self._reason_edit)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setMinimumHeight(36)
        layout.addWidget(self._status)

        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._submit_btn = QPushButton("Submit Transfer Request")
        self._submit_btn.setFixedHeight(36)
        f3 = QFont(); f3.setBold(True)
        self._submit_btn.setFont(f3)
        self._submit_btn.setDefault(True)
        self._submit_btn.clicked.connect(self._do_submit)
        btn_row.addWidget(self._submit_btn)

        layout.addLayout(btn_row)

    def _prefill(self):
        """Pre-fill email from the stored license token if available."""
        info = self._manager.get_info()
        if info.get("email"):
            self._email_edit.setText(info["email"])

    def _do_submit(self):
        key    = self._key_edit.text().strip()
        email  = self._email_edit.text().strip()
        reason = self._reason_edit.toPlainText().strip()

        if not email or "@" not in email:
            return self._set_status("Please enter a valid email address.", error=True)
        if not key:
            return self._set_status("Please enter your activation key.", error=True)
        if not reason:
            return self._set_status("Please describe why you need a transfer.", error=True)

        self._set_busy(True)
        self._set_status("Submitting request...")

        self._worker = _TransferWorker(self._manager, key, email, reason)
        self._worker.done.connect(self._on_done)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_done(self, success: bool, message: str):
        self._set_busy(False)
        if success:
            QMessageBox.information(
                self, "Request Submitted",
                message + "\n\nDo not uninstall PDF Merger until your request is approved.",
            )
            self.accept()
        else:
            self._set_status(message, error=True)

    def _set_status(self, msg: str, error: bool = False):
        color = "#cc2200" if error else "#1a7a40"
        self._status.setStyleSheet(f"color: {color};")
        self._status.setText(msg)

    def _set_busy(self, busy: bool):
        self._submit_btn.setEnabled(not busy)
        self._key_edit.setEnabled(not busy)
        self._email_edit.setEnabled(not busy)
        self._reason_edit.setEnabled(not busy)
        self._submit_btn.setText(
            "Submitting..." if busy else "Submit Transfer Request"
        )
