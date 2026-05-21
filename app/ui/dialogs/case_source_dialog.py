# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CaseSourceDialog(QDialog):
    """Диалог выбора картотеки, когда дело найдено и в уголовной, и в материалах.

    Возвращает результат через атрибут selected_source: "u1" или "m".
    Закрытие крестиком оставляет selected_source = None.
    """

    def __init__(self, case_number, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор картотеки")
        self.setModal(True)
        self.setMinimumWidth(380)

        self.selected_source = None

        info = QLabel(
            "Дело № {0} найдено в обеих картотеках.\n"
            "В какой картотеке искать данное дело?".format(case_number)
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)

        btn_u1 = QPushButton("Уголовная картотека")
        btn_m = QPushButton("Материалы")
        btn_u1.setMinimumHeight(36)
        btn_m.setMinimumHeight(36)

        btn_u1.clicked.connect(self._on_u1)
        btn_m.clicked.connect(self._on_m)

        buttons = QHBoxLayout()
        buttons.addWidget(btn_u1)
        buttons.addWidget(btn_m)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 16, 20, 16)
        root.addWidget(info)
        root.addLayout(buttons)

    def _on_u1(self):
        self.selected_source = "u1"
        self.accept()

    def _on_m(self):
        self.selected_source = "m"
        self.accept()
