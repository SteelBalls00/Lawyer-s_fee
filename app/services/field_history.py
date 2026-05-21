# -*- coding: utf-8 -*-
"""История введённых значений для полей (секретарь, гос. обвинитель и т.п.).

Хранится в field_history.ini рядом с config.ini.
Каждая секция — ключ поля, значения нумерованные (порядок = свежесть, 0 — самое новое).

Пример:
    [secretary]
    0 = Иванова И.И.
    1 = Петрова П.П.

    [prosecutor]
    0 = Сидоров С.С.
"""

import configparser
import os


class FieldHistory:
    def __init__(self, path, max_per_field=25):
        self.path = path
        self.max_per_field = max_per_field
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str
        self._load()

    # ─── Чтение ─────────────────────────────────────────────────────────

    def get_values(self, key):
        """Возвращает список значений (свежие сверху) для данного поля."""
        if not self._config.has_section(key):
            return []
        items = []
        for idx_str, value in self._config.items(key):
            try:
                idx = int(idx_str)
            except ValueError:
                continue
            if value.strip():
                items.append((idx, value.strip()))
        items.sort(key=lambda t: t[0])
        return [v for _, v in items]

    # ─── Запись ─────────────────────────────────────────────────────────

    def add_value(self, key, value):
        """Добавляет значение в начало истории (свежее сверху), убирает дубликаты."""
        value = (value or "").strip()
        if not value:
            return

        current = self.get_values(key)
        # Убираем существующий такой же (без учёта регистра), чтобы поднять наверх
        current = [v for v in current if v.lower() != value.lower()]
        current.insert(0, value)
        current = current[: self.max_per_field]

        # Пересобираем секцию
        if self._config.has_section(key):
            self._config.remove_section(key)
        self._config.add_section(key)
        for i, v in enumerate(current):
            self._config.set(key, str(i), v)

        self._write()

    # ─── Приватное ──────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.path):
            try:
                self._config.read(self.path, encoding="utf-8")
            except Exception:
                pass

    def _write(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                self._config.write(f)
        except Exception:
            pass
