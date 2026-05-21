# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QLineEdit, QCompleter


class HistoryLineEdit(QLineEdit):
    """QLineEdit с выпадающим списком ранее использованных значений.

    При пустом поле (клик/фокус) показывает все варианты.
    При наборе текста — только совпадающие; если совпадений нет, список скрыт.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = QStringListModel(self)

        self._completer = QCompleter(self._model, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        # Обычный режим — фильтрует по введённому тексту и сам скрывается,
        # если ни один вариант не подходит
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(self._completer)

    def set_history_values(self, values):
        self._model.setStringList(list(values or []))

    def _show_popup(self):
        if self._model.rowCount() == 0:
            return

        self._completer.setCompletionPrefix(self.text())
        # Показываем только если есть хотя бы одно совпадение
        if self._completer.completionCount() > 0:
            self._completer.complete()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._show_popup()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._show_popup()