# -*- coding: utf-8 -*-
"""Пользовательские настройки программы, хранятся в settings.ini.

Сейчас содержит:
- последний путь сохранения постановления
- путь к сетевому файлу declensions.ini для общего кеша склонений
"""

import configparser
import os


DEFAULT_NETWORK_DECLENSIONS = r"\\192.168.0.200\Minato\Lawyer_s_fee\declensions.ini"


class UserSettings:
    def __init__(self, settings_path):
        self.settings_path = settings_path
        self._config = configparser.RawConfigParser()
        self._load()
        self._ensure_defaults()

    # ─── Геттеры ────────────────────────────────────────────────────────

    def get_last_save_dir(self):
        return self._get("paths", "last_save_dir", "")

    def get_network_declensions_path(self):
        return self._get("paths", "network_declensions", DEFAULT_NETWORK_DECLENSIONS)

    # ─── Сеттеры (с автосохранением) ────────────────────────────────────

    def set_last_save_dir(self, path):
        self._set("paths", "last_save_dir", path or "")
        self._write()

    def set_network_declensions_path(self, path):
        self._set("paths", "network_declensions", path or "")
        self._write()

    # ─── Приватное ──────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.settings_path):
            try:
                self._config.read(self.settings_path, encoding="utf-8")
            except Exception:
                pass

    def _ensure_defaults(self):
        """Создаёт settings.ini с дефолтным сетевым путём, если его ещё нет."""
        changed = False
        if not self._config.has_section("paths"):
            self._config.add_section("paths")
            changed = True
        if not self._config.has_option("paths", "network_declensions"):
            self._config.set("paths", "network_declensions", DEFAULT_NETWORK_DECLENSIONS)
            changed = True
        if changed:
            self._write()

    def _get(self, section, key, default=""):
        if self._config.has_option(section, key):
            return self._config.get(section, key)
        return default

    def _set(self, section, key, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, value)

    def _write(self):
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                self._config.write(f)
        except Exception:
            pass
