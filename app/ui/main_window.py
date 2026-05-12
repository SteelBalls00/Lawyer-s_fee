# -*- coding: utf-8 -*-
import os
import sys

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon
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

        def _get_base_path():
            if getattr(sys, 'frozen', False):
                return sys._MEIPASS  # путь внутри скомпилированного приложения
            return os.path.dirname(os.path.abspath(sys.argv[0]))

        icon_path = os.path.join(_get_base_path(), 'lawyer_fee.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        toolbar.addAction(self.check_template_action)

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
            /* ═══════════════════════════════════════════
               ОСНОВА
            ═══════════════════════════════════════════ */
            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12px;
                color: #1c2b3a;
                background-color: #eaecf0;
            }

            QMainWindow {
                background-color: #eaecf0;
            }

            /* ═══════════════════════════════════════════
               ПАНЕЛЬ ИНСТРУМЕНТОВ
            ═══════════════════════════════════════════ */
            QToolBar {
                background-color: #1e3a5f;
                border: none;
                border-bottom: 2px solid #162d4a;
                spacing: 6px;
                padding: 4px 8px;
            }

            QToolButton {
                color: #dce8f5;
                background-color: transparent;
                border: 1px solid transparent;
                min-height: 28px;
                padding: 4px 14px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.3px;
            }

            QToolButton:hover {
                background-color: #2c5282;
                border: 1px solid #3a6aab;
                color: #ffffff;
            }

            QToolButton:pressed {
                background-color: #162d4a;
                border: 1px solid #1a3a5c;
            }

            /* ═══════════════════════════════════════════
               ГРУПП-БОКСЫ
            ═══════════════════════════════════════════ */
            QGroupBox {
                background-color: #f5f7fa;
                border: 1px solid #b0bec8;
                border-top: 2px solid #2c5282;
                margin-top: 12px;
                padding-top: 10px;
                padding-bottom: 4px;
                padding-left: 6px;
                padding-right: 6px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                top: -1px;
                padding: 0 6px;
                color: #1e3a5f;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.4px;
                background-color: #f5f7fa;
            }

            /* ═══════════════════════════════════════════
               ПОЛЯ ВВОДА
            ═══════════════════════════════════════════ */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #9aafc0;
                border-radius: 0px;
                padding: 3px 6px;
                color: #1c2b3a;
                selection-background-color: #2c5282;
                selection-color: #ffffff;
            }

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #1e3a5f;
                background-color: #f7faff;
            }

            QLineEdit:disabled {
                background-color: #e8edf2;
                color: #7a8fa0;
            }

            /* ═══════════════════════════════════════════
               КОМБОБОКС
            ═══════════════════════════════════════════ */
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #9aafc0;
                border-radius: 0px;
                padding: 3px 6px;
                color: #1c2b3a;
                min-height: 24px;
            }

            QComboBox:hover {
                border: 1px solid #2c5282;
            }

            QComboBox:focus {
                border: 1px solid #1e3a5f;
            }

            QComboBox::drop-down {
                border: none;
                border-left: 1px solid #9aafc0;
                width: 20px;
                background-color: #dce8f0;
            }

            QComboBox::down-arrow {
                image: url(resources/arrow_down.svg);
                width: 8px;
                height: 5px;
            }


            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #2c5282;
                selection-background-color: #dce8f5;
                selection-color: #1c2b3a;
                outline: none;
            }
            
            QTableWidget QComboBox {
                padding: 1px 4px;
                min-height: 0px;
                border: none;
            }

            /* ═══════════════════════════════════════════
               КНОПКИ
            ═══════════════════════════════════════════ */
            QPushButton {
                background-color: #dce6ef;
                border: 1px solid #8fa3b8;
                border-bottom: 2px solid #7a96ae;
                border-radius: 0px;
                color: #1c2b3a;
                font-weight: bold;
                min-height: 26px;
                padding: 3px 12px;
            }

            QPushButton:hover {
                background-color: #c8daea;
                border-color: #2c5282;
                border-bottom-color: #1e3a5f;
                color: #1e3a5f;
            }

            QPushButton:pressed {
                background-color: #b0ccdf;
                border-bottom-width: 1px;
                padding-top: 4px;
            }

            QPushButton:disabled {
                background-color: #e4e9ed;
                color: #9aafc0;
                border-color: #c0cdd6;
            }

            /* ═══════════════════════════════════════════
               ЧЕКБОКСЫ И РАДИОКНОПКИ
            ═══════════════════════════════════════════ */
            QCheckBox, QRadioButton {
                color: #1c2b3a;
                spacing: 6px;
                background-color: transparent;
            }

            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: none;
                image: url(resources/checkbox_unchecked.svg);
            }

            QCheckBox::indicator:checked {
                image: url(resources/checkbox_checked.svg);
            }

            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: none;
                image: url(resources/radio_unchecked.svg);
            }

            QRadioButton::indicator:checked {
                image: url(resources/radio_checked.svg);
            }

            /* ═══════════════════════════════════════════
               ТАБЛИЦЫ
            ═══════════════════════════════════════════ */
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #9aafc0;
                gridline-color: #cad5de;
                border-radius: 0px;
                selection-background-color: #dce8f5;
                selection-color: #1c2b3a;
            }

            QTableWidget::item {
                padding: 2px 4px;
            }

            QTableWidget::item:selected {
                background-color: #c8daea;
                color: #1c2b3a;
            }

            QHeaderView::section {
                background-color: #d4dfe8;
                border: none;
                border-right: 1px solid #9aafc0;
                border-bottom: 2px solid #8fa3b8;
                padding: 4px 6px;
                font-weight: bold;
                color: #1e3a5f;
            }

            /* ═══════════════════════════════════════════
               СКРОЛЛБАРЫ
            ═══════════════════════════════════════════ */
            QScrollBar:vertical {
                background-color: #eaecf0;
                width: 12px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background-color: #9aafc0;
                min-height: 24px;
                border: 1px solid #8fa3b8;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #2c5282;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #eaecf0;
                height: 12px;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background-color: #9aafc0;
                min-width: 24px;
                border: 1px solid #8fa3b8;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #2c5282;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }

            /* ═══════════════════════════════════════════
               РАЗДЕЛИТЕЛЬ
            ═══════════════════════════════════════════ */
            QSplitter::handle {
                background-color: #b0bec8;
                width: 3px;
            }

            QSplitter::handle:hover {
                background-color: #2c5282;
            }

            /* ═══════════════════════════════════════════
               СТАТУС-СТРОКА
            ═══════════════════════════════════════════ */
            QStatusBar {
                background-color: #1e3a5f;
                color: #dce8f5;
                border-top: 1px solid #162d4a;
                font-size: 11px;
                padding: 2px 8px;
            }

            /* ═══════════════════════════════════════════
               МЕТКИ И ПРОЧЕЕ
            ═══════════════════════════════════════════ */
            QLabel {
                color: #1c2b3a;
                background-color: transparent;
            }

            QTextBrowser {
                background-color: #eaecf0;
                border: none;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)