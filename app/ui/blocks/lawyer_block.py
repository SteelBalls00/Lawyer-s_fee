# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)
from app.services.money_to_text import to_decimal_money, format_money_for_edit
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox


class LawyerBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Информация об адвокате", parent)

        self._lawyers = []
        self._loading = False

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.lawyer_combo = NoWheelComboBox()
        self.claimed_amount_edit = QLineEdit()
        self.claimed_amount_edit.setPlaceholderText("Введите сумму")

        self.recipient_label = QLabel("-")
        self.inn_label = QLabel("-")
        self.kpp_label = QLabel("-")
        self.account_label = QLabel("-")
        self.bank_label = QLabel("-")
        self.bik_label = QLabel("-")
        self.corr_account_label = QLabel("-")

        top_form = QFormLayout()
        top_form.addRow("Адвокат", self.lawyer_combo)
        top_form.addRow("Заявлено адвокатом", self.claimed_amount_edit)

        details_form = QFormLayout()
        details_form.addRow("Получатель", self.recipient_label)
        details_form.addRow("ИНН", self.inn_label)
        details_form.addRow("КПП", self.kpp_label)
        details_form.addRow("Расч. счёт", self.account_label)
        details_form.addRow("Банк", self.bank_label)
        details_form.addRow("БИК", self.bik_label)
        details_form.addRow("Корр. счёт", self.corr_account_label)

        root = QVBoxLayout()
        root.addLayout(top_form)
        root.addLayout(details_form)

        self.setLayout(root)

    def _connect_signals(self):
        self.lawyer_combo.currentIndexChanged.connect(self._on_current_changed)
        self.lawyer_combo.currentIndexChanged.connect(self.data_changed.emit)
        self.claimed_amount_edit.textChanged.connect(self._on_claimed_amount_changed)

    def load_from_state(self, state):
        self._lawyers = list(state.lawyers)

        self._loading = True

        self.lawyer_combo.blockSignals(True)
        self.claimed_amount_edit.blockSignals(True)

        self.lawyer_combo.clear()

        for lawyer in self._lawyers:
            self.lawyer_combo.addItem(lawyer.fio)

        if self._lawyers:
            index = min(state.selected_lawyer_index, len(self._lawyers) - 1)
            self.lawyer_combo.setCurrentIndex(index)
            self._apply_lawyer(index)
        else:
            self._clear_labels()

        self.claimed_amount_edit.setText(
            format_money_for_edit(state.lawyer_claimed_amount)
            if state.lawyer_claimed_amount
            else ""
        )

        self.lawyer_combo.blockSignals(False)
        self.claimed_amount_edit.blockSignals(False)

        self._loading = False

    def save_to_state(self, state):
        index = self.lawyer_combo.currentIndex()
        if index < 0:
            state.selected_lawyer_index = 0
        else:
            state.selected_lawyer_index = index

        state.lawyer_claimed_amount = to_decimal_money(self.claimed_amount_edit.text())

    def _on_current_changed(self, index):
        self._apply_lawyer(index)

    def _on_claimed_amount_changed(self, text):
        if self._loading:
            return

        cleaned = self._clean_money_text(text)

        if text != cleaned:
            self._loading = True
            self.claimed_amount_edit.setText(cleaned)
            self.claimed_amount_edit.setCursorPosition(len(cleaned))
            self._loading = False

        self.data_changed.emit()

    @staticmethod
    def _clean_money_text(text):
        result = []
        comma_used = False

        for ch in text:
            if ch.isdigit():
                result.append(ch)
            elif ch in ",." and not comma_used:
                result.append(",")
                comma_used = True

        if comma_used:
            left, right = "".join(result).split(",", 1)
            right = right[:2]
            return left + "," + right

        return "".join(result)

    def _apply_lawyer(self, index):
        if not (0 <= index < len(self._lawyers)):
            self._clear_labels()
            return

        lawyer = self._lawyers[index]
        self.recipient_label.setText(lawyer.recipient_name or "-")
        self.inn_label.setText(lawyer.inn or "-")
        self.kpp_label.setText(lawyer.kpp or "-")
        self.account_label.setText(lawyer.account or "-")
        self.bank_label.setText(lawyer.bank or "-")
        self.bik_label.setText(lawyer.bik or "-")
        self.corr_account_label.setText(lawyer.corr_account or "-")

    def _clear_labels(self):
        self.recipient_label.setText("-")
        self.inn_label.setText("-")
        self.kpp_label.setText("-")
        self.account_label.setText("-")
        self.bank_label.setText("-")
        self.bik_label.setText("-")
        self.corr_account_label.setText("-")