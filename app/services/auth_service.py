# -*- coding: utf-8 -*-
"""Авторизация по паролю через таблицу GROUPCONTENT основной БД (ГАС СДП).

Логика идентична C#-программе: пользователь вводит только пароль,
по нему ищется username в groupcontent.userpsw.
"""


class AuthService:
    QUERY = "select username from groupcontent where userpsw = ?"

    def __init__(self, db_client):
        self.db = db_client

    def authenticate(self, password):
        """Возвращает username при успехе или None."""
        password = (password or "").strip()
        if not password:
            return None

        row = self.db.fetch_one(self.QUERY, (password,))
        if row and row[0]:
            return str(row[0]).strip()
        return None
