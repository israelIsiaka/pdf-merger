"""
Activation dialog for PDF Merger.
Shown on first launch when no valid license token is found.
The dialog is modal and cannot be dismissed — the app quits if the user cancels.
"""

import sys

from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame,
    QLabel, QLineEdit, QPushButton,
    QMessageBox,
)

from .license import LicenseManager, ACTIVATION_SERVER_URL

import requests as _requests


class _ActivateWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, manager: LicenseManager, key: str, email: str):
        super().__init__()
        self._manager = manager
        self._key     = key
        self._email   = email

    def run(self):
        ok, msg = self._manager.activate(self._key, self._email)
        self.done.emit(ok, msg)

    def __del__(self):
        self.wait()


class _BuyWorker(QThread):
    done = pyqtSignal(bool, str)   # (success, checkout_url_or_error)

    def __init__(self, server_url: str, email: str):
        super().__init__()
        self._server_url = server_url
        self._email      = email

    def run(self):
        try:
            resp = _requests.post(
                f"{self._server_url}/api/create-checkout",
                json={"email": self._email},
                timeout=15,
            )
            if resp.status_code == 200:
                url = resp.json().get("url", "")
                self.done.emit(bool(url), url or "No checkout URL returned.")
            else:
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    detail = ""
                self.done.emit(False, detail or f"Server error ({resp.status_code}).")
        except _requests.exceptions.ConnectionError:
            self.done.emit(False, "Cannot reach the server. Check your internet connection.")
        except _requests.exceptions.Timeout:
            self.done.emit(False, "Server timed out. Please try again.")
        except Exception as exc:
            self.done.emit(False, f"Network error: {exc}")

    def __del__(self):
        self.wait()


class ActivationDialog(QDialog):

    def __init__(self, manager: LicenseManager, parent=None):
        super().__init__(parent)
        self._manager        = manager
        self._worker         = None
        self._buy_worker     = None

        self.setWindowTitle("PDF Merger — Activation Required")
        self.setMinimumWidth(520)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 28)
        layout.setSpacing(14)

        # Title
        title = QLabel("PDF Merger")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Activation Required")
        f2 = QFont(); f2.setPointSize(13)
        sub.setFont(f2)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(4)

        info = QLabel(
            "Purchase a lifetime license or enter your existing key below.\n"
            "Each key activates one device — no subscription, no expiry."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        layout.addSpacing(4)

        # Form fields
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
        f3 = QFont("monospace"); f3.setPointSize(13)
        self._key_edit.setFont(f3)
        self._key_edit.setMinimumHeight(34)
        self._key_edit.returnPressed.connect(self._do_activate)
        form.addRow("Activation Key:", self._key_edit)

        layout.addLayout(form)

        # Status
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._status.setMinimumHeight(40)
        layout.addWidget(self._status)

        # Button row
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)

        self._quit_btn = QPushButton("Quit")
        self._quit_btn.setFixedHeight(38)
        self._quit_btn.clicked.connect(self._on_quit)
        btn_row.addWidget(self._quit_btn)

        btn_row.addStretch()

        self._buy_btn = QPushButton("Buy License")
        self._buy_btn.setFixedHeight(38)
        self._buy_btn.setToolTip("Purchase a lifetime license — opens secure payment in your browser")
        self._buy_btn.clicked.connect(self._do_buy)
        btn_row.addWidget(self._buy_btn)

        self._activate_btn = QPushButton("Activate")
        self._activate_btn.setFixedHeight(38)
        f4 = QFont(); f4.setBold(True)
        self._activate_btn.setFont(f4)
        self._activate_btn.setDefault(True)
        self._activate_btn.clicked.connect(self._do_activate)
        btn_row.addWidget(self._activate_btn)

        layout.addLayout(btn_row)

        # Footer
        priv = QLabel("100% offline after activation  |  Your files never leave your device")
        priv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f5 = QFont(); f5.setPointSize(9)
        priv.setFont(f5)
        layout.addWidget(priv)

    # ── Buy flow ──────────────────────────────────────────────────────────────

    def _do_buy(self):
        email = self._email_edit.text().strip()
        if not email:
            return self._set_status("Enter your email address first, then click Buy License.", error=True)
        if "@" not in email:
            return self._set_status("Please enter a valid email address.", error=True)

        self._set_status("Opening payment page...")
        self._set_busy(True)

        self._buy_worker = _BuyWorker(ACTIVATION_SERVER_URL, email)
        self._buy_worker.done.connect(self._on_buy_done)
        self._buy_worker.finished.connect(self._buy_worker.deleteLater)
        self._buy_worker.start()

    def _on_buy_done(self, success: bool, url_or_error: str):
        self._set_busy(False)
        if success:
            QDesktopServices.openUrl(QUrl(url_or_error))
            self._set_status(
                "Payment page opened in your browser. After paying, check your email "
                "for your activation key, then enter it above.",
                error=False,
            )
        else:
            self._set_status(url_or_error, error=True)

    # ── Activate flow ─────────────────────────────────────────────────────────

    def _do_activate(self):
        key   = self._key_edit.text().strip()
        email = self._email_edit.text().strip()
        if not email:
            return self._set_status("Please enter your email address.", error=True)
        if "@" not in email:
            return self._set_status("Please enter a valid email address.", error=True)
        if not key:
            return self._set_status("Please enter your activation key.", error=True)

        self._set_status("Contacting activation server...")
        self._set_busy(True)

        self._worker = _ActivateWorker(self._manager, key, email)
        self._worker.done.connect(self._on_done)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_done(self, success: bool, message: str):
        self._set_busy(False)
        if success:
            self._set_status(message, error=False)
            QMessageBox.information(self, "Activated", message)
            self.accept()
        else:
            self._set_status(message, error=True)

    def _on_quit(self):
        sys.exit(0)

    def _set_status(self, msg: str, error: bool = False):
        color = "#cc2200" if error else "#1a7a40"
        self._status.setStyleSheet(f"color: {color};")
        self._status.setText(msg)

    def _set_busy(self, busy: bool):
        self._activate_btn.setEnabled(not busy)
        self._buy_btn.setEnabled(not busy)
        self._quit_btn.setEnabled(not busy)
        self._key_edit.setEnabled(not busy)
        self._email_edit.setEnabled(not busy)
        if busy:
            self._activate_btn.setText("Activating...")
        else:
            self._activate_btn.setText("Activate")
