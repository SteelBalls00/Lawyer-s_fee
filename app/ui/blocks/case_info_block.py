# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QWidget,
)
from app.ui.widgets.history_line_edit import HistoryLineEdit


class CaseInfoBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, field_history=None, parent=None):
        super().__init__("Информация по делу", parent)

        self.field_history = field_history

        self._build_ui()
        self._connect_signals()
        self._load_history_values()

    def _build_ui(self):
        self.case_number_edit = QLineEdit()
        self.uid_edit = QLineEdit()
        self.decree_date_edit = QLineEdit()
        self.judge_edit = QLineEdit()
        self.secretary_edit = HistoryLineEdit()
        self.prosecutor_edit = HistoryLineEdit()
        self.verdict_date_edit = QLineEdit()

        # Поля только для уголовных материалов
        self.sub_type_edit = QLineEdit()
        self.sub_type_label = QLabel("Предмет представления,\nходатайства, жалобы")

        self.radio_petition = QRadioButton("ходатайство")
        self.radio_representation = QRadioButton("представление")
        self.radio_petition.setChecked(True)
        self._petition_group = QButtonGroup(self)
        self._petition_group.addButton(self.radio_petition)
        self._petition_group.addButton(self.radio_representation)

        self.petition_row_widget = QWidget()
        petition_row = QHBoxLayout(self.petition_row_widget)
        petition_row.setContentsMargins(0, 0, 0, 0)
        self.petition_row_widget.setStyleSheet("background: transparent;")
        petition_row.addWidget(self.radio_petition)
        petition_row.addWidget(self.radio_representation)
        petition_row.addStretch(1)

        self.petition_label = QLabel("Предмет рассмотрения")

        self._form = QFormLayout()
        self._form.addRow("№ дела", self.case_number_edit)
        self._form.addRow("УИД", self.uid_edit)
        self._form.addRow("Дата постановления", self.decree_date_edit)
        self._form.addRow("Судья", self.judge_edit)
        self._form.addRow("Секретарь", self.secretary_edit)
        self._form.addRow("Гос. обвинитель", self.prosecutor_edit)
        self._form.addRow("Дата приговора", self.verdict_date_edit)
        self._form.addRow(self.sub_type_label, self.sub_type_edit)
        self._form.addRow(self.petition_label, self.petition_row_widget)

        # По умолчанию скрываем поля для материалов
        self._set_materials_fields_visible(False)

        self.setLayout(self._form)

    def _connect_signals(self):
        edits = [
            self.case_number_edit,
            self.uid_edit,
            self.decree_date_edit,
            self.judge_edit,
            self.secretary_edit,
            self.prosecutor_edit,
            self.verdict_date_edit,
            self.sub_type_edit,
        ]
        for edit in edits:
            edit.textChanged.connect(self.data_changed.emit)

        self.radio_petition.toggled.connect(self.data_changed.emit)
        self.radio_representation.toggled.connect(self.data_changed.emit)

    def _set_materials_fields_visible(self, visible):
        """Поля sub_type и petition радиокнопки видны только для материалов."""
        self.sub_type_label.setVisible(visible)
        self.sub_type_edit.setVisible(visible)
        self.petition_label.setVisible(visible)
        self.petition_row_widget.setVisible(visible)

    def load_from_state(self, state):
        self._load_edit(self.case_number_edit, state.case_number)
        self._load_edit(self.uid_edit, state.judicial_uid)
        self._load_edit(self.decree_date_edit, state.decree_date)
        self._load_edit(self.judge_edit, state.judge)
        self._load_edit(self.secretary_edit, state.secretary, hint="(не склоняется автоматически)")
        self._load_edit(self.prosecutor_edit, state.prosecutor, hint="(не склоняется автоматически)")
        self._load_edit(self.verdict_date_edit, state.verdict_date)
        self._load_edit(self.sub_type_edit, state.case_sub_type)

        is_materials = getattr(state, "case_source", "") == "m"
        self._set_materials_fields_visible(is_materials)

        self.radio_petition.blockSignals(True)
        self.radio_representation.blockSignals(True)
        is_petition = getattr(state, "petition_or_representation", "petition") == "petition"
        self.radio_petition.setChecked(is_petition)
        self.radio_representation.setChecked(not is_petition)
        self.radio_petition.blockSignals(False)
        self.radio_representation.blockSignals(False)

    def save_to_state(self, state):
        state.case_number.set_user_value(self.case_number_edit.text())
        state.judicial_uid.set_user_value(self.uid_edit.text())
        state.decree_date.set_user_value(self.decree_date_edit.text())
        state.judge.set_user_value(self.judge_edit.text())
        state.secretary.set_user_value(self.secretary_edit.text())
        state.prosecutor.set_user_value(self.prosecutor_edit.text())
        state.verdict_date.set_user_value(self.verdict_date_edit.text())
        state.case_sub_type.set_user_value(self.sub_type_edit.text())

        if self.radio_petition.isChecked():
            state.petition_or_representation = "petition"
        else:
            state.petition_or_representation = "representation"

    def _load_history_values(self):
        """Подгружает варианты автодополнения из истории."""
        if not self.field_history:
            return
        self.secretary_edit.set_history_values(
            self.field_history.get_values("secretary")
        )
        self.prosecutor_edit.set_history_values(
            self.field_history.get_values("prosecutor")
        )

    def commit_history(self):
        """Сохраняет текущие значения секретаря и обвинителя в историю.

        Вызывается при сохранении постановления (значение «использовано»).
        """
        if not self.field_history:
            return

        secretary = self.secretary_edit.text().strip()
        prosecutor = self.prosecutor_edit.text().strip()

        if secretary:
            self.field_history.add_value("secretary", secretary)
        if prosecutor:
            self.field_history.add_value("prosecutor", prosecutor)

        # Обновляем выпадающие списки, чтобы свежие значения сразу появились
        self._load_history_values()

    @staticmethod
    def _load_edit(edit, editable_field, hint=None):
        edit.blockSignals(True)
        edit.setText(editable_field.user_value)
        # Если есть значение из БД — показываем его как подсказку,
        # иначе показываем переданный hint (например, «(не склоняется)»)
        if editable_field.db_value:
            edit.setPlaceholderText(editable_field.db_value)
        elif hint:
            edit.setPlaceholderText(hint)
        else:
            edit.setPlaceholderText("")
        edit.blockSignals(False)
