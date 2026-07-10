# -*- coding: utf-8 -*-
"""Архив постановлений: запись и чтение из отдельной Firebird-базы.

Подключение настраивается в config.ini, секция [archive]:

    [archive]
    host = 192.168.0.200
    port = 3050
    database = C:\\data\\lawyer_fee\\DECREE_ARCHIVE.FDB
    user = SYSDBA
    password = masterkey
    charset = WIN1251

Структура таблиц — см. archive_db.sql.
"""

import json

from app.services.state_serializer import state_to_dict


INSERT_DECREE = """
INSERT INTO DECREES (
    USERNAME, CASE_NUMBER, CASE_SOURCE,
    LAWYER_FIO, DEFENDANT_FIO,
    SERVICES_TOTAL, EXTRA_TOTAL, FULL_TOTAL,
    SNAPSHOT
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
RETURNING ID
"""

INSERT_SERVICE = """
INSERT INTO DECREE_SERVICES (DECREE_ID, SERVICE_DATE, SERVICE_NAME, AMOUNT, IS_SESSION)
VALUES (?, ?, ?, ?, ?)
"""

INSERT_EXTRA = """
INSERT INTO DECREE_EXTRAS (DECREE_ID, SOURCE_NAME, DECREE_DATE, AMOUNT)
VALUES (?, ?, ?, ?)
"""

SELECT_LIST = """
SELECT FIRST 300
    ID, CREATED_AT, CASE_NUMBER, LAWYER_FIO, DEFENDANT_FIO, SERVICES_TOTAL
FROM DECREES
WHERE USERNAME = ?
ORDER BY CREATED_AT DESC, ID DESC
"""

SELECT_SNAPSHOT = "SELECT SNAPSHOT FROM DECREES WHERE ID = ?"


class DecreeArchive:
    def __init__(self, db_client):
        self.db = db_client

    # ─── Запись ─────────────────────────────────────────────────────────

    def save_decree(self, state, username, services_total, extra_total, full_total):
        """Пишет постановление целиком (шапку + услуги + доп. постановления)
        одной транзакцией. Возвращает ID новой записи."""
        snapshot_json = json.dumps(
            state_to_dict(state), ensure_ascii=False, default=str
        )

        defendant = state.selected_defendant
        lawyer = state.selected_lawyer

        with self.db.connection() as conn:
            cur = conn.cursor()

            cur.execute(INSERT_DECREE, (
                username,
                state.case_number.value,
                state.case_source or "",
                (lawyer.fio if lawyer else ""),
                (defendant.fio if defendant else ""),
                services_total,
                extra_total,
                full_total,
                snapshot_json,
            ))
            decree_id = cur.fetchone()[0]

            for s in state.services:
                cur.execute(INSERT_SERVICE, (
                    decree_id,
                    s.service_date,
                    s.service_name,
                    s.amount,
                    1 if s.is_session else 0,
                ))

            if state.use_extra_decrees:
                for x in state.extra_decrees:
                    cur.execute(INSERT_EXTRA, (
                        decree_id,
                        x.source,
                        x.decree_date,
                        x.amount,
                    ))

            conn.commit()

        return decree_id

    # ─── Чтение ─────────────────────────────────────────────────────────

    def list_decrees(self, username):
        """Список постановлений пользователя (свежие сверху).

        Возвращает список словарей:
        {id, created_at, case_number, lawyer_fio, defendant_fio,
         services_total, services: [...], extras: [...]}
        """
        rows = self.db.fetch_all(SELECT_LIST, (username,))

        records = []
        ids = []
        for row in rows:
            records.append({
                "id": row[0],
                "created_at": row[1],
                "case_number": row[2] or "",
                "lawyer_fio": row[3] or "",
                "defendant_fio": row[4] or "",
                "services_total": row[5],
                "services": [],
                "extras": [],
            })
            ids.append(int(row[0]))

        if not ids:
            return records

        by_id = {r["id"]: r for r in records}
        ids_csv = ",".join(str(i) for i in ids)   # только int — безопасно

        svc_rows = self.db.fetch_all(
            "SELECT DECREE_ID, SERVICE_DATE, SERVICE_NAME, AMOUNT "
            "FROM DECREE_SERVICES WHERE DECREE_ID IN ({0}) "
            "ORDER BY DECREE_ID, SERVICE_DATE".format(ids_csv)
        )
        for row in svc_rows:
            rec = by_id.get(row[0])
            if rec is not None:
                rec["services"].append({
                    "date": row[1],
                    "name": row[2] or "",
                    "amount": row[3],
                })

        ext_rows = self.db.fetch_all(
            "SELECT DECREE_ID, SOURCE_NAME, DECREE_DATE, AMOUNT "
            "FROM DECREE_EXTRAS WHERE DECREE_ID IN ({0}) "
            "ORDER BY DECREE_ID, DECREE_DATE".format(ids_csv)
        )
        for row in ext_rows:
            rec = by_id.get(row[0])
            if rec is not None:
                rec["extras"].append({
                    "source": row[1] or "",
                    "date": row[2],
                    "amount": row[3],
                })

        return records

    def get_snapshot(self, decree_id):
        """Возвращает снапшот состояния как dict или None."""
        row = self.db.fetch_one(SELECT_SNAPSHOT, (int(decree_id),))
        if not row or not row[0]:
            return None

        raw = row[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return None
