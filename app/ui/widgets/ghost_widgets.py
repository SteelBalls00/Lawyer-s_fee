# -*- coding: utf-8 -*-
"""Виджеты с «невидимым» стилем: выглядят как текст, редактируются как поле.

Визуально нет рамки, только тонкое подчёркивание при наведении и фокусе.
"""

from PyQt5.QtWidgets import QLineEdit
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox

_GHOST_LINE_EDIT_STYLE = """
GhostLineEdit {
    border: none;
    border-bottom: 1px solid transparent;
    background: transparent;
    color: #1c2b3a;
    padding: 2px 0px;
    font-size: 12px;
}
GhostLineEdit:hover {
    border-bottom: 1px solid #9aafc0;
    background: transparent;
}
GhostLineEdit:focus {
    border-bottom: 2px solid #2c5282;
    background: #f4f8fc;
}
"""

_GHOST_COMBO_STYLE = """
GhostComboBox {
    border: none;
    border-bottom: 1px solid transparent;
    background: transparent;
    color: #1c2b3a;
    padding: 2px 0px;
    font-size: 12px;
    min-height: 22px;
}
GhostComboBox:hover {
    border-bottom: 1px solid #9aafc0;
}
GhostComboBox:focus {
    border-bottom: 2px solid #2c5282;
    background: #f4f8fc;
}
GhostComboBox::drop-down {
    border: none;
    width: 16px;
    background: transparent;
}
"""


class GhostLineEdit(QLineEdit):
    """QLineEdit с прозрачным фоном и только нижней границей при фокусе."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_GHOST_LINE_EDIT_STYLE)


class GhostComboBox(NoWheelComboBox):
    """NoWheelComboBox с прозрачным фоном и только нижней границей при фокусе."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_GHOST_COMBO_STYLE)
