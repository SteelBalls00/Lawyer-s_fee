# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
)


class CaseInfoBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Информация по делу", parent)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.case_number_edit = QLineEdit()
        self.uid_edit = QLineEdit()
        self.decree_date_edit = QLineEdit()
        self.judge_edit = QLineEdit()
        self.secretary_edit = QLineEdit()
        self.prosecutor_edit = QLineEdit()
        self.verdict_date_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("№ дела", self.case_number_edit)
        form.addRow("УИД", self.uid_edit)
        form.addRow("Дата постановления", self.decree_date_edit)
        form.addRow("Судья", self.judge_edit)
        form.addRow("Секретарь", self.secretary_edit)
        form.addRow("Гос. обвинитель", self.prosecutor_edit)
        form.addRow("Дата приговора", self.verdict_date_edit)

        self.setLayout(form)

    def _connect_signals(self):
        edits = [
            self.case_number_edit,
            self.uid_edit,
            self.decree_date_edit,
            self.judge_edit,
            self.secretary_edit,
            self.prosecutor_edit,
            self.verdict_date_edit,
        ]
        for edit in edits:
            edit.textChanged.connect(self.data_changed.emit)

    def load_from_state(self, state):
        self._load_edit(self.case_number_edit, state.case_number)
        self._load_edit(self.uid_edit, state.judicial_uid)
        self._load_edit(self.decree_date_edit, state.decree_date)
        self._load_edit(self.judge_edit, state.judge)
        self._load_edit(self.secretary_edit, state.secretary)
        self._load_edit(self.prosecutor_edit, state.prosecutor)
        self._load_edit(self.verdict_date_edit, state.verdict_date)

    def save_to_state(self, state):
        state.case_number.set_user_value(self.case_number_edit.text())
        state.judicial_uid.set_user_value(self.uid_edit.text())
        state.decree_date.set_user_value(self.decree_date_edit.text())
        state.judge.set_user_value(self.judge_edit.text())
        state.secretary.set_user_value(self.secretary_edit.text())
        state.prosecutor.set_user_value(self.prosecutor_edit.text())
        state.verdict_date.set_user_value(self.verdict_date_edit.text())

    @staticmethod
    def _load_edit(edit, editable_field):
        edit.blockSignals(True)
        edit.setText(editable_field.user_value)
        edit.setPlaceholderText(editable_field.db_value)
        edit.blockSignals(False)