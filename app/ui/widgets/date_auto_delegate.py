# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QStyledItemDelegate


class DateAutoDelegate(QStyledItemDelegate):
    """Делегат для колонки с датой: точки расставляются прямо при вводе цифр."""

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMaxLength(10)
        editor.setAlignment(Qt.AlignCenter)
        editor.setPlaceholderText("дд.мм.гггг")
        editor._updating = False

        def on_text_changed(text):
            if editor._updating:
                return
            editor._updating = True

            digits = "".join(ch for ch in text if ch.isdigit())[:8]

            if len(digits) <= 2:
                formatted = digits
            elif len(digits) <= 4:
                formatted = digits[:2] + "." + digits[2:]
            else:
                formatted = digits[:2] + "." + digits[2:4] + "." + digits[4:]

            editor.setText(formatted)
            editor.setCursorPosition(len(formatted))
            editor._updating = False

        editor.textChanged.connect(on_text_changed)
        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.data() or "")
        editor.selectAll()

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)