# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
)

from app.constants import WINDOW_TITLE
from app.ui.panels.info_panel import InfoPanel
from app.ui.panels.preview_panel import PreviewPanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        state,
        case_controller,
        payment_calculator,
        preview_renderer,
        save_controller,
        parent=None,
    ):
        super().__init__(parent)

        self.state = state
        self.case_controller = case_controller
        self.payment_calculator = payment_calculator
        self.preview_renderer = preview_renderer
        self.save_controller = save_controller

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1600, 900)

        self._apply_style()
        self._build_toolbar()
        self._build_ui()
        self._connect_signals()

        self.refresh_preview()

    def _build_toolbar(self):
        self.save_docx_action = QAction("Сохранить постановление", self)
        self.save_docx_action.triggered.connect(self._on_save_docx)

        self.check_template_action = QAction("Проверить шаблон", self)
        self.check_template_action.triggered.connect(self._on_check_template)

        toolbar = self.addToolBar("Документ")
        toolbar.setMovable(False)
        toolbar.addAction(self.save_docx_action)
        # toolbar.addAction(self.check_template_action)

    def _build_ui(self):
        self.info_panel = InfoPanel(
            state=self.state,
            case_controller=self.case_controller,
            payment_calculator=self.payment_calculator,
            parent=self,
        )
        self.info_panel.setMinimumWidth(620)

        self.preview_panel = PreviewPanel(
            preview_renderer=self.preview_renderer,
            parent=self,
        )

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.info_panel)
        splitter.addWidget(self.preview_panel)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([640, 960])

        self.setCentralWidget(splitter)

        self.statusBar().showMessage("Готово")

    def _connect_signals(self):
        self.info_panel.data_changed.connect(self.refresh_preview)
        self.info_panel.status_message.connect(self.statusBar().showMessage)

    def refresh_preview(self):
        self.preview_panel.update_preview(self.state)

    def _on_check_template(self):
        self.info_panel.save_to_state()

        try:
            all_tags = self.save_controller.get_template_tags()
            unknown_tags = self.save_controller.get_unknown_template_tags()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка проверки шаблона",
                "Не удалось проверить шаблон:\n{0}".format(str(exc)),
            )
            return

        if unknown_tags:
            text = (
                "В шаблоне есть теги, которые пока не обрабатываются:\n\n{0}"
            ).format("\n".join(unknown_tags))
            self._show_tag_report(
                title="Проверка шаблона",
                text=text,
                all_tags=all_tags,
                icon=QMessageBox.Warning,
            )
        else:
            text = "Все теги шаблона известны программе."
            self._show_tag_report(
                title="Проверка шаблона",
                text=text,
                all_tags=all_tags,
                icon=QMessageBox.Information,
            )

    def _on_save_docx(self):
        self.info_panel.save_to_state()
        self.refresh_preview()

        default_name = self.save_controller.get_default_file_name()

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить постановление",
            default_name,
            "Документы Word (*.docx)",
        )

        if not output_path:
            return

        try:
            saved_path = self.save_controller.save_to_docx(output_path)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                "Не удалось сохранить постановление:\n{0}".format(str(exc)),
            )
            self.statusBar().showMessage("Ошибка сохранения")
            return

        unknown_tags = self.save_controller.get_last_unknown_tags()
        unresolved_tags = self.save_controller.get_last_unresolved_tags()

        if unknown_tags or unresolved_tags:
            parts = []

            if unknown_tags:
                parts.append(
                    "Неизвестные теги:\n{0}".format("\n".join(unknown_tags))
                )

            if unresolved_tags:
                parts.append(
                    "Теги, оставшиеся в готовом документе:\n{0}".format(
                        "\n".join(unresolved_tags)
                    )
                )

            QMessageBox.warning(
                self,
                "Документ сохранён с предупреждениями",
                "\n\n".join(parts),
            )

        self.statusBar().showMessage("Документ сохранён")
        self._open_file(saved_path)

    def _open_file(self, path):
        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        if not ok:
            QMessageBox.warning(
                self,
                "Открытие файла",
                "Документ сохранён, но открыть его автоматически не удалось:\n{0}".format(path),
            )

    def _show_tag_report(self, title, text, all_tags, icon):
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)

        if all_tags:
            box.setDetailedText("Все теги шаблона:\n\n{0}".format("\n".join(all_tags)))
        else:
            box.setDetailedText("Теги в шаблоне не найдены.")

        box.exec_()

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                font-size: 12px;
            }

            QMainWindow {
                background-color: #f2f2f2;
            }

            QToolBar {
                border: 1px solid #9a9a9a;
                background-color: #eeeeee;
                spacing: 4px;
            }

            QToolButton {
                min-height: 26px;
                padding: 4px 10px;
                border: 1px solid #7f7f7f;
                background-color: #e9e9e9;
                border-radius: 0px;
            }

            QToolButton:hover {
                background-color: #dddddd;
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