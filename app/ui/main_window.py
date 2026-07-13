# -*- coding: utf-8 -*-
import os
import sys

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QWidget,
)
from app.services.money_to_text import format_money

from app.constants import WINDOW_TITLE
from app.ui.panels.info_panel import InfoPanel
from app.ui.panels.preview_panel import PreviewPanel
from app.ui.panels.archive_panel import ArchivePanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        state,
        case_controller,
        payment_calculator,
        preview_renderer,
        save_controller,
        declension_cache=None,
        user_settings=None,
        field_history=None,
        auth_service=None,
        decree_archive=None,
        team_service=None,
        parent=None,
    ):
        super().__init__(parent)

        self.state = state
        self.case_controller = case_controller
        self.payment_calculator = payment_calculator
        self.preview_renderer = preview_renderer
        self.save_controller = save_controller
        self.declension_cache = declension_cache
        self.user_settings = user_settings
        self.field_history = field_history
        self.auth_service = auth_service
        self.decree_archive = decree_archive
        self.team_service = team_service

        # Авторизованный пользователь (None до входа)
        self.current_user = None

        # Отслеживаем ФИО адвоката, чтобы при смене загружать кеш
        self._loaded_lawyer_fio = None

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
        # До авторизации сохранение недоступно
        self.save_docx_action.setEnabled(False)
        self.save_docx_action.setToolTip("Сначала вам нужно авторизоваться.")

        self.check_template_action = QAction("Проверить шаблон", self)
        self.check_template_action.triggered.connect(self._on_check_template)

        toolbar = self.addToolBar("Документ")
        toolbar.setMovable(False)
        toolbar.addAction(self.save_docx_action)
        # toolbar.addAction(self.check_template_action)
        toolbar.addSeparator()

        # Информер по суммам справа от кнопок
        self.amounts_label = QLabel()
        self.amounts_label.setTextFormat(Qt.RichText)
        self.amounts_label.setContentsMargins(12, 0, 12, 0)
        toolbar.addWidget(self.amounts_label)

        toolbar.addSeparator()

        self.declensions_action = QAction("Склонения", self)
        self.declensions_action.triggered.connect(self._on_open_declensions)
        toolbar.addAction(self.declensions_action)

        toolbar.addSeparator()

        self.archive_action = QAction("Архив\nпостановлений", self)
        self.archive_action.triggered.connect(self._on_toggle_archive)
        toolbar.addAction(self.archive_action)
        if self.decree_archive is None:
            self.archive_action.setEnabled(False)
            self.archive_action.setToolTip(
                "В config.ini не настроена секция [archive]."
            )

        # Распорка, чтобы блок авторизации прижался вправо
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        toolbar.addWidget(spacer)

        # Приветствие — слева от поля пароля
        self.auth_status_label = QLabel("")
        self.auth_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.auth_status_label.setStyleSheet(
            "color: #dce8f5; font-weight: bold; font-size: 12px; "
            "padding: 0 12px; background: transparent;"
        )
        toolbar.addWidget(self.auth_status_label)

        # Поле ввода пароля прямо в тулбаре — без отдельных окон.
        self.auth_password_edit = QLineEdit()
        self.auth_password_edit.setEchoMode(QLineEdit.Password)
        self.auth_password_edit.setPlaceholderText("Пароль от ГАС СДП")
        self.auth_password_edit.setToolTip("Введите пароль и нажмите Enter")
        self.auth_password_edit.setFixedWidth(180)
        self.auth_password_edit.returnPressed.connect(self._try_login)
        self.auth_password_edit.textChanged.connect(self._reset_auth_error)
        toolbar.addWidget(self.auth_password_edit)

        # Кнопка входа — постоянная, чтобы всегда можно было сменить пользователя
        self.login_action = QAction("Войти", self)
        self.login_action.triggered.connect(self._try_login)
        toolbar.addAction(self.login_action)

        if self.auth_service is None:
            self.auth_password_edit.setEnabled(False)
            self.auth_password_edit.setToolTip("Авторизация недоступна")
            self.login_action.setEnabled(False)

    def _build_ui(self):
        self.info_panel = InfoPanel(
            state=self.state,
            case_controller=self.case_controller,
            payment_calculator=self.payment_calculator,
            field_history=self.field_history,
            parent=self,
        )
        self.info_panel.setMinimumWidth(620)

        self.preview_panel = PreviewPanel(
            preview_renderer=self.preview_renderer,
            parent=self,
        )

        self.archive_panel = ArchivePanel(parent=self)
        self.archive_panel.record_selected.connect(self._on_archive_record_selected)
        self.archive_panel.record_chosen.connect(self._on_archive_record_chosen)

        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.preview_panel)   # index 0
        self.right_stack.addWidget(self.archive_panel)   # index 1

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.info_panel)
        splitter.addWidget(self.right_stack)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([640, 960])

        self.setCentralWidget(splitter)

        self.statusBar().showMessage("Готово")

        # Шестерёнка настроек составов — правый нижний угол, видна только админам
        self.admin_gear_btn = QToolButton()
        self.admin_gear_btn.setText("\u2699")
        self.admin_gear_btn.setToolTip("Настройка составов (администратор)")
        self.admin_gear_btn.setCursor(Qt.PointingHandCursor)
        self.admin_gear_btn.setStyleSheet(
            "QToolButton { color: #dce8f5; background: transparent; border: none;"
            " font-size: 16px; padding: 0 8px; min-height: 18px; }"
            "QToolButton:hover { color: #ffffff; background: #2c5282; }"
        )
        self.admin_gear_btn.clicked.connect(self._on_open_team_settings)
        self.admin_gear_btn.setVisible(False)
        self.statusBar().addPermanentWidget(self.admin_gear_btn)

    def _connect_signals(self):
        self.info_panel.data_changed.connect(self.refresh_preview)
        self.info_panel.status_message.connect(self.statusBar().showMessage)

    def refresh_preview(self):
        self.preview_panel.update_preview(self.state)
        self._update_amounts_info()

    def _update_amounts_info(self):
        claimed = self.state.lawyer_claimed_amount
        services_total = self.payment_calculator.get_services_total(self.state.services)

        claimed_str = format_money(claimed)
        services_str = format_money(services_total)

        # Абсолютный путь к значкам (работает и после сборки PyInstaller)
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(sys.argv[0]))
        res_dir = os.path.join(base, "resources").replace("\\", "/")

        if claimed == services_total and claimed > 0:
            icon = "amount_match.svg"
            sum_color = "#b8e8c5"
        elif claimed == 0 and services_total == 0:
            icon = "amount_neutral.svg"
            sum_color = "#dce8f5"
        else:
            icon = "amount_mismatch.svg"
            sum_color = "#ffd0a8"

        icon_path = "{0}/{1}".format(res_dir, icon)

        self.amounts_label.setText(
            '<table cellpadding="0" cellspacing="0"><tr>'
            '<td valign="middle"><img src="{icon}" width="26" height="26"></td>'
            '<td valign="middle">&nbsp;&nbsp;</td>'
            '<td valign="middle">'
            '<span style="color:#cfd5db;font-size:14px;">Заявлено адвокатом:</span> '
            '<span style="color:{c};font-weight:bold;font-size:15px;">{claimed}</span>'
            '<span style="color:#cfd5db;font-size:14px;">&nbsp;&nbsp;&nbsp;&nbsp;Сумма услуг:</span> '
            '<span style="color:{c};font-weight:bold;font-size:15px;">{services}</span>'
            '</td></tr></table>'.format(
                icon=icon_path,
                c=sum_color,
                claimed=claimed_str,
                services=services_str,
            )
        )

    def _on_open_declensions(self):
        self.info_panel.save_to_state()

        try:
            template_tags = self.save_controller.get_template_tags()
        except Exception:
            template_tags = []

        tag_resolver = self.preview_renderer.tag_resolver
        morphology = tag_resolver.morphology

        from app.ui.dialogs.declension_dialog import DeclensionDialog

        dialog = DeclensionDialog(
            state=self.state,
            tag_resolver=tag_resolver,
            morphology_service=morphology,
            template_tags=template_tags,
            declension_cache=self.declension_cache,
            parent=self,
        )

        if dialog.exec_() == dialog.Accepted:
            self._loaded_lawyer_fio = None   # перечитать кеш после правок
            self.refresh_preview()

    def _try_login(self):
        """Вход по Enter в поле пароля. Повторный ввод — смена пользователя."""
        if self.auth_service is None:
            return

        password = self.auth_password_edit.text().strip()
        if not password:
            self._mark_auth_error("Введите пароль")
            return

        try:
            username = self.auth_service.authenticate(password)
        except Exception as exc:
            self._mark_auth_error("Ошибка подключения к БД")
            self.statusBar().showMessage(
                "Ошибка авторизации: {0}".format(exc)
            )
            return

        if not username:
            self._mark_auth_error("Неверный пароль")
            self.auth_password_edit.selectAll()
            self.auth_password_edit.setFocus()
            return

        # Успех: очищаем поле, показываем приветствие справа
        self.current_user = username
        self.auth_password_edit.clear()

        self.auth_status_label.setText(
            "Здравствуйте,\n{0}".format(self.current_user)
        )

        self.save_docx_action.setEnabled(True)
        self.save_docx_action.setToolTip("")

        # Показать шестерёнку, если пользователь — администратор
        self._update_admin_gear()

        self.statusBar().showMessage(
            "Авторизация выполнена: {0}".format(self.current_user)
        )

    def _update_admin_gear(self):
        """Шестерёнка видна только администраторам (таблица ADMINS архивной БД)."""
        visible = False
        if self.team_service and self.current_user:
            try:
                visible = self.team_service.is_admin(self.current_user)
            except Exception:
                visible = False
        self.admin_gear_btn.setVisible(visible)

    def _on_open_team_settings(self):
        if self.team_service is None:
            return

        from app.ui.dialogs.team_settings_dialog import TeamSettingsDialog

        main_db = self.auth_service.db if self.auth_service else None
        dialog = TeamSettingsDialog(
            team_service=self.team_service,
            main_db=main_db,
            parent=self,
        )
        dialog.exec_()

    def _mark_auth_error(self, message):
        """Подсветить поле пароля красной рамкой и показать сообщение."""
        self.auth_password_edit.setStyleSheet(
            "border: 1px solid #d9534f; background-color: #fff5f5;"
        )
        self.statusBar().showMessage(message)

    def _reset_auth_error(self, _text=""):
        """Вернуть обычный вид поля пароля при изменении текста."""
        self.auth_password_edit.setStyleSheet("")

    def _on_toggle_archive(self):
        # Повторное нажатие — вернуть предпросмотр
        if self.right_stack.currentIndex() == 1:
            self.right_stack.setCurrentIndex(0)
            return

        if self.decree_archive is None:
            return

        if not self.current_user:
            QMessageBox.information(
                self,
                "Архив постановлений",
                "Сначала вам нужно авторизоваться.",
            )
            return

        try:
            usernames = [self.current_user]
            if self.team_service:
                try:
                    usernames = self.team_service.get_group_usernames(
                        self.current_user
                    )
                except Exception:
                    usernames = [self.current_user]
            records = self.decree_archive.list_decrees(usernames)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Архив постановлений",
                "Не удалось загрузить архив:\n{0}".format(exc),
            )
            return

        self.archive_panel.set_records(records)
        self.right_stack.setCurrentIndex(1)

    def _load_snapshot(self, decree_id, mode):
        """Достаёт снапшот и применяет к state. Возвращает snapshot или None."""
        from app.services.state_serializer import apply_dict_to_state

        snapshot = self.decree_archive.get_snapshot(decree_id)
        if snapshot is None:
            QMessageBox.warning(
                self,
                "Архив постановлений",
                "Не удалось прочитать данные постановления.",
            )
            return None

        if mode == "full":
            self.state.reset_case_related_data()

        apply_dict_to_state(self.state, snapshot, mode=mode)
        return snapshot

    def _on_archive_record_selected(self, decree_id):
        """Клик по записи архива: показать её данные в полях слева."""
        if self.decree_archive is None:
            return

        scroll_pos = self.info_panel.get_scroll_value()

        if self._load_snapshot(decree_id, mode="full") is None:
            return

        self.info_panel.refresh_from_state()

        # Вернуть прокрутку после перерисовки полей
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.info_panel.set_scroll_value(scroll_pos))

        self._update_amounts_info()
        self.preview_panel.update_preview(self.state)

    def _on_archive_record_chosen(self, decree_id):
        """Кнопка «Загрузить по делу\nновые данные»: обновить дело из БД и наложить архивные данные."""
        if self.decree_archive is None:
            return

        snapshot = self.decree_archive.get_snapshot(decree_id)
        if snapshot is None:
            QMessageBox.warning(
                self,
                "Архив постановлений",
                "Не удалось прочитать данные постановления.",
            )
            return

        case_number = ((snapshot.get("fields") or {})
                       .get("case_number") or {})
        number = (case_number.get("user") or case_number.get("db") or "").strip()
        source = snapshot.get("case_source") or ""

        loaded_fresh = False
        if number and source in ("u1", "m"):
            try:
                loaded_fresh = self.case_controller.load_case(number, source)
            except Exception:
                loaded_fresh = False

        from app.services.state_serializer import apply_dict_to_state

        if loaded_fresh:
            # Свежие данные из БД + архивные правки поверх
            apply_dict_to_state(self.state, snapshot, mode="overlay")
            self.statusBar().showMessage(
                "Дело обновлено из БД, применены данные постановления"
            )
        else:
            # БД недоступна или дело не нашлось — восстанавливаем целиком из архива
            self.state.reset_case_related_data()
            apply_dict_to_state(self.state, snapshot, mode="full")
            self.statusBar().showMessage(
                "Данные восстановлены из архива (без обновления из БД)"
            )

        self.info_panel.refresh_from_state()
        self.right_stack.setCurrentIndex(0)
        self.refresh_preview()

    def _save_decree_to_archive(self):
        """Пишет текущее постановление в архивную БД."""
        if self.decree_archive is None or not self.current_user:
            return

        services_total = self.payment_calculator.get_services_total(
            self.state.services
        )
        if self.state.use_extra_decrees:
            extra_total = self.payment_calculator.get_extra_decrees_total(
                self.state.extra_decrees
            )
        else:
            extra_total = 0
        full_total = services_total + extra_total

        try:
            self.decree_archive.save_decree(
                self.state,
                self.current_user,
                services_total,
                extra_total,
                full_total,
            )
        except Exception as exc:
            self.statusBar().showMessage(
                "Постановление сохранено, но запись в архив не удалась: {0}".format(exc)
            )

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

        # Запомненная директория сохранения
        last_dir = ""
        if self.user_settings:
            last_dir = self.user_settings.get_last_save_dir() or ""

        if last_dir and os.path.isdir(last_dir):
            initial_path = os.path.join(last_dir, default_name)
        else:
            initial_path = default_name

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить постановление",
            initial_path,
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

        # Запоминаем директорию сохранения для следующего раза
        if self.user_settings and saved_path:
            self.user_settings.set_last_save_dir(os.path.dirname(saved_path))

        # Запоминаем использованные значения секретаря и обвинителя
        self.info_panel.case_info_block.commit_history()

        # Пишем постановление в архивную БД
        self._save_decree_to_archive()

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
            
            QGroupBox:disabled {
                color: #a0aab4;
                border-top-color: #c5d0db;
            }

            QGroupBox::title:disabled {
                color: #a0aab4;
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
            
            QRadioButton:disabled {
                color: #a0aab4;
            }

            QRadioButton::indicator:disabled {
                image: url(resources/radio_unchecked.svg);
                opacity: 0.5;
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
            
            QCheckBox:disabled {
                color: #a0aab4;
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
            
            QLabel:disabled {
                color: #a0aab4;
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