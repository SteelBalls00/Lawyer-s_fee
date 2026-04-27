# -*- coding: utf-8 -*-

from datetime import date, datetime

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import EXTRA_DECREE_SOURCES
from app.state import ExtraDecreeRow


class ExtraDecreesBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Дополнительные постановления", parent)

        self._loading = False

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.label = QLabel("Есть дополнительные постановления?")
        self.radio_yes = QRadioButton("Да")
        self.radio_no = QRadioButton("Нет")
        self.radio_no.setChecked(True)

        top_row = QHBoxLayout()
        top_row.addWidget(self.label)
        top_row.addWidget(self.radio_yes)
        top_row.addWidget(self.radio_no)
        top_row.addStretch(1)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["От кого", "Дата постановления", "Сумма"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 320)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 100)

        self.add_button = QPushButton("Добавить")
        self.delete_button = QPushButton("Удалить")

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch(1)

        table_row = QHBoxLayout()
        table_row.addWidget(self.table, 1)
        table_row.addLayout(buttons_layout)

        self.container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addLayout(table_row)
        self.container.setLayout(container_layout)
        self.container.setVisible(False)

        root = QVBoxLayout()
        root.addLayout(top_row)
        root.addWidget(self.container)

        self.setLayout(root)

    def _connect_signals(self):
        self.radio_yes.toggled.connect(self._on_mode_changed)
        self.radio_yes.toggled.connect(self.data_changed.emit)
        self.radio_no.toggled.connect(self.data_changed.emit)

        self.add_button.clicked.connect(self._on_add_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.table.itemChanged.connect(self._on_item_changed)

    def load_from_state(self, state):
        self._loading = True

        self.radio_yes.blockSignals(True)
        self.radio_no.blockSignals(True)

        self.radio_yes.setChecked(state.use_extra_decrees)
        self.radio_no.setChecked(not state.use_extra_decrees)
        self.container.setVisible(state.use_extra_decrees)

        self.table.setRowCount(0)
        for item in state.extra_decrees:
            self._append_row(
                source=item.source,
                decree_date=item.decree_date,
                amount=item.amount,
            )

        self.radio_yes.blockSignals(False)
        self.radio_no.blockSignals(False)

        self._loading = False

    def save_to_state(self, state):
        state.use_extra_decrees = self.radio_yes.isChecked()

        rows = []
        for row in range(self.table.rowCount()):
            rows.append(
                ExtraDecreeRow(
                    source=self._get_row_source(row),
                    decree_date=self._get_row_date(row),
                    amount=self._get_row_amount(row),
                )
            )

        state.extra_decrees = rows

    def _on_mode_changed(self):
        self.container.setVisible(self.radio_yes.isChecked())

    def _on_add_clicked(self):
        self._loading = True
        self._append_row(
            source=EXTRA_DECREE_SOURCES[0],
            decree_date=date.today(),
            amount=0,
        )
        self._loading = False
        self.data_changed.emit()

    def _on_delete_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            return

        self.table.removeRow(row)
        self.data_changed.emit()

    def _on_item_changed(self, item):
        if self._loading:
            return

        if item.column() == 2:
            text = item.text().strip()
            digits = "".join(ch for ch in text if ch.isdigit())
            if text != digits:
                self._loading = True
                item.setText(digits)
                self._loading = False

        self.data_changed.emit()

    def _append_row(self, source, decree_date, amount):
        row = self.table.rowCount()
        self.table.insertRow(row)

        source_combo = self._create_source_combo(source)

        date_item = QTableWidgetItem(
            decree_date.strftime("%d.%m.%Y") if decree_date else ""
        )
        date_item.setTextAlignment(Qt.AlignCenter)

        amount_item = QTableWidgetItem(str(int(amount or 0)))
        amount_item.setTextAlignment(Qt.AlignCenter)

        self.table.setCellWidget(row, 0, source_combo)
        self.table.setItem(row, 1, date_item)
        self.table.setItem(row, 2, amount_item)

    def _create_source_combo(self, current_text):
        combo = QComboBox()
        combo.setEditable(True)

        for item in EXTRA_DECREE_SOURCES:
            combo.addItem(item)

        combo.setCurrentText(current_text or "")
        combo.currentTextChanged.connect(self._on_source_changed)
        return combo

    def _on_source_changed(self):
        if self._loading:
            return
        self.data_changed.emit()

    def _get_row_source(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is None:
            return ""
        return widget.currentText().strip()

    def _get_row_date(self, row):
        item = self.table.item(row, 1)
        if item is None:
            return None

        text = item.text().strip()
        if not text:
            return None

        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None

    def _get_row_amount(self, row):
        item = self.table.item(row, 2)
        if item is None:
            return 0

        text = item.text().strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        return int(digits) if digits else 0