# -*- coding: utf-8 -*-

from datetime import datetime

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from app.ui.widgets.no_wheel_combo_box import NoWheelComboBox
from app.ui.widgets.ghost_widgets import GhostLineEdit, GhostComboBox


SEX_OPTIONS = ["мужской", "женский"]

_CAPTION_STYLE = (
    "color: #7a96ae; font-size: 10px; font-weight: 600; "
    "letter-spacing: 0.4px; padding: 0; margin: 0;"
)


def _caption(text):
    """Создаёт маленький серый заголовок над полем ввода."""
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(_CAPTION_STYLE)
    return lbl


def _field_block(caption_text, widget):
    """Возвращает вертикальный блок: подпись + виджет."""
    box = QVBoxLayout()
    box.setSpacing(1)
    box.setContentsMargins(0, 4, 0, 0)
    box.addWidget(_caption(caption_text))
    box.addWidget(widget)
    return box


class DefendantBlock(QGroupBox):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Информация о подсудимом", parent)
        self._defendants = []
        self._current_index = -1
        self._updating_date = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        # ── Выбор подсудимого ─────────────────────────────────────────
        self.defendant_combo = NoWheelComboBox()

        top_form = QFormLayout()
        top_form.setSpacing(4)
        top_form.addRow("Подсудимый", self.defendant_combo)

        # ── Чекбокс ───────────────────────────────────────────────────
        self.custody_checkbox = QCheckBox("Находился под стражей")

        # ── Поля в стиле «ghost» ──────────────────────────────────────
        self.sex_combo = GhostComboBox()
        for option in SEX_OPTIONS:
            self.sex_combo.addItem(option)

        self.birth_date_edit = GhostLineEdit()
        self.birth_date_edit.setPlaceholderText("дд.мм.гггг")
        self.birth_date_edit.setMaxLength(10)

        self.native_edit = GhostLineEdit()
        self.native_edit.setPlaceholderText("место рождения")

        self.article_edit = GhostLineEdit()
        self.article_edit.setPlaceholderText("статья УК РФ")

        # ── Компоновка: пол + дата рождения в одной строке ────────────
        row1 = QHBoxLayout()
        row1.setSpacing(24)
        sex_block = _field_block("Пол", self.sex_combo)
        self.sex_combo.setMinimumWidth(110)
        row1.addLayout(sex_block, 1)

        birth_block = _field_block("Дата рождения", self.birth_date_edit)
        self.birth_date_edit.setMinimumWidth(100)
        row1.addLayout(birth_block, 1)

        # ── Уроженец и статья на всю ширину ───────────────────────────
        root = QVBoxLayout()
        root.setSpacing(0)
        root.addLayout(top_form)
        root.addWidget(self.custody_checkbox)
        root.addLayout(row1)
        root.addLayout(_field_block("Уроженец", self.native_edit))
        root.addLayout(_field_block("Основная статья", self.article_edit))

        self.setLayout(root)

    def _connect_signals(self):
        self.defendant_combo.currentIndexChanged.connect(self._on_defendant_changed)
        self.custody_checkbox.toggled.connect(self._on_field_changed)
        self.sex_combo.currentIndexChanged.connect(self._on_field_changed)
        self.native_edit.textChanged.connect(self._on_field_changed)
        self.birth_date_edit.textChanged.connect(self._on_birth_date_changed)
        self.article_edit.textChanged.connect(self._on_field_changed)

    # ─── Загрузка / сохранение ──────────────────────────────────────────

    def load_from_state(self, state):
        self._defendants = list(state.defendants)
        self.defendant_combo.blockSignals(True)
        self.defendant_combo.clear()
        for item in self._defendants:
            self.defendant_combo.addItem("{0} — {1}".format(item.fio, item.article))
        if self._defendants:
            index = min(state.selected_defendant_index, len(self._defendants) - 1)
            self.defendant_combo.setCurrentIndex(index)
            self._current_index = index
            self._fill_fields(index)
        else:
            self._current_index = -1
            self._clear_fields()
        self.defendant_combo.blockSignals(False)

    def save_to_state(self, state):
        index = self.defendant_combo.currentIndex()
        if index < 0:
            state.selected_defendant_index = 0
            return
        state.selected_defendant_index = index
        self._write_fields_to_defendant(index)

    # ─── Обработчики ───────────────────────────────────────────────────

    def _on_defendant_changed(self, new_index):
        if 0 <= self._current_index < len(self._defendants):
            self._write_fields_to_defendant(self._current_index)
        self._current_index = new_index
        self._fill_fields(new_index)
        self.data_changed.emit()

    def _on_field_changed(self, *_):
        self.data_changed.emit()

    def _on_birth_date_changed(self, text):
        if self._updating_date:
            return
        self._updating_date = True
        formatted = self._format_date(text)
        if formatted != text:
            self.birth_date_edit.setText(formatted)
            self.birth_date_edit.setCursorPosition(len(formatted))
        self._updating_date = False
        self.data_changed.emit()

    @staticmethod
    def _format_date(text):
        digits = "".join(c for c in text if c.isdigit())[:8]
        if len(digits) <= 2:
            return digits
        if len(digits) <= 4:
            return digits[:2] + "." + digits[2:]
        return digits[:2] + "." + digits[2:4] + "." + digits[4:]

    # ─── Внутренние ────────────────────────────────────────────────────

    def _fill_fields(self, index):
        if not (0 <= index < len(self._defendants)):
            self._clear_fields()
            return
        d = self._defendants[index]

        sex = (d.sex or "").lower()
        sex_index = 0
        for i, opt in enumerate(SEX_OPTIONS):
            if opt in sex or sex in opt:
                sex_index = i
                break
        self.sex_combo.blockSignals(True)
        self.sex_combo.setCurrentIndex(sex_index)
        self.sex_combo.blockSignals(False)

        self.birth_date_edit.blockSignals(True)
        self.birth_date_edit.setText(
            d.birth_date.strftime("%d.%m.%Y") if d.birth_date else ""
        )
        self.birth_date_edit.blockSignals(False)

        self.native_edit.blockSignals(True)
        self.native_edit.setText(d.native or "")
        self.native_edit.blockSignals(False)

        self.article_edit.blockSignals(True)
        self.article_edit.setText(d.article or "")
        self.article_edit.blockSignals(False)

        self.custody_checkbox.blockSignals(True)
        self.custody_checkbox.setChecked(d.in_custody)
        self.custody_checkbox.blockSignals(False)

    def _clear_fields(self):
        self.sex_combo.blockSignals(True)
        self.sex_combo.setCurrentIndex(0)
        self.sex_combo.blockSignals(False)
        for w in (self.birth_date_edit, self.native_edit, self.article_edit):
            w.blockSignals(True)
            w.setText("")
            w.blockSignals(False)
        self.custody_checkbox.blockSignals(True)
        self.custody_checkbox.setChecked(False)
        self.custody_checkbox.blockSignals(False)

    def _write_fields_to_defendant(self, index):
        if not (0 <= index < len(self._defendants)):
            return
        d = self._defendants[index]
        d.sex = self.sex_combo.currentText()
        d.native = self.native_edit.text().strip()
        d.article = self.article_edit.text().strip()
        d.in_custody = self.custody_checkbox.isChecked()
        date_text = self.birth_date_edit.text().strip()
        if date_text:
            try:
                d.birth_date = datetime.strptime(date_text, "%d.%m.%Y").date()
            except ValueError:
                pass
        else:
            d.birth_date = None
