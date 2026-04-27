# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTextBrowser, QVBoxLayout, QWidget


class PreviewPanel(QWidget):
    def __init__(self, preview_renderer, parent=None):
        super().__init__(parent)

        self.preview_renderer = preview_renderer

        self._build_ui()

    def _build_ui(self):
        self.preview_browser = QTextBrowser()

        layout = QVBoxLayout()
        layout.addWidget(self.preview_browser)

        self.setLayout(layout)

    def update_preview(self, state):
        try:
            text = self.preview_renderer.render(state)
        except Exception as exc:
            text = "Ошибка формирования предпросмотра:\n{0}".format(str(exc))

        self.preview_browser.setPlainText(text)