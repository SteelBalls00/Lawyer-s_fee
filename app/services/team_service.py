# -*- coding: utf-8 -*-
"""Администраторы и составы (связки судья↔помощник) в архивной БД.

Таблицы ADMINS и TEAM_MEMBERS — см. archive_db_teams.sql.
Все участники одного состава видят в архиве постановления друг друга.
"""


class TeamService:
    def __init__(self, db_client):
        self.db = db_client

    # ─── Администраторы ─────────────────────────────────────────────────

    def is_admin(self, username):
        username = (username or "").strip()
        if not username:
            return False
        row = self.db.fetch_one(
            "SELECT FIRST 1 1 FROM ADMINS WHERE UPPER(USERNAME) = UPPER(?)",
            (username,),
        )
        return row is not None

    # ─── Чтение составов ────────────────────────────────────────────────

    def get_group_usernames(self, username):
        """Все пользователи, состоящие хотя бы в одном составе вместе
        с указанным (включая его самого)."""
        username = (username or "").strip()
        if not username:
            return []

        rows = self.db.fetch_all(
            "SELECT DISTINCT TM2.USERNAME "
            "FROM TEAM_MEMBERS TM1 "
            "JOIN TEAM_MEMBERS TM2 ON TM2.TEAM_NAME = TM1.TEAM_NAME "
            "WHERE UPPER(TM1.USERNAME) = UPPER(?)",
            (username,),
        )

        names = {username}
        for row in rows:
            name = (row[0] or "").strip()
            if name:
                names.add(name)
        return sorted(names)

    def list_teams(self):
        """{team_name: [username, ...]} — все составы."""
        rows = self.db.fetch_all(
            "SELECT TEAM_NAME, USERNAME FROM TEAM_MEMBERS "
            "ORDER BY TEAM_NAME, USERNAME"
        )
        teams = {}
        for row in rows:
            team = (row[0] or "").strip()
            user = (row[1] or "").strip()
            if team and user:
                teams.setdefault(team, []).append(user)
        return teams

    # ─── Изменение составов ─────────────────────────────────────────────

    def add_member(self, team_name, username):
        team_name = (team_name or "").strip()
        username = (username or "").strip()
        if not team_name or not username:
            return

        exists = self.db.fetch_one(
            "SELECT FIRST 1 1 FROM TEAM_MEMBERS "
            "WHERE UPPER(TEAM_NAME) = UPPER(?) AND UPPER(USERNAME) = UPPER(?)",
            (team_name, username),
        )
        if exists:
            return

        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO TEAM_MEMBERS (TEAM_NAME, USERNAME) VALUES (?, ?)",
                (team_name, username),
            )
            conn.commit()

    def remove_member(self, team_name, username):
        team_name = (team_name or "").strip()
        username = (username or "").strip()
        if not team_name or not username:
            return

        with self.db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM TEAM_MEMBERS "
                "WHERE UPPER(TEAM_NAME) = UPPER(?) AND UPPER(USERNAME) = UPPER(?)",
                (team_name, username),
            )
            conn.commit()
