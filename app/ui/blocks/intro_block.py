# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)
from PyQt5.QtGui import QFont


class IntroBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Вводная часть", parent)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.label = QLabel("Использовать свою часть состава суда: ")

        self.radio_yes = QRadioButton("Да")
        self.radio_no = QRadioButton("Нет")
        self.radio_no.setChecked(True)

        top_row = QHBoxLayout()
        top_row.addWidget(self.label)
        top_row.addWidget(self.radio_yes)
        top_row.addWidget(self.radio_no)
        top_row.addStretch(1)

        self.text_edit = QTextEdit()
        self.text_edit.setMinimumHeight(90)
        self.text_edit.setVisible(False)

        root = QVBoxLayout()
        root.addLayout(top_row)
        root.addWidget(self.text_edit)

        self.setLayout(root)

    def _connect_signals(self):
        self.radio_yes.toggled.connect(self._on_mode_changed)
        self.radio_yes.toggled.connect(self.data_changed.emit)
        self.radio_no.toggled.connect(self.data_changed.emit)
        self.text_edit.textChanged.connect(self.data_changed.emit)

    def load_from_state(self, state):
        self.radio_yes.blockSignals(True)
        self.radio_no.blockSignals(True)
        self.text_edit.blockSignals(True)

        self.radio_yes.setChecked(state.use_custom_intro)
        self.radio_no.setChecked(not state.use_custom_intro)
        if state.custom_intro_html:
            self.text_edit.setHtml(state.custom_intro_html)
        else:
            self.text_edit.setPlainText(state.custom_intro_text or "")
        self.text_edit.setVisible(state.use_custom_intro)

        self.radio_yes.blockSignals(False)
        self.radio_no.blockSignals(False)
        self.text_edit.blockSignals(False)

    def save_to_state(self, state):
        state.use_custom_intro = self.radio_yes.isChecked()
        state.custom_intro_text = self.text_edit.toPlainText().strip()
        state.custom_intro_html = self.text_edit.toHtml()
        state.custom_intro_segments = self._extract_rich_segments()

    def _on_mode_changed(self):
        self.text_edit.setVisible(self.radio_yes.isChecked())

    def _extract_rich_segments(self):
        segments = []

        document = self.text_edit.document()
        block = document.begin()

        first_block = True

        while block.isValid():
            if not first_block:
                segments.append({
                    "text": "\n",
                    "bold": False,
                })

            iterator = block.begin()

            while not iterator.atEnd():
                fragment = iterator.fragment()

                if fragment.isValid():
                    text = fragment.text()

                    if text:
                        char_format = fragment.charFormat()
                        is_bold = char_format.fontWeight() >= QFont.Bold

                        segments.append({
                            "text": text,
                            "bold": is_bold,
                        })

                iterator += 1

            first_block = False
            block = block.next()

        return segments