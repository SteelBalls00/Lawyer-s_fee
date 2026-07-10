# -*- coding: utf-8 -*-

import configparser
from contextlib import contextmanager

import fdb


class FirebirdClient(object):
    def __init__(self, config_path: str, section: str = "database"):
        self.config_path = config_path
        self.section = section
        self._config = self._load_config()

    def _load_config(self) -> configparser.SectionProxy:
        parser = configparser.ConfigParser()
        read_files = parser.read(self.config_path, encoding="utf-8")
        if not read_files:
            raise FileNotFoundError("Не найден config.ini: {0}".format(self.config_path))

        if self.section not in parser:
            raise KeyError(
                "В config.ini отсутствует секция [{0}]".format(self.section)
            )

        return parser[self.section]

    @contextmanager
    def connection(self):
        conn = None
        try:
            conn = fdb.connect(
                host=self._config.get("host"),
                port=self._config.getint("port"),
                database=self._config.get("database"),
                user=self._config.get("user"),
                password=self._config.get("password"),
                charset=self._config.get("charset", fallback="WIN1251"),
            )
            yield conn
        finally:
            if conn is not None:
                conn.close()

    def fetch_all(self, query: str, params=None):
        if params is None:
            params = ()

        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            return rows

    def fetch_one(self, query: str, params=None):
        if params is None:
            params = ()

        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            cur.close()
            return row