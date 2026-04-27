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
)


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


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

    def get_case_info(self, case_number: str) -> Optional[CaseCard]:
        query = self._prepare_case_query(U1_GET_CASE_INFO, case_number)
        row = self.db.fetch_one(query)
        if not row:
            return None

        return CaseCard(
            case_id=row[0],
            full_number=row[1] or "",
            judicial_uid=row[2] or "",
            judge=row[3] or "",
            verdict_date=_to_date(row[4]),
            verdict_name=row[5] or "",
        )

    def get_defendants(self, case_number: str) -> List[DefendantCard]:
        query = self._prepare_case_query(U1_GET_DEFENDANTS_INFO, case_number)
        rows = self.db.fetch_all(query)

        result = []
        for row in rows:
            result.append(
                DefendantCard(
                    fio=row[0] or "",
                    sex=row[1] or "",
                    birth_date=_to_date(row[2]),
                    article=row[3] or "",
                )
            )
        return result

    def get_events(self, case_number: str) -> List[EventCard]:
        query = self._prepare_case_query(U1_GET_SUD_ZASEDANIE_INFO, case_number)
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

    def get_lawyer_names(self, case_number: str) -> List[str]:
        query = self._prepare_case_query(U1_GET_PARTS_INFO, case_number)
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

    def get_lawyers_with_requisites(self, case_number: str) -> List[LawyerRequisites]:
        names = self.get_lawyer_names(case_number)
        result = []

        for fio in names:
            requisites = self.get_lawyer_requisites(fio)
            if requisites is not None:
                result.append(requisites)
            else:
                result.append(LawyerRequisites(fio=fio))

        return result