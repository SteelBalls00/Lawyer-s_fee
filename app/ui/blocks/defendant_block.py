# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox


class DefendantBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Информация о подсудимом", parent)

        self._defendants = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.defendant_combo = NoWheelComboBox()
        self.custody_checkbox = QCheckBox("Находился под стражей")

        self.sex_label = QLabel("-")
        self.native_label = QLabel("-")
        self.birth_date_label = QLabel("-")
        self.article_label = QLabel("-")

        top_form = QFormLayout()
        top_form.addRow("Подсудимый", self.defendant_combo)

        details_form = QFormLayout()
        details_form.addRow("Пол", self.sex_label)
        details_form.addRow("Уроженец", self.native_label)
        details_form.addRow("Дата рождения", self.birth_date_label)
        details_form.addRow("Основная статья", self.article_label)

        root = QVBoxLayout()
        root.addLayout(top_form)
        root.addWidget(self.custody_checkbox)
        root.addLayout(details_form)

        self.setLayout(root)

    def _connect_signals(self):
        self.defendant_combo.currentIndexChanged.connect(self._on_current_changed)
        self.defendant_combo.currentIndexChanged.connect(self.data_changed.emit)
        self.custody_checkbox.toggled.connect(self.data_changed.emit)

    def load_from_state(self, state):
        self._defendants = list(state.defendants)

        self.defendant_combo.blockSignals(True)
        self.custody_checkbox.blockSignals(True)

        self.defendant_combo.clear()

        for item in self._defendants:
            text = "{0} — {1}".format(item.fio, item.article)
            self.defendant_combo.addItem(text)

        if self._defendants:
            index = min(state.selected_defendant_index, len(self._defendants) - 1)
            self.defendant_combo.setCurrentIndex(index)
            self._apply_defendant(index)
        else:
            self.sex_label.setText("-")
            self.native_label.setText("-")
            self.birth_date_label.setText("-")
            self.article_label.setText("-")
            self.custody_checkbox.setChecked(False)

        self.defendant_combo.blockSignals(False)
        self.custody_checkbox.blockSignals(False)

    def save_to_state(self, state):
        index = self.defendant_combo.currentIndex()
        if index < 0:
            state.selected_defendant_index = 0
            return

        state.selected_defendant_index = index

        defendant = state.selected_defendant
        if defendant is not None:
            defendant.in_custody = self.custody_checkbox.isChecked()

    def _on_current_changed(self, index):
        self._apply_defendant(index)

    def _apply_defendant(self, index):
        if not (0 <= index < len(self._defendants)):
            self.sex_label.setText("-")
            self.native_label.setText("-")
            self.birth_date_label.setText("-")
            self.article_label.setText("-")
            self.custody_checkbox.setChecked(False)
            return

        defendant = self._defendants[index]
        self.sex_label.setText(defendant.sex or "-")
        self.native_label.setText(defendant.native or "-")
        self.birth_date_label.setText(
            defendant.birth_date.strftime("%d.%m.%Y") if defendant.birth_date else "-"
        )
        self.article_label.setText(defendant.article or "-")
        self.custody_checkbox.setChecked(defendant.in_custody)