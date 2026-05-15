# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
)


class RecoveryModeBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Освобождение/взыскание", parent)

        self._loading = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.radio_recovery = QRadioButton("Взыскание")
        self.radio_exempt_insolvency = QRadioButton(
            "Освобождение — имущественная несостоятельность"
        )
        self.radio_exempt_special = QRadioButton(
            "Освобождение — особый порядок (гл. 40 УПК РФ)"
        )
        self.radio_not_considered = QRadioButton("Дело не рассмотрено")
        self.radio_not_participate = QRadioButton("Не участвовал")

        self.radio_recovery.setChecked(True)

        self._group = QButtonGroup(self)
        self._group.addButton(self.radio_recovery)
        self._group.addButton(self.radio_exempt_insolvency)
        self._group.addButton(self.radio_exempt_special)
        self._group.addButton(self.radio_not_considered)
        self._group.addButton(self.radio_not_participate)

        root = QVBoxLayout()
        root.addWidget(self.radio_recovery)
        root.addWidget(self.radio_exempt_insolvency)
        root.addWidget(self.radio_exempt_special)
        root.addWidget(self.radio_not_considered)
        root.addWidget(self.radio_not_participate)

        self.setLayout(root)

    def _connect_signals(self):
        self.radio_recovery.toggled.connect(self._emit_changed)
        self.radio_exempt_insolvency.toggled.connect(self._emit_changed)
        self.radio_exempt_special.toggled.connect(self._emit_changed)
        self.radio_not_considered.toggled.connect(self._emit_changed)
        self.radio_not_participate.toggled.connect(self._emit_changed)

    def _emit_changed(self):
        if not self._loading:
            self.data_changed.emit()

    def load_from_state(self, state):
        self._loading = True

        self.radio_recovery.blockSignals(True)
        self.radio_exempt_insolvency.blockSignals(True)
        self.radio_exempt_special.blockSignals(True)
        self.radio_not_considered.blockSignals(True)
        self.radio_not_participate.blockSignals(True)

        mode = getattr(state, "recovery_mode", "recovery")
        self.radio_recovery.setChecked(mode == "recovery")
        self.radio_exempt_insolvency.setChecked(mode == "exempt_insolvency")
        self.radio_exempt_special.setChecked(mode == "exempt_special")
        self.radio_not_considered.setChecked(mode == "not_considered")
        self.radio_not_participate.setChecked(mode == "not_participate")

        self.radio_recovery.blockSignals(False)
        self.radio_exempt_insolvency.blockSignals(False)
        self.radio_exempt_special.blockSignals(False)
        self.radio_not_considered.blockSignals(False)
        self.radio_not_participate.blockSignals(False)

        self._loading = False

    def save_to_state(self, state):
        if self.radio_recovery.isChecked():
            state.recovery_mode = "recovery"
        elif self.radio_exempt_insolvency.isChecked():
            state.recovery_mode = "exempt_insolvency"
        elif self.radio_exempt_special.isChecked():
            state.recovery_mode = "exempt_special"
        elif self.radio_not_considered.isChecked():
            state.recovery_mode = "not_considered"
        else:
            state.recovery_mode = "not_participate"
