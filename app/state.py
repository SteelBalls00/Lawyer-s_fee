# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from decimal import Decimal


@dataclass
class EditableField:
    db_value: str = ""
    user_value: str = ""

    @property
    def value(self) -> str:
        return self.user_value.strip() or self.db_value.strip()

    def clear_user_value(self) -> None:
        self.user_value = ""

    def set_db_value(self, value: str) -> None:
        self.db_value = value or ""

    def set_user_value(self, value: str) -> None:
        self.user_value = value or ""


@dataclass
class CaseCard:
    case_id: Optional[int] = None
    full_number: str = ""
    judicial_uid: str = ""
    judge: str = ""
    verdict_date: Optional[date] = None
    verdict_name: str = ""


@dataclass
class DefendantCard:
    fio: str = ""
    sex: str = ""
    birth_date: Optional[date] = None
    article: str = ""
    in_custody: bool = False


@dataclass
class EventCard:
    event_name: str = ""
    event_result: str = ""
    reason_for_result: str = ""
    event_date: Optional[date] = None


@dataclass
class LawyerRequisites:
    part_id: Optional[int] = None
    fio: str = ""
    recipient_name: str = ""
    inn: str = ""
    kpp: str = ""
    account: str = ""
    bank: str = ""
    bik: str = ""
    corr_account: str = ""


@dataclass
class PaymentRule:
    letter: str = "A"
    add_region_20: bool = True
    add_experience_30: bool = True


@dataclass
class ServiceRow:
    service_date: Optional[date] = None
    service_name: str = ""
    amount: Decimal = Decimal("0.00")
    is_session: bool = False


@dataclass
class ExtraDecreeRow:
    source: str = ""
    decree_date: Optional[date] = None
    amount: Decimal = Decimal("0.00")


@dataclass
class AppState:
    case_card: CaseCard = field(default_factory=CaseCard)

    case_number: EditableField = field(default_factory=EditableField)
    judicial_uid: EditableField = field(default_factory=EditableField)
    decree_date: EditableField = field(default_factory=EditableField)
    judge: EditableField = field(default_factory=EditableField)
    secretary: EditableField = field(default_factory=EditableField)
    prosecutor: EditableField = field(default_factory=EditableField)
    verdict_date: EditableField = field(default_factory=EditableField)

    defendants: List[DefendantCard] = field(default_factory=list)
    selected_defendant_index: int = 0

    lawyers: List[LawyerRequisites] = field(default_factory=list)
    selected_lawyer_index: int = 0
    lawyer_claimed_amount: Decimal = Decimal("0.00")

    events: List[EventCard] = field(default_factory=list)

    use_custom_intro: bool = False
    custom_intro_text: str = ""

    payment_rule: PaymentRule = field(default_factory=PaymentRule)
    services: List[ServiceRow] = field(default_factory=list)

    use_extra_decrees: bool = False
    extra_decrees: List[ExtraDecreeRow] = field(default_factory=list)

    def reset_case_related_data(self) -> None:
        self.case_card = CaseCard()

        self.case_number = EditableField()
        self.judicial_uid = EditableField()
        self.decree_date = EditableField()
        self.judge = EditableField()
        self.secretary = EditableField()
        self.prosecutor = EditableField()
        self.verdict_date = EditableField()

        self.defendants = []
        self.selected_defendant_index = 0

        self.lawyers = []
        self.selected_lawyer_index = 0
        self.lawyer_claimed_amount = Decimal("0.00")

        self.events = []

        self.use_custom_intro = False
        self.custom_intro_text = ""

        self.services = []

        self.use_extra_decrees = False
        self.extra_decrees = []

    @property
    def selected_defendant(self) -> Optional[DefendantCard]:
        if 0 <= self.selected_defendant_index < len(self.defendants):
            return self.defendants[self.selected_defendant_index]
        return None

    @property
    def selected_lawyer(self) -> Optional[LawyerRequisites]:
        if 0 <= self.selected_lawyer_index < len(self.lawyers):
            return self.lawyers[self.selected_lawyer_index]
        return None