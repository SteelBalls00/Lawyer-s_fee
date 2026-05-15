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
import threading

CASES = ("рп", "дп", "вп", "тп", "пп")
SECTION = "words"

# Сериализуем сетевые записи, чтобы не было гонок
_network_lock = threading.Lock()


class DeclensionWordCache:
    def __init__(self, cache_path, network_path=None):
        self.cache_path = cache_path
        self.network_path = (network_path or "").strip() or None
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str   # сохраняем регистр
        self._load()

    # ─── Стартовая синхронизация ────────────────────────────────────────

    def sync_from_network(self):
        """При старте программы: подтягивает изменения из сетевого файла в локальный.

        Сетевые записи мерджатся в локальный кеш (сетевые приоритетнее
        локальных при конфликте — это «общая правда»).
        Если сеть недоступна, просто игнорируем.
        """
        if not self.network_path or not os.path.exists(self.network_path):
            return

        try:
            net_config = configparser.RawConfigParser()
            net_config.optionxform = str
            net_config.read(self.network_path, encoding="utf-8")
        except Exception:
            return

        if not net_config.has_section(SECTION):
            return

        if not self._config.has_section(SECTION):
            self._config.add_section(SECTION)

        changed = False
        for word, value in net_config.items(SECTION):
            if not self._config.has_option(SECTION, word) or self._config.get(SECTION, word) != value:
                self._config.set(SECTION, word, value)
                changed = True

        if changed:
            self._write_local()

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

        self._write_local()
        self._schedule_network_word_update(word)

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

    def _write_local(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                self._config.write(f)
        except Exception:
            pass

    def _schedule_network_word_update(self, word):
        """Асинхронно добавляет одно слово в сетевой файл, мерджа с тем что там есть.

        Сеть может быть недоступна — это нормально, ошибка игнорируется.
        """
        if not self.network_path:
            return

        # Снимок локальных форм этого слова (вызов из основного потока — безопасно)
        local_forms = self.get_forms(word)
        network_path = self.network_path

        def task():
            with _network_lock:
                try:
                    net_config = configparser.RawConfigParser()
                    net_config.optionxform = str
                    if os.path.exists(network_path):
                        net_config.read(network_path, encoding="utf-8")

                    if not net_config.has_section(SECTION):
                        net_config.add_section(SECTION)

                    # Существующие формы этого слова в сети
                    existing = {}
                    if net_config.has_option(SECTION, word):
                        raw = net_config.get(SECTION, word)
                        parts = [p.strip() for p in raw.split(",")]
                        for i, case in enumerate(CASES):
                            if i < len(parts) and parts[i]:
                                existing[case] = parts[i]

                    # Локальные правки приоритетнее — они только что введены пользователем
                    for case, form in local_forms.items():
                        if form:
                            existing[case] = form

                    if existing:
                        csv = ", ".join(existing.get(c, "") for c in CASES)
                        net_config.set(SECTION, word, csv)
                    elif net_config.has_option(SECTION, word):
                        net_config.remove_option(SECTION, word)

                    with open(network_path, "w", encoding="utf-8") as f:
                        net_config.write(f)
                except Exception:
                    pass   # сеть недоступна — игнорируем

        threading.Thread(target=task, daemon=True).start()
