# -*- coding: utf-8 -*-

from datetime import date

from app.state import AppState


class CaseController(object):
    def __init__(self, state: AppState, repository):
        self.state = state
        self.repository = repository

    def find_sources(self, case_number: str):
        """Возвращает список картотек, где найдено дело: 'u1', 'm' или обе."""
        case_number = (case_number or "").strip()
        if not case_number:
            raise ValueError("Не указан номер дела")
        return self.repository.find_case_sources(case_number)

    def load_case(self, case_number: str, source: str) -> bool:
        """Загружает дело из указанной картотеки.

        source: 'u1' — уголовные дела, 'm' — материалы.
        """
        case_number = (case_number or "").strip()
        if not case_number:
            raise ValueError("Не указан номер дела")
        if source not in ("u1", "m"):
            raise ValueError("Неизвестная картотека: {0}".format(source))

        self.state.reset_case_related_data()

        case_info = self.repository.get_case_info(case_number, source)
        if case_info is None:
            return False

        defendants = self.repository.get_defendants(case_number, source)
        events = self.repository.get_events(case_number, source)
        lawyers = self.repository.get_lawyers_with_requisites(case_number, source)

        self.state.case_card = case_info
        self.state.case_source = source
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

        if verdict_date_text:
            self.state.decree_date.set_db_value(verdict_date_text)
        else:
            self.state.decree_date.set_db_value("")

        # Для материалов — заполняем sub_type и автоматически выставляем
        # ходатайство/представление по первой букве номера материала
        if source == "m":
            self.state.case_sub_type.set_db_value(case_info.sub_type or "")
            first_char = case_info.full_number.strip()[:1].lower()
            if first_char in ("а", "a"):
                self.state.petition_or_representation = "petition"
            else:
                self.state.petition_or_representation = "representation"

        self.state.selected_defendant_index = 0
        self.state.selected_lawyer_index = 0

        return True
