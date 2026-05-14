# -*- coding: utf-8 -*-
"""Персистентный кеш ручных правок склонений ФИО.

Хранится в файле declensions.ini рядом с config.ini.
Каждая секция — полное ФИО (как в БД).
Ключи — короткие обозначения падежей: рп, дп, вп, тп, пп.
Значения — полная склонённая форма (без инициалов).

Пример:
    [Печников Алексей Евгеньевич]
    рп = Печникова Алексея Евгеньевича
    дп = Печникову Алексею Евгеньевичу
    вп = Печникова Алексея Евгеньевича
    тп = Печниковым Алексеем Евгеньевичем
"""

import configparser
import os


CASE_SHORTS = ("рп", "дп", "вп", "тп", "пп", "ип")


class DeclensionCache:
    def __init__(self, cache_path):
        self.cache_path = cache_path
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str   # сохраняем регистр ключей
        self._load()

    # ─── Чтение ─────────────────────────────────────────────────────────

    def get_by_fio(self, fio):
        """Возвращает {case_short: full_form} для данного ФИО.

        Если ФИО не найдено — пустой словарь.
        """
        fio = (fio or "").strip()
        if not fio or not self._config.has_section(fio):
            return {}

        result = {}
        for key, value in self._config.items(fio):
            if key in CASE_SHORTS and value.strip():
                result[key] = value.strip()
        return result

    def all_fio_names(self):
        """Список всех ФИО, для которых есть сохранённые правки."""
        return list(self._config.sections())

    # ─── Запись ─────────────────────────────────────────────────────────

    def save_for_fio(self, fio, case_forms):
        """Сохраняет {case_short: full_form} для данного ФИО.

        Пустое значение удаляет соответствующий ключ из кеша
        (будет применяться автосклонение).
        """
        fio = (fio or "").strip()
        if not fio:
            return

        if not self._config.has_section(fio):
            self._config.add_section(fio)

        changed = False
        for case_short, form in case_forms.items():
            form = (form or "").strip()
            if form:
                self._config.set(fio, case_short, form)
                changed = True
            elif self._config.has_option(fio, case_short):
                self._config.remove_option(fio, case_short)
                changed = True

        # Если после удалений секция опустела — убираем её совсем
        if not dict(self._config.items(fio)):
            self._config.remove_section(fio)

        if changed:
            self._write()

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
