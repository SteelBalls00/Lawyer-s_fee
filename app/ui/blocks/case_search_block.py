# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)


class CaseSearchBlock(QGroupBox):
    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Поиск дела", parent)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.case_number_label = QLabel("№ дела")
        self.case_number_edit = QLineEdit()
        self.case_number_edit.setPlaceholderText("Введите номер дела")

        self.find_button = QPushButton("Найти")

        row = QHBoxLayout()
        row.addWidget(self.case_number_label)
        row.addWidget(self.case_number_edit, 1)
        row.addWidget(self.find_button)

        root = QVBoxLayout()
        root.addLayout(row)

        self.setLayout(root)

    def _connect_signals(self):
        self.find_button.clicked.connect(self._emit_search)
        self.case_number_edit.returnPressed.connect(self._emit_search)

    def _emit_search(self):
        self.search_requested.emit(self.case_number_edit.text().strip())

    def set_case_number(self, value: str):
        self.case_number_edit.setText(value or "")