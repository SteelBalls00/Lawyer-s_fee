# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class LoginDialog(QDialog):
    """Окно авторизации: только пароль, как в ГАС СДП.

    При успехе self.username содержит имя пользователя.
    """

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.username = None

        self.setWindowTitle("Авторизация")
        self.setModal(True)
        self.setMinimumWidth(340)

        info = QLabel("Введите пароль от ГАС СДП:")

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._on_login)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b85c5c; font-weight: bold;")
        self.error_label.setVisible(False)

        login_btn = QPushButton("Войти")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self._on_login)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(login_btn)
        buttons.addWidget(cancel_btn)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(18, 14, 18, 14)
        root.addWidget(info)
        root.addWidget(self.password_edit)
        root.addWidget(self.error_label)
        root.addLayout(buttons)

        self.password_edit.setFocus()

    def _on_login(self):
        password = self.password_edit.text().strip()
        if not password:
            self._show_error("Введите пароль")
            return

        try:
            username = self.auth_service.authenticate(password)
        except Exception as exc:
            self._show_error("Ошибка подключения к БД:\n{0}".format(exc))
            return

        if username:
            self.username = username
            self.accept()
        else:
            self._show_error("Неверный пароль")
            self.password_edit.selectAll()
            self.password_edit.setFocus()

    def _show_error(self, text):
        self.error_label.setText(text)
        self.error_label.setVisible(True)
