# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QSplitter

from app.constants import WINDOW_TITLE
from app.ui.panels.info_panel import InfoPanel
from app.ui.panels.preview_panel import PreviewPanel


class MainWindow(QMainWindow):
    def __init__(self, state, case_controller, payment_calculator, parent=None):
        super().__init__(parent)

        self.state = state
        self.case_controller = case_controller
        self.payment_calculator = payment_calculator

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1600, 900)

        self._apply_style()
        self._build_ui()
        self._connect_signals()

        self.refresh_preview()

    def _build_ui(self):
        self.info_panel = InfoPanel(
            state=self.state,
            case_controller=self.case_controller,
            payment_calculator=self.payment_calculator,
            parent=self,
        )
        self.preview_panel = PreviewPanel(parent=self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.info_panel)
        splitter.addWidget(self.preview_panel)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([520, 1080])

        self.setCentralWidget(splitter)

        self.statusBar().showMessage("Готово")

    def _connect_signals(self):
        self.info_panel.data_changed.connect(self.refresh_preview)
        self.info_panel.status_message.connect(self.statusBar().showMessage)

    def refresh_preview(self):
        self.preview_panel.update_preview(self.state)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                font-size: 12px;
            }

            QMainWindow {
                background-color: #f2f2f2;
            }

            QGroupBox {
                border: 1px solid #9a9a9a;
                margin-top: 10px;
                padding-top: 8px;
                background: #fcfcfc;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px 0 4px;
            }

            QPushButton {
                min-height: 28px;
                padding: 4px 10px;
                border: 1px solid #7f7f7f;
                background-color: #e9e9e9;
                border-radius: 0px;
            }

            QPushButton:hover {
                background-color: #dddddd;
            }

            QPushButton:pressed {
                background-color: #d0d0d0;
            }

            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QTextBrowser, QTableWidget {
                border: 1px solid #8c8c8c;
                background: white;
                border-radius: 0px;
                padding: 4px;
            }

            QCheckBox, QLabel {
                color: #202020;
            }
        """)