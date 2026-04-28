# -*- coding: utf-8 -*-

from datetime import date

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)

from app.constants import (
    PAYMENT_RULE_OPTIONS,
    PAYMENT_RULE_DESCRIPTIONS_SHORT,
    PAYMENT_RULE_DESCRIPTIONS_FULL,
)
from app.services.money_to_text import format_money
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox


class PaymentRuleBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, payment_calculator, parent=None):
        super().__init__("Размер оплаты за 1 рабочий день", parent)

        self.payment_calculator = payment_calculator
        self._loading = False

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.letter_combo = NoWheelComboBox()
        self.letter_combo.view().setMouseTracking(True)

        for display_text, value in PAYMENT_RULE_OPTIONS:
            self.letter_combo.addItem("", value)
            index = self.letter_combo.count() - 1
            self.letter_combo.setItemData(index, display_text, Qt.UserRole + 1)

        self.rule_label = QLabel("из пп. ст. 22 о возмещении процессуальных издержек")
        self.rule_label.setWordWrap(True)

        self.region_checkbox = QCheckBox("+20% (районный коэффициент)")
        self.region_checkbox.setChecked(True)

        self.experience_checkbox = QCheckBox("+30% (непрерывный стаж работы)")
        self.experience_checkbox.setChecked(True)

        checks_row = QHBoxLayout()
        checks_row.addWidget(self.region_checkbox)
        checks_row.addWidget(self.experience_checkbox)
        checks_row.addStretch(1)

        root = QVBoxLayout()
        root.addWidget(self.letter_combo)
        root.addWidget(self.rule_label)
        root.addLayout(checks_row)

        self.setLayout(root)

    def _connect_signals(self):
        self.letter_combo.currentIndexChanged.connect(self._emit_data_changed)
        self.region_checkbox.toggled.connect(self._emit_data_changed)
        self.experience_checkbox.toggled.connect(self._emit_data_changed)

    def _emit_data_changed(self):
        if self._loading:
            return
        self.data_changed.emit()

    def load_from_state(self, state):
        self._loading = True

        self.letter_combo.blockSignals(True)
        self.region_checkbox.blockSignals(True)
        self.experience_checkbox.blockSignals(True)

        reference_date = self._get_reference_date(state)
        self._refresh_combo_items(reference_date)

        for index in range(self.letter_combo.count()):
            if self.letter_combo.itemData(index) == state.payment_rule.letter:
                self.letter_combo.setCurrentIndex(index)
                break

        self.region_checkbox.setChecked(state.payment_rule.add_region_20)
        self.experience_checkbox.setChecked(state.payment_rule.add_experience_30)

        self.letter_combo.blockSignals(False)
        self.region_checkbox.blockSignals(False)
        self.experience_checkbox.blockSignals(False)

        self._loading = False

    def save_to_state(self, state):
        state.payment_rule.letter = self.letter_combo.currentData()
        state.payment_rule.add_region_20 = self.region_checkbox.isChecked()
        state.payment_rule.add_experience_30 = self.experience_checkbox.isChecked()

    def _refresh_combo_items(self, reference_date):
        for index in range(self.letter_combo.count()):
            value = self.letter_combo.itemData(index)
            display_letter = self.letter_combo.itemData(index, Qt.UserRole + 1)

            upper_letter = str(display_letter).upper()
            amount = self.payment_calculator.get_base_rate(value, reference_date)

            short_text = PAYMENT_RULE_DESCRIPTIONS_SHORT.get(value, "")
            full_text = PAYMENT_RULE_DESCRIPTIONS_FULL.get(value, "")

            item_text = "{0} - {1} - {2}".format(
                upper_letter,
                format_money(amount),
                short_text,
            )

            self.letter_combo.setItemText(index, item_text)
            self.letter_combo.setItemData(index, full_text, Qt.ToolTipRole)

        self.letter_combo.setToolTip(
            "Сумма в списке рассчитана по дате: {0}".format(
                reference_date.strftime("%d.%m.%Y") if reference_date else "-"
            )
        )

    @staticmethod
    def _get_reference_date(state):
        service_dates = [
            item.service_date
            for item in state.services
            if item.service_date is not None
        ]
        if service_dates:
            return max(service_dates)

        event_dates = [
            item.event_date
            for item in state.events
            if item.event_date is not None
        ]
        if event_dates:
            return max(event_dates)

        verdict_date = state.case_card.verdict_date
        if verdict_date:
            return verdict_date

        return date.today()