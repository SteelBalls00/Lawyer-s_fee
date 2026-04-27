# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QComboBox


class NoWheelComboBox(QComboBox):
    """
    QComboBox, который не меняет выбранное значение при прокрутке колесом мыши.
    Это удобно для таблиц, чтобы случайно не менять услугу или источник постановления.
    """

    def wheelEvent(self, event):
        event.ignore()