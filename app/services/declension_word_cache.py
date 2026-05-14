# -*- coding: utf-8 -*-
"""Кеш склонений отдельных слов ФИО.

Хранится в declensions.ini. Одна секция [words].
Ключ — слово в именительном падеже (фамилия, имя или отчество).
Значение — CSV через запятую в порядке: рп, дп, вп, тп, пп.

Пример:
    [words]
    Печников = Печникова, Печникову, Печникова, Печниковым, Печникове
    Алексей  = Алексея, Алексею, Алексея, Алексеем, Алексее
    Козлова  = Козловой, Козловой, Козлову, Козловой, Козловой

Преимущество перед кешем по ФИО: одна запись для слова работает
для любого человека с этой фамилией/именем/отчеством.
"""

import configparser
import os

CASES = ("рп", "дп", "вп", "тп", "пп")
SECTION = "words"


class DeclensionWordCache:
    def __init__(self, cache_path):
        self.cache_path = cache_path
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str   # сохраняем регистр
        self._load()

    # ─── Чтение ─────────────────────────────────────────────────────────

    def get_forms(self, word):
        """Возвращает {case_short: declined_form} для данного слова.

        Если слово не найдено — пустой словарь.
        """
        word = (word or "").strip()
        if not word:
            return {}
        if not self._config.has_section(SECTION):
            return {}
        if not self._config.has_option(SECTION, word):
            return {}

        raw = self._config.get(SECTION, word)
        parts = [p.strip() for p in raw.split(",")]
        return {
            case: parts[i]
            for i, case in enumerate(CASES)
            if i < len(parts) and parts[i]
        }

    def has_word(self, word):
        word = (word or "").strip()
        if not word or not self._config.has_section(SECTION):
            return False
        return self._config.has_option(SECTION, word)

    def all_words(self):
        if not self._config.has_section(SECTION):
            return []
        return [k for k, _ in self._config.items(SECTION)]

    # ─── Запись ─────────────────────────────────────────────────────────

    def save_forms(self, word, case_forms):
        """Сохраняет {case_short: declined_form} для данного слова.

        Merge с существующими данными: сохраняются только переданные падежи,
        остальные не затрагиваются.
        Пустая строка в value удаляет этот падеж (вернуть в авто).
        """
        word = (word or "").strip()
        if not word:
            return

        existing = self.get_forms(word)
        changed = False

        for case_short, form in case_forms.items():
            form = (form or "").strip()
            if form:
                if existing.get(case_short) != form:
                    existing[case_short] = form
                    changed = True
            elif case_short in existing:
                del existing[case_short]
                changed = True

        if not changed:
            return

        if not self._config.has_section(SECTION):
            self._config.add_section(SECTION)

        if existing:
            csv = ", ".join(existing.get(c, "") for c in CASES)
            self._config.set(SECTION, word, csv)
        else:
            # Все формы удалены — убираем слово из кеша
            self._config.remove_option(SECTION, word)

        self._write()

    def save_fio_case(self, source_fio, corrected_form, case_short):
        """Разбирает два ФИО по словам и сохраняет каждое в кеш.

        source_fio    — ФИО в именительном падеже (из БД)
        corrected_form — ФИО в нужном падеже (введённое пользователем)
        case_short    — 'рп' / 'дп' / 'вп' / 'тп' / 'пп'

        Слова выравниваются по позиции. Если количество слов не совпадает,
        ничего не сохраняется.
        """
        src_words = (source_fio or "").strip().split()
        cor_words = (corrected_form or "").strip().split()

        if not src_words or not cor_words:
            return
        if len(src_words) != len(cor_words):
            return

        for src, cor in zip(src_words, cor_words):
            if "." in src or "." in cor:
                continue   # инициалы не кешируем
            self.save_forms(src, {case_short: cor})

    # ─── Приватное ──────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.cache_path):
            try:
                self._config.read(self.cache_path, encoding="utf-8")
            except Exception:
                pass

    def _write(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                self._config.write(f)
        except Exception:
            pass
