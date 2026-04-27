# -*- coding: utf-8 -*-

from app.services.date_service import (
    format_date,
    format_russian_date,
    group_dates_by_month_year,
    format_russian_dates_list,
)
from app.services.money_to_text import money_to_text


class ContextBuilder(object):
    def __init__(self, payment_calculator):
        self.payment_calculator = payment_calculator

    def build(self, state):
        defendant = state.selected_defendant
        lawyer = state.selected_lawyer

        services_total = self.payment_calculator.get_services_total(state.services)

        if state.use_extra_decrees:
            extra_total = self.payment_calculator.get_extra_decrees_total(state.extra_decrees)
        else:
            extra_total = 0

        full_total = services_total + extra_total

        last_service_date = self._get_last_service_date(state)
        reward_base = 0
        reward_with_coefficients = 0

        if last_service_date is not None:
            reward_base = self.payment_calculator.get_base_rate(
                state.payment_rule.letter,
                last_service_date,
            )
            reward_with_coefficients = self.payment_calculator.get_amount_for_date(
                state.payment_rule,
                last_service_date,
            )

        context = {
            "номер дела": state.case_number.value,
            "дело": state.case_number.value,
            "уид": state.judicial_uid.value,
            "дата постановления": state.decree_date.value,
            "судья": state.judge.value,
            "секретарь": state.secretary.value,
            "гос обвинитель": state.prosecutor.value,
            "государственный обвинитель": state.prosecutor.value,
            "дата приговора": state.verdict_date.value,

            "вводная часть": self._build_intro_text(state),

            "подсудимый": defendant.fio if defendant else "",
            "подсудимый пол": defendant.sex if defendant else "",
            "подсудимый дата рождения": format_date(defendant.birth_date) if defendant else "",
            "подсудимый статья": defendant.article if defendant else "",

            "адвокат": lawyer.fio if lawyer else "",
            "адвокат получатель": lawyer.recipient_name if lawyer else "",
            "адвокат инн": lawyer.inn if lawyer else "",
            "адвокат кпп": lawyer.kpp if lawyer else "",
            "адвокат счет": lawyer.account if lawyer else "",
            "адвокат банк": lawyer.bank if lawyer else "",
            "адвокат бик": lawyer.bik if lawyer else "",
            "адвокат корр счет": lawyer.corr_account if lawyer else "",

            "заявлено адвокатом": str(state.lawyer_claimed_amount or 0),

            "вознаграждение": str(reward_base),
            "вознаграждение с процентами": str(reward_with_coefficients),

            "количество услуг": str(len(state.services)),
            "вознаграждение за услуги": str(services_total),
            "вознаграждение за услуги прописью": money_to_text(services_total),

            "сумма дополнительных постановлений": str(extra_total),
            "итоговая сумма взыскания": str(full_total),
            "итоговая сумма взыскания прописью": money_to_text(full_total),

            "заседания": self._build_sessions_text(state),
            "услуги адвоката": self._build_services_text(state),
            "дополнительные постановления": self._build_extra_decrees_text(state),
            "взыскание или освобождение": self._build_recovery_reasoning_text(state, full_total),
            "взыскать или освободить": self._build_recovery_result_text(state, full_total),
            "под стражей": self._build_custody_text(state),
        }

        if state.payment_rule.add_region_20:
            context["+ 20% (районный коэффициент)"] = "+ 20% (районный коэффициент)"
            context["+20% (районный коэффициент)"] = "+20% (районный коэффициент)"
        else:
            context["+ 20% (районный коэффициент)"] = ""
            context["+20% (районный коэффициент)"] = ""

        if state.payment_rule.add_experience_30:
            context["+ 30% (непрерывный стаж работы)"] = "+ 30% (непрерывный стаж работы)"
            context["+30% (непрерывный стаж работы)"] = "+30% (непрерывный стаж работы)"
        else:
            context["+ 30% (непрерывный стаж работы)"] = ""
            context["+30% (непрерывный стаж работы)"] = ""

        return context

    def _build_intro_text(self, state):
        if state.use_custom_intro and state.custom_intro_text:
            return state.custom_intro_text

        return (
            "Судья Благовещенского городского суда Амурской области {судья},\n"
            "при секретаре {секретарь},\n"
            "с участием государственного обвинителя {гос обвинитель},\n\n"
            "рассмотрев материалы уголовного дела № {номер дела} в отношении "
            "{подсудимый рп ио},\n"
            "{родился пол}, обвиняемого по {подсудимый статья},"
        )

    def _get_last_service_date(self, state):
        dates = [item.service_date for item in state.services if item.service_date is not None]
        if not dates:
            return None
        return max(dates)

    def _build_sessions_text(self, state):
        dates = [
            item.service_date
            for item in state.services
            if item.service_name == "Участие в судебном заседании"
        ]
        return group_dates_by_month_year(dates)

    def _build_services_text(self, state):
        lines = []

        for item in state.services:
            if item.service_name == "Участие в судебном заседании":
                continue

            if item.service_date is None:
                date_text = ""
            else:
                date_text = format_russian_date(item.service_date)

            service_name = item.service_name or ""

            if service_name == "Ознакомление с материалами дела":
                lines.append(
                    "Кроме того, {0} адвокат готовился к судебному заседанию и изучал материалы уголовного дела.".format(
                        date_text
                    )
                )
            elif service_name == "Посещение СИЗО":
                lines.append(
                    "{0} адвокат встречался с подзащитным в следственном изоляторе.".format(
                        date_text
                    )
                )
            elif service_name == "Составление апелляционной жалобы":
                lines.append(
                    "{0} адвокат составлял апелляционную жалобу.".format(
                        date_text
                    )
                )
            elif service_name == "Подготовка к прениям сторон":
                lines.append(
                    "{0} адвокат готовился к прениям сторон.".format(
                        date_text
                    )
                )
            else:
                lines.append("{0} — {1}.".format(date_text, service_name))

        return "\n".join(lines)

    def _build_extra_decrees_text(self, state):
        if not state.use_extra_decrees:
            return ""

        grouped = {}

        for item in state.extra_decrees:
            source = item.source or ""
            if not source:
                continue

            if source not in grouped:
                grouped[source] = {
                    "dates": [],
                    "amount": 0,
                }

            if item.decree_date:
                grouped[source]["dates"].append(item.decree_date)

            grouped[source]["amount"] += int(item.amount or 0)

        lines = []

        for source, data in grouped.items():
            dates_text = format_russian_dates_list(data["dates"])
            amount = data["amount"]

            if source == "от следователя":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями следователя от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу адвокату "
                        "{{адвокат дп ио}} выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением следователя от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу адвокату "
                        "{{адвокат дп ио}} выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )

            elif source == "от судьи Благовещенского городского суда Амурской области":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями Благовещенского городского суда Амурской области от {0} "
                        "за осуществление защиты {{подсудимый рп ио}} на досудебной стадии производства "
                        "по делу при обжаловании постановления о продлении срока содержания под стражей "
                        "адвокату {{адвокат дп ио}} выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением судьи Благовещенского городского суда Амурской области "
                        "от {0} за осуществление защиты {{подсудимый рп ио}} на досудебной стадии производства "
                        "по делу при обжаловании постановления о продлении срока содержания под стражей "
                        "адвокату {{адвокат дп ио}} выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )

            elif source == "от судьи Амурского областного суда":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями Амурского областного суда от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу при обжаловании "
                        "постановления о продлении срока содержания под стражей адвокату {{адвокат дп ио}} "
                        "выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением судьи Амурского областного суда от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу при обжаловании "
                        "постановления о продлении срока содержания под стражей адвокату {{адвокат дп ио}} "
                        "выплачено вознаграждение в сумме {1} рублей.".format(
                            dates_text,
                            amount,
                        )
                    )

            else:
                lines.append(
                    "Кроме того, постановлением {0} от {1} адвокату {{адвокат дп ио}} выплачено "
                    "вознаграждение в сумме {2} рублей.".format(
                        source,
                        dates_text,
                        amount,
                    )
                )

        return "\n".join(lines)

    def _build_recovery_reasoning_text(self, state, full_total):
        defendant = state.selected_defendant

        if state.use_extra_decrees:
            return (
                "Все указанные денежные средства относятся к процессуальным издержкам.\n\n"
                "Обязанность по возмещению процессуальных издержек, связанных с выплатой "
                "вознаграждения адвокату, суд возлагает на осуждённого {{подсудимый рп ио}}, "
                "который является трудоспособным и способным к возмещению судебных издержек. "
                "Препятствия для их взыскания с осуждённого отсутствуют. Вопреки доводам "
                "осуждённого, ни в одной из стадий производства по делу от услуг защитника "
                "он не отказывался. Данных о том, что адвокаты фактически не оказывали ему "
                "юридическую помощь, материалы дела не содержат. Само по себе назначенное "
                "судом наказание, при установленных обстоятельствах, препятствием для взыскания "
                "с осуждённого процессуальных издержек не является. При таких обстоятельствах, "
                "на основании ч. 1 ст. 132 УПК РФ с осуждённого {{подсудимый рп ио}} в доход "
                "федерального бюджета Российской Федерации следует взыскать {0} рублей."
            ).format(full_total)

        if defendant is None:
            return "Подсудимый освобождается от взыскания."

        return "{подсудимый рп ио} освобождается от взыскания."

    def _build_recovery_result_text(self, state, full_total):
        if state.use_extra_decrees:
            return (
                "Взыскать с {{подсудимый тп}} процессуальные издержки в сумме "
                "{0} ({1})."
            ).format(
                full_total,
                money_to_text(full_total),
            )

        return (
            "Освободить {подсудимый рп} от взыскания с него процессуальных издержек, "
            "связанных с выплатой вознаграждения адвокату."
        )

    def _build_custody_text(self, state):
        defendant = state.selected_defendant

        if defendant is not None and defendant.in_custody:
            return (
                "Постановление может быть обжаловано в апелляционном порядке в судебную "
                "коллегию по уголовным делам Амурского областного суда через Благовещенский "
                "городской суд Амурской области в течение 15 суток со дня его вынесения, "
                "а осуждённым, содержащимся под стражей, - в тот же срок со дня вручения "
                "ему копии постановления."
            )

        return (
            "Постановление может быть обжаловано в апелляционном порядке в судебную "
            "коллегию по уголовным делам Амурского областного суда через Благовещенский "
            "городской суд Амурской области в течение 15 суток со дня его вынесения."
        )