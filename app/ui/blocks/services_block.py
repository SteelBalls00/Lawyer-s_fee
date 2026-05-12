# -*- coding: utf-8 -*-

from datetime import date, datetime

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.constants import LAWYER_SERVICE_TYPES
from app.state import ServiceRow
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox
from app.services.money_to_text import to_decimal_money, format_money_for_edit, format_money


class ServicesBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, state, payment_calculator, parent=None):
        super().__init__("Услуги адвоката", parent)

        self.state = state
        self.payment_calculator = payment_calculator
        self._loading = False

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Дата", "Событие", "Сумма"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setColumnWidth(0, 88)
        self.table.setColumnWidth(2, 78)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)

        self.add_button = QPushButton("Добавить")
        self.add_all_sessions_button = QPushButton("Добавить все с/з")
        self.delete_button = QPushButton("Удалить")

        self.summary_label = QLabel("Число дней 0, Сумма: 0")

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.add_all_sessions_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch(1)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.table, 1)
        top_layout.addLayout(buttons_layout)

        root = QVBoxLayout()
        root.addLayout(top_layout)
        root.addWidget(self.summary_label)

        self.setLayout(root)

    def _connect_signals(self):
        self.add_button.clicked.connect(self._on_add_clicked)
        self.add_all_sessions_button.clicked.connect(self._on_add_all_sessions_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.table.itemChanged.connect(self._on_item_changed)

    def load_from_state(self, state):
        self._loading = True
        self.table.setRowCount(0)

        for service in state.services:
            self._append_row(
                service_date=service.service_date,
                service_name=service.service_name,
                amount=service.amount,
                is_session=service.is_session,
            )

        self._loading = False
        self._update_summary()

    def save_to_state(self, state):
        services = []

        for row in range(self.table.rowCount()):
            service_date = self._get_row_date(row)
            service_name = self._get_row_service_name(row)
            amount = self._get_row_amount(row)

            services.append(
                ServiceRow(
                    service_date=service_date,
                    service_name=service_name,
                    amount=amount,
                    is_session=(service_name == "Участие в судебном заседании"),
                )
            )

        state.services = services

    def recalculate_all_amounts(self):
        self._loading = True
        for row in range(self.table.rowCount()):
            self._recalculate_row_amount(row)
        self._loading = False
        self._update_summary()
        self.data_changed.emit()

    def _on_add_clicked(self):
        default_date = date.today()
        default_service = LAWYER_SERVICE_TYPES[0]
        default_amount = self.payment_calculator.get_amount_for_date(
            self.state.payment_rule,
            default_date,
        )

        self._loading = True
        self._append_row(
            service_date=default_date,
            service_name=default_service,
            amount=default_amount,
            is_session=(default_service == "Участие в судебном заседании"),
        )
        self._loading = False

        self._update_summary()
        self.data_changed.emit()

    def _on_add_all_sessions_clicked(self):
        existing = set()

        for row in range(self.table.rowCount()):
            row_date = self._get_row_date(row)
            service_name = self._get_row_service_name(row)
            if row_date and service_name:
                existing.add((row_date, service_name))

        added = False

        self._loading = True
        for event in self.state.events:
            if not event.event_date:
                continue

            key = (event.event_date, "Участие в судебном заседании")
            if key in existing:
                continue

            amount = self.payment_calculator.get_amount_for_date(
                self.state.payment_rule,
                event.event_date,
            )

            self._append_row(
                service_date=event.event_date,
                service_name="Участие в судебном заседании",
                amount=amount,
                is_session=True,
            )
            existing.add(key)
            added = True

        self._loading = False

        if added:
            self._update_summary()
            self.data_changed.emit()

    def _on_delete_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            return

        self.table.removeRow(row)
        self._update_summary()
        self.data_changed.emit()

    def _on_item_changed(self, item):
        if self._loading:
            return

        row = item.row()
        column = item.column()

        if column == 0:
            self._loading = True
            self._recalculate_row_amount(row)
            self._loading = False


        elif column == 2:
            text = item.text().strip()
            cleaned = self._clean_money_text(text)
            if text != cleaned:
                self._loading = True
                item.setText(cleaned)
                self._loading = False

        self._update_summary()
        self.data_changed.emit()

    def _append_row(self, service_date, service_name, amount, is_session=False):
        row = self.table.rowCount()
        self.table.insertRow(row)

        date_item = QTableWidgetItem(
            service_date.strftime("%d.%m.%Y") if service_date else ""
        )
        date_item.setTextAlignment(Qt.AlignCenter)

        amount_item = QTableWidgetItem(format_money_for_edit(amount))
        amount_item.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(row, 0, date_item)
        self.table.setCellWidget(row, 1, self._create_service_combo(service_name))
        self.table.setItem(row, 2, amount_item)

    def _create_service_combo(self, current_text):
        combo = NoWheelComboBox()
        combo.setEditable(True)

        for item in LAWYER_SERVICE_TYPES:
            combo.addItem(item)

        combo.setCurrentText(current_text or "")
        combo.currentTextChanged.connect(self._on_service_changed)
        return combo

    def _on_service_changed(self):
        if self._loading:
            return

        self._update_summary()
        self.data_changed.emit()

    def _recalculate_row_amount(self, row):
        service_date = self._get_row_date(row)
        amount_item = self.table.item(row, 2)

        if amount_item is None:
            amount_item = QTableWidgetItem("")
            amount_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, amount_item)

        if service_date is None:
            amount_item.setText("")
            return

        amount = self.payment_calculator.get_amount_for_date(
            self.state.payment_rule,
            service_date,
        )
        amount_item.setText(format_money_for_edit(amount))

    def _get_row_date(self, row):
        item = self.table.item(row, 0)
        if item is None:
            return None

        text = item.text().strip()
        if not text:
            return None

        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None

    def _get_row_service_name(self, row):
        widget = self.table.cellWidget(row, 1)
        if widget is None:
            return ""
        return widget.currentText().strip()

    def _get_row_amount(self, row):
        item = self.table.item(row, 2)
        if item is None:
            return to_decimal_money("0")

        return to_decimal_money(item.text())

    def _update_summary(self):
        rows_count = self.table.rowCount()
        total = 0

        for row in range(rows_count):
            total += self._get_row_amount(row)

        self.summary_label.setText(
            "Число дней {0}, Сумма: {1}".format(rows_count, format_money(total))
        )

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