# -*- coding: utf-8 -*-

from datetime import date

from app.state import AppState


class CaseController(object):
    def __init__(self, state: AppState, repository):
        self.state = state
        self.repository = repository

    def load_case(self, case_number: str) -> bool:
        case_number = (case_number or "").strip()
        if not case_number:
            raise ValueError("Не указан номер дела")

        self.state.reset_case_related_data()

        case_info = self.repository.get_case_info(case_number)
        if case_info is None:
            return False

        defendants = self.repository.get_defendants(case_number)
        events = self.repository.get_events(case_number)
        lawyers = self.repository.get_lawyers_with_requisites(case_number)

        self.state.case_card = case_info
        self.state.defendants = defendants
        self.state.events = events
        self.state.lawyers = lawyers

        self.state.case_number.set_db_value(case_info.full_number)
        self.state.judicial_uid.set_db_value(case_info.judicial_uid)
        self.state.judge.set_db_value(case_info.judge)

        if case_info.verdict_date:
            verdict_date_text = case_info.verdict_date.strftime("%d.%m.%Y")
        else:
            verdict_date_text = ""

        self.state.verdict_date.set_db_value(verdict_date_text)

        # По умолчанию дата постановления совпадает с датой приговора.
        # Если даты приговора нет, тогда ставим текущую дату как запасной вариант.
        if verdict_date_text:
            self.state.decree_date.set_db_value(verdict_date_text)
        else:
            self.state.decree_date.set_db_value(date.today().strftime("%d.%m.%Y"))

        self.state.selected_defendant_index = 0
        self.state.selected_lawyer_index = 0

        return True