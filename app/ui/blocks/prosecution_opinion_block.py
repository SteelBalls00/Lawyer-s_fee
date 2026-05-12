# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)


class ProsecutionOpinionBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Мнение сторон о взыскании", parent)

        self._loading = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        # ── Строка 1: государственный обвинитель ──────────────────────────
        self.radio_prosecutor_recover = QRadioButton("взыскать")
        self.radio_prosecutor_exempt = QRadioButton("освободить")
        self.radio_prosecutor_recover.setChecked(True)

        self._prosecutor_group = QButtonGroup(self)
        self._prosecutor_group.addButton(self.radio_prosecutor_recover)
        self._prosecutor_group.addButton(self.radio_prosecutor_exempt)

        prosecutor_row = QHBoxLayout()
        prosecutor_row.addWidget(QLabel("Государственный обвинитель предлагал"))
        prosecutor_row.addWidget(self.radio_prosecutor_recover)
        prosecutor_row.addWidget(self.radio_prosecutor_exempt)
        prosecutor_row.addStretch(1)

        # ── Строка 2: подсудимый ──────────────────────────────────────────
        self.radio_defendant_objected = QRadioButton("возражал")
        self.radio_defendant_not_objected = QRadioButton("не возражал")
        self.radio_defendant_objected.setChecked(True)

        self._defendant_group = QButtonGroup(self)
        self._defendant_group.addButton(self.radio_defendant_objected)
        self._defendant_group.addButton(self.radio_defendant_not_objected)

        defendant_row = QHBoxLayout()
        defendant_row.addWidget(QLabel("Подсудимый"))
        defendant_row.addWidget(self.radio_defendant_objected)
        defendant_row.addWidget(self.radio_defendant_not_objected)
        defendant_row.addStretch(1)

        root = QVBoxLayout()
        root.addLayout(prosecutor_row)
        root.addLayout(defendant_row)

        self.setLayout(root)

    def _connect_signals(self):
        self.radio_prosecutor_recover.toggled.connect(self._emit_changed)
        self.radio_prosecutor_exempt.toggled.connect(self._emit_changed)
        self.radio_defendant_objected.toggled.connect(self._emit_changed)
        self.radio_defendant_not_objected.toggled.connect(self._emit_changed)

    def _emit_changed(self):
        if not self._loading:
            self.data_changed.emit()

    def load_from_state(self, state):
        self._loading = True

        self.radio_prosecutor_recover.blockSignals(True)
        self.radio_prosecutor_exempt.blockSignals(True)
        self.radio_defendant_objected.blockSignals(True)
        self.radio_defendant_not_objected.blockSignals(True)

        self.radio_prosecutor_recover.setChecked(state.prosecutor_proposes_recovery)
        self.radio_prosecutor_exempt.setChecked(not state.prosecutor_proposes_recovery)

        self.radio_defendant_objected.setChecked(state.defendant_objected)
        self.radio_defendant_not_objected.setChecked(not state.defendant_objected)

        self.radio_prosecutor_recover.blockSignals(False)
        self.radio_prosecutor_exempt.blockSignals(False)
        self.radio_defendant_objected.blockSignals(False)
        self.radio_defendant_not_objected.blockSignals(False)

        self._loading = False

    def save_to_state(self, state):
        state.prosecutor_proposes_recovery = self.radio_prosecutor_recover.isChecked()
        state.defendant_objected = self.radio_defendant_objected.isChecked()
