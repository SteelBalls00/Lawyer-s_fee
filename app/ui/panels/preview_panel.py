# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QTextBrowser,
)


class PreviewPanel(QGroupBox):
    def __init__(self, preview_renderer, parent=None):
        super().__init__("ПРЕДПРОСМОТР ДОКУМЕНТА", parent)

        self.preview_renderer = preview_renderer

        self._ignore_scroll_changes = False
        self._last_scroll_value = 0

        self._build_ui()

    def _build_ui(self):
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)

        self.browser.verticalScrollBar().valueChanged.connect(
            self._on_scroll_changed
        )

        layout = QVBoxLayout()
        layout.addWidget(self.browser)

        self.setLayout(layout)

    def _on_scroll_changed(self, value):
        if self._ignore_scroll_changes:
            return

        self._last_scroll_value = value

    def update_preview(self, state):
        scroll_bar = self.browser.verticalScrollBar()

        saved_value = self._last_scroll_value
        if saved_value <= 0 and scroll_bar.value() > 0:
            saved_value = scroll_bar.value()

        try:
            html = self.preview_renderer.render(state)
        except Exception as exc:
            html = """
                <html>
                <body style="font-family: Segoe UI; background:#eef1f4;">
                    <div style="margin:20px; padding:16px; background:white; border:1px solid #d7dde5;">
                        <div style="color:#8a3d3d; font-weight:bold; margin-bottom:8px;">
                            Ошибка формирования предпросмотра
                        </div>
                        <pre style="white-space:pre-wrap;">{0}</pre>
                    </div>
                </body>
                </html>
            """.format(str(exc))

        self._ignore_scroll_changes = True
        self.browser.setHtml(html)
        self._restore_scroll_later(saved_value)

    def _restore_scroll_later(self, value):
        QTimer.singleShot(0, lambda: self._restore_scroll(value))
        QTimer.singleShot(30, lambda: self._restore_scroll(value))
        QTimer.singleShot(80, lambda: self._restore_scroll(value))
        QTimer.singleShot(150, lambda: self._finish_restore_scroll(value))

    def _restore_scroll(self, value):
        scroll_bar = self.browser.verticalScrollBar()
        maximum = scroll_bar.maximum()

        value = max(0, min(value, maximum))
        scroll_bar.setValue(value)

    def _finish_restore_scroll(self, value):
        self._restore_scroll(value)

        self._ignore_scroll_changes = False
        self._last_scroll_value = self.browser.verticalScrollBar().value()