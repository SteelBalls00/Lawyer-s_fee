# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

CASE_LABELS = {
    "ип": "Именительный",
    "рп": "Родительный",
    "дп": "Дательный",
    "вп": "Винительный",
    "тп": "Творительный",
    "пп": "Предложный",
}

CASE_ORDER = ["ип", "рп", "дп", "вп", "тп", "пп"]

FIO_BASE_KEYS = ("подсудимый", "адвокат", "фио адвоката")

def _normalize_base(base_key):
    return "адвокат" if base_key == "фио адвоката" else base_key

GROUP_TITLES = {
    "подсудимый": "Подсудимый",
    "адвокат": "Адвокат",
}

ALWAYS_SHOW_CASES = {
    "подсудимый": {"рп", "дп"},
    "адвокат": {"рп", "дп"},
}


def _make_initials_form(full_form):
    words = (full_form or "").strip().split()
    if len(words) <= 1:
        return full_form or ""
    surname = words[0]
    initials = "".join(w[0].upper() + "." for w in words[1:] if w)
    return "{0} {1}".format(surname, initials)


class DeclensionDialog(QDialog):

    def __init__(self, state, tag_resolver, morphology_service,
                 template_tags, declension_cache=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.tag_resolver = tag_resolver
        self.morphology = morphology_service
        self.template_tags = template_tags or []
        self.declension_cache = declension_cache
        self._editors = {}
        self.setWindowTitle("Склонения ФИО")
        self.setMinimumSize(700, 460)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        root = QVBoxLayout(self)
        info = QLabel(
            "Введите нужную форму — она применится везде в тексте, включая "
            "дополнительные постановления. Форма с инициалами выводится "
            "автоматически. Кнопка \u21ba возвращает автосклонение."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(2, 4, 2, 4)
        self._content_layout.setSpacing(10)
        scroll.setWidget(self._content_widget)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Применить")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _populate(self):
        groups = self._discover_used_cases()
        if not groups:
            lbl = QLabel("В шаблоне не найдено маркеров ФИО, требующих склонения.")
            lbl.setAlignment(Qt.AlignCenter)
            self._content_layout.addWidget(lbl)
            self._content_layout.addStretch(1)
            return
        for base_key in ("подсудимый", "адвокат"):
            if base_key not in groups:
                continue
            self._add_group(base_key, groups[base_key])
        self._content_layout.addStretch(1)

    def _add_group(self, base_key, cases):
        fio = self._get_source_fio(base_key)
        title = GROUP_TITLES.get(base_key, base_key)
        if fio:
            title = "{0}: {1}".format(title, fio)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #1e3a5f; padding: 2px 0 4px 0;")
        self._content_layout.addWidget(lbl)
        for case_short in sorted(cases, key=lambda c: CASE_ORDER.index(c) if c in CASE_ORDER else 99):
            self._add_row(base_key, case_short)

    def _add_row(self, base_key, case_short):
        row = QHBoxLayout()
        lbl = QLabel(CASE_LABELS.get(case_short, case_short) + ":")
        lbl.setMinimumWidth(140)
        row.addWidget(lbl)

        edit = QLineEdit()
        full_key = self.tag_resolver._make_override_key(base_key, case_short, False)
        existing = self.state.declension_overrides.get(full_key, "")
        auto_full = self._auto_value(base_key, case_short, False)
        edit.setText(existing if existing else auto_full)
        edit.setPlaceholderText(auto_full)
        edit.setProperty("__base_key", base_key)
        edit.setProperty("__case_short", case_short)
        row.addWidget(edit, 1)

        initials_preview = QLabel()
        initials_preview.setMinimumWidth(110)
        initials_preview.setMaximumWidth(150)
        initials_preview.setStyleSheet("color: #6a8aaa; font-size: 10px;")
        initials_preview.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        row.addWidget(initials_preview)

        def _upd(text, lbl=initials_preview):
            lbl.setText("\u2192 " + _make_initials_form(text) if text.strip() else "")
        _upd(edit.text())
        edit.textChanged.connect(_upd)

        reset_btn = QPushButton("↶ Сброс")
        reset_btn.setFixedWidth(80)
        reset_btn.setToolTip("Вернуть автосклонение")
        reset_btn.clicked.connect(
            lambda _=False, e=edit, bk=base_key, cs=case_short:
                e.setText(self._auto_value(bk, cs, False))
        )
        row.addWidget(reset_btn)

        self._content_layout.addLayout(row)
        self._editors[(base_key, case_short)] = edit

    def _discover_used_cases(self):
        groups = {}

        def add(base_key, case_short):
            norm = _normalize_base(base_key)
            if norm not in GROUP_TITLES or not case_short:
                return
            groups.setdefault(norm, set()).add(case_short)

        for raw in self.template_tags:
            raw = (raw or "").strip().strip("{}").strip()
            if not raw:
                continue
            parsed = self.tag_resolver._parse_tag(raw)
            if parsed["base_key"] in FIO_BASE_KEYS and parsed["case_short"]:
                add(parsed["base_key"], parsed["case_short"])

        for norm, cases in ALWAYS_SHOW_CASES.items():
            for cs in cases:
                add(norm, cs)

        return groups

    def _get_source_fio(self, base_key):
        if base_key == "подсудимый":
            d = self.state.selected_defendant
            return d.fio if d else ""
        lw = self.state.selected_lawyer
        return lw.fio if lw else ""

    def _auto_value(self, base_key, case_short, initials):
        fio = self._get_source_fio(base_key)
        if not fio:
            return ""
        if case_short and case_short != "ип":
            return self.morphology.decline_fio(fio, case_short, initials=initials)
        if initials:
            return self.morphology.to_initials(fio)
        return fio

    def accept(self):
        # Сохраняем правки слов в персистентный кеш (по слову, не по ФИО)
        for (base_key, case_short), edit in self._editors.items():
            text = edit.text().strip()
            auto = (self._auto_value(base_key, case_short, False) or "").strip()
            if not text or text == auto:
                continue
            source_fio = self._get_source_fio(base_key)
            if source_fio and self.declension_cache:
                self.declension_cache.save_fio_case(source_fio, text, case_short)

        # Очищаем state-level overrides — теперь всё через word_cache в morphology
        self.state.declension_overrides = {}
        super().accept()
