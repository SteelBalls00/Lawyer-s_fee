# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from app.constants import PAYMENT_RULE_OPTIONS


class PaymentRuleBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Размер оплаты за 1 рабочий день", parent)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.letter_combo = QComboBox()
        for display_text, value in PAYMENT_RULE_OPTIONS:
            self.letter_combo.addItem(display_text, value)

        self.rule_label = QLabel("из пп. ст. 22 о возмещении процессуальных издержек")

        self.region_checkbox = QCheckBox("+20% (районный коэффициент)")
        self.region_checkbox.setChecked(True)

        self.experience_checkbox = QCheckBox("+30% (непрерывный стаж работы)")
        self.experience_checkbox.setChecked(True)

        top_row = QHBoxLayout()
        top_row.addWidget(self.letter_combo)
        top_row.addWidget(self.rule_label, 1)

        checks_row = QHBoxLayout()
        checks_row.addWidget(self.region_checkbox)
        checks_row.addWidget(self.experience_checkbox)
        checks_row.addStretch(1)

        root = QVBoxLayout()
        root.addLayout(top_row)
        root.addLayout(checks_row)

        self.setLayout(root)

    def _connect_signals(self):
        self.letter_combo.currentIndexChanged.connect(self.data_changed.emit)
        self.region_checkbox.toggled.connect(self.data_changed.emit)
        self.experience_checkbox.toggled.connect(self.data_changed.emit)

    def load_from_state(self, state):
        self.letter_combo.blockSignals(True)
        self.region_checkbox.blockSignals(True)
        self.experience_checkbox.blockSignals(True)

        for index in range(self.letter_combo.count()):
            if self.letter_combo.itemData(index) == state.payment_rule.letter:
                self.letter_combo.setCurrentIndex(index)
                break

        self.region_checkbox.setChecked(state.payment_rule.add_region_20)
        self.experience_checkbox.setChecked(state.payment_rule.add_experience_30)

        self.letter_combo.blockSignals(False)
        self.region_checkbox.blockSignals(False)
        self.experience_checkbox.blockSignals(False)

    def save_to_state(self, state):
        state.payment_rule.letter = self.letter_combo.currentData()
        state.payment_rule.add_region_20 = self.region_checkbox.isChecked()
        state.payment_rule.add_experience_30 = self.experience_checkbox.isChecked()