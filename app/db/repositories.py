# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional

from app.state import CaseCard, DefendantCard, EventCard, LawyerRequisites
from app.db.queries import (
    U1_GET_CASE_INFO,
    U1_GET_DEFENDANTS_INFO,
    U1_GET_SUD_ZASEDANIE_INFO,
    U1_GET_PARTS_INFO,
    U1_GET_PARTS_REQUISITE,
    M_GET_CASE_INFO,
    M_GET_DEFENDANTS_INFO,
    M_GET_SUD_ZASEDANIE_INFO,
    M_GET_PARTS_INFO,
)


SOURCE_U1 = "u1"
SOURCE_M = "m"


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def _guess_sources(case_number: str) -> List[str]:
    """Подсказывает, в каких картотеках искать дело по префиксу номера.

    Возвращает список картотек, в которых имеет смысл искать.
    Финальное решение (если дело есть в обеих) принимает пользователь.
    """
    cn = (case_number or "").strip()
    if not cn:
        return []

    # Дела с префиксом "10-" могут быть и в уголовной картотеке, и в материалах
    if cn.startswith("10-"):
        return [SOURCE_U1, SOURCE_M]
    # Префикс "1-" — точно уголовные дела
    if cn.startswith("1-"):
        return [SOURCE_U1]
    # Всё остальное — материалы
    return [SOURCE_M]


class CaseRepository(object):
    def __init__(self, db_client):
        self.db = db_client

    @staticmethod
    def _normalize_case_number(case_number: str) -> str:
        return (case_number or "").strip()

    @staticmethod
    def _escape_sql_string(value: str) -> str:
        return (value or "").replace("'", "''")

    @classmethod
    def _like_param(cls, case_number: str) -> str:
        case_number = cls._normalize_case_number(case_number)
        case_number = cls._escape_sql_string(case_number)
        return "%{0}%".format(case_number)

    @classmethod
    def _prepare_case_query(cls, query: str, case_number: str) -> str:
        return query.replace("__CASE_NUMBER__", cls._like_param(case_number))

    # ─── Поиск дела во всех картотеках ──────────────────────────────────

    def find_case_sources(self, case_number: str) -> List[str]:
        """Возвращает список картотек, где найдено дело с этим номером.

        Сначала проверяет вероятные картотеки по префиксу, при двусмысленности
        ("10-") опрашивает обе.
        """
        candidates = _guess_sources(case_number)
        found = []
        for source in candidates:
            if self._case_exists(case_number, source):
                found.append(source)
        return found

    def _case_exists(self, case_number: str, source: str) -> bool:
        if source == SOURCE_U1:
            query = self._prepare_case_query(U1_GET_CASE_INFO, case_number)
        else:
            query = self._prepare_case_query(M_GET_CASE_INFO, case_number)
        return self.db.fetch_one(query) is not None

    # ─── Основные запросы с явным источником ────────────────────────────

    def get_case_info(self, case_number: str, source: str) -> Optional[CaseCard]:
        if source == SOURCE_U1:
            query = self._prepare_case_query(U1_GET_CASE_INFO, case_number)
        else:
            query = self._prepare_case_query(M_GET_CASE_INFO, case_number)

        row = self.db.fetch_one(query)
        if not row:
            return None

        # У материалов 7-я колонка — sub_type
        sub_type = row[6] if (source == SOURCE_M and len(row) > 6) else ""

        return CaseCard(
            case_id=row[0],
            full_number=row[1] or "",
            judicial_uid=row[2] or "",
            judge=row[3] or "",
            verdict_date=_to_date(row[4]),
            verdict_name=row[5] or "",
            sub_type=(sub_type or ""),
        )

    def get_defendants(self, case_number: str, source: str) -> List[DefendantCard]:
        if source == SOURCE_U1:
            query = self._prepare_case_query(U1_GET_DEFENDANTS_INFO, case_number)
        else:
            query = self._prepare_case_query(M_GET_DEFENDANTS_INFO, case_number)

        is_materials = (source == SOURCE_M)
        rows = self.db.fetch_all(query)
        result = []
        for row in rows:
            native = row[4] if (len(row) > 4 and not is_materials) else ""
            result.append(
                DefendantCard(
                    fio=row[0] or "",
                    sex=row[1] or "",
                    birth_date=_to_date(row[2]),
                    article=row[3] or "",
                    native=native or "",
                )
            )
        return result

    def get_events(self, case_number: str, source: str) -> List[EventCard]:
        if source == SOURCE_U1:
            query = self._prepare_case_query(U1_GET_SUD_ZASEDANIE_INFO, case_number)
        else:
            query = self._prepare_case_query(M_GET_SUD_ZASEDANIE_INFO, case_number)

        rows = self.db.fetch_all(query)
        result = []
        for row in rows:
            result.append(
                EventCard(
                    event_name=row[0] or "",
                    event_result=row[1] or "",
                    reason_for_result=row[2] or "",
                    event_date=_to_date(row[3]),
                )
            )
        return result

    def get_lawyer_names(self, case_number: str, source: str) -> List[str]:
        if source == SOURCE_U1:
            query = self._prepare_case_query(U1_GET_PARTS_INFO, case_number)
        else:
            query = self._prepare_case_query(M_GET_PARTS_INFO, case_number)

        rows = self.db.fetch_all(query)
        result = []
        for row in rows:
            fio = (row[0] or "").strip()
            if fio and fio not in result:
                result.append(fio)
        return result

    def get_lawyer_requisites(self, lawyer_fio: str) -> Optional[LawyerRequisites]:
        row = self.db.fetch_one(U1_GET_PARTS_REQUISITE, (lawyer_fio,))
        if not row:
            return None
        return LawyerRequisites(
            part_id=row[0],
            fio=row[1] or "",
            recipient_name=row[2] or "",
            inn=row[3] or "",
            kpp=row[4] or "",
            account=row[5] or "",
            bank=row[6] or "",
            bik=row[7] or "",
            corr_account=row[8] or "",
        )

    def get_lawyers_with_requisites(self, case_number: str, source: str) -> List[LawyerRequisites]:
        names = self.get_lawyer_names(case_number, source)
        result = []
        for fio in names:
            requisites = self.get_lawyer_requisites(fio)
            if requisites is not None:
                result.append(requisites)
            else:
                result.append(LawyerRequisites(fio=fio))
        return result
