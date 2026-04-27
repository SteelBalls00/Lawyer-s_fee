# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
)


class TotalBlock(QGroupBox):
    def __init__(self, payment_calculator, parent=None):
        super().__init__("Итог", parent)

        self.payment_calculator = payment_calculator
        self._build_ui()

    def _build_ui(self):
        self.services_total_edit = QLineEdit()
        self.extra_decrees_total_edit = QLineEdit()
        self.full_total_edit = QLineEdit()

        self.services_total_edit.setReadOnly(True)
        self.extra_decrees_total_edit.setReadOnly(True)
        self.full_total_edit.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Сумма услуг адвоката", self.services_total_edit)
        form.addRow("Сумма доп. постановлений", self.extra_decrees_total_edit)
        form.addRow("Сумма вознаграждения в суде и на следствии", self.full_total_edit)

        self.setLayout(form)

    def load_from_state(self, state):
        services_total = self.payment_calculator.get_services_total(state.services)

        if state.use_extra_decrees:
            extra_total = self.payment_calculator.get_extra_decrees_total(state.extra_decrees)
        else:
            extra_total = 0

        full_total = services_total + extra_total

        self.services_total_edit.setText(str(services_total))
        self.extra_decrees_total_edit.setText(str(extra_total))
        self.full_total_edit.setText(str(full_total))