"""
Reusable dialogs for PDF Merger.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
)


class _PasswordDialog(QDialog):
    """Modal dialog for entering (and optionally confirming) a password."""

    def __init__(self, parent, title: str, prompt: str, confirm: bool = False):
        super().__init__(parent)
        self._confirm  = confirm
        self._password = None

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        prompt_lbl = QLabel(prompt)
        prompt_lbl.setWordWrap(True)
        prompt_lbl.setObjectName("dialogPrompt")
        layout.addWidget(prompt_lbl)

        pwd_row = QHBoxLayout()
        pwd_row.setContentsMargins(0, 0, 0, 0)
        pwd_row.setSpacing(4)
        self._pwd_input = QLineEdit()
        self._pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pwd_input.setObjectName("inputField")
        self._pwd_input.setPlaceholderText("Enter password...")
        _eye1 = QPushButton("Show")
        _eye1.setObjectName("eyeBtn")
        _eye1.setCheckable(True)
        _eye1.setFixedWidth(54)
        _eye1.setCursor(Qt.CursorShape.PointingHandCursor)
        _eye1.toggled.connect(
            lambda checked: (
                self._pwd_input.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked
                    else QLineEdit.EchoMode.Password
                ),
                _eye1.setText("Hide" if checked else "Show"),
            )
        )
        pwd_row.addWidget(self._pwd_input)
        pwd_row.addWidget(_eye1)
        layout.addLayout(pwd_row)

        self._confirm_input = None
        if confirm:
            lbl = QLabel("Confirm Password:")
            lbl.setObjectName("fieldLabel")
            layout.addWidget(lbl)
            conf_row = QHBoxLayout()
            conf_row.setContentsMargins(0, 0, 0, 0)
            conf_row.setSpacing(4)
            self._confirm_input = QLineEdit()
            self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._confirm_input.setObjectName("inputField")
            self._confirm_input.setPlaceholderText("Confirm password...")
            _eye2 = QPushButton("Show")
            _eye2.setObjectName("eyeBtn")
            _eye2.setCheckable(True)
            _eye2.setFixedWidth(54)
            _eye2.setCursor(Qt.CursorShape.PointingHandCursor)
            _eye2.toggled.connect(
                lambda checked: (
                    self._confirm_input.setEchoMode(
                        QLineEdit.EchoMode.Normal if checked
                        else QLineEdit.EchoMode.Password
                    ),
                    _eye2.setText("Hide" if checked else "Show"),
                )
            )
            conf_row.addWidget(self._confirm_input)
            conf_row.addWidget(_eye2)
            layout.addLayout(conf_row)

        self._error_lbl = QLabel("")
        self._error_lbl.setObjectName("errorLabel")
        layout.addWidget(self._error_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.setDefault(True)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._submit)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self._pwd_input.returnPressed.connect(self._submit)

    def _submit(self):
        pwd = self._pwd_input.text()
        if not pwd:
            self._error_lbl.setText("Password cannot be empty.")
            return
        if self._confirm and self._confirm_input:
            if pwd != self._confirm_input.text():
                self._error_lbl.setText("Passwords do not match.")
                return
        self._password = pwd
        self.accept()

    @property
    def password(self):
        return self._password
