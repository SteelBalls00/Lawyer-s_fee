# -*- coding: utf-8 -*-

from app.constants import PAYMENT_RULE_OPTIONS
from app.services.date_service import (
    format_date,
    format_russian_date,
    group_dates_by_month_year,
    format_russian_dates_list,
)
from app.services.money_to_text import (
    format_money,
    money_words_only,
    money_units_text,
    money_with_words,
)


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

        defendant_fio = defendant.fio if defendant else ""
        defendant_sex = defendant.sex if defendant else ""
        defendant_article = defendant.article if defendant else ""

        lawyer_fio = lawyer.fio if lawyer else ""
        recipient_name = lawyer.recipient_name if lawyer else ""
        inn = lawyer.inn if lawyer else ""
        kpp = lawyer.kpp if lawyer else ""
        account = lawyer.account if lawyer else ""
        bank = lawyer.bank if lawyer else ""
        bik = lawyer.bik if lawyer else ""
        corr_account = lawyer.corr_account if lawyer else ""

        rule_display_letter = self._get_payment_rule_display_letter(state.payment_rule.letter)

        context = {
            # Дело
            "номер дела": state.case_number.value,
            "дело": state.case_number.value,
            "уид": state.judicial_uid.value,
            "дата постановления": state.decree_date.value,
            "судья": state.judge.value,
            "секретарь": state.secretary.value,
            "гос обвинитель": state.prosecutor.value,
            "гос. обвинитель": state.prosecutor.value,
            "государственный обвинитель": state.prosecutor.value,
            "дата приговора": state.verdict_date.value,

            # Вводная часть
            "вводная часть": self._build_intro_text(state),

            # Подсудимый
            "подсудимый": defendant_fio,
            "подсудимый пол": defendant_sex,
            "подсудимый дата рождения": format_date(defendant.birth_date) if defendant else "",
            "подсудимый статья": defendant_article,
            "основная статья": defendant_article,
            "осуждение": self._build_conviction_word(state),

            # Адвокат
            "адвокат": lawyer_fio,
            "фио адвоката": lawyer_fio,

            # Получатель / реквизиты — нижний регистр, потому что TagResolver приводит тег к lower()
            "наименование получателя": recipient_name,
            "адвокат получатель": recipient_name,
            "получатель": recipient_name,

            "инн": inn,
            "адвокат инн": inn,

            "кпп": kpp,
            "адвокат кпп": kpp,

            # В шаблоне написано "Рассчетный счет" с двумя "с", оставляем совместимость.
            "рассчетный счет": account,
            "расчетный счет": account,
            "адвокат счет": account,
            "счет": account,

            "банк получателя": bank,
            "адвокат банк": bank,
            "банк": bank,

            "бик": bik,
            "адвокат бик": bik,

            "корр. счет банка получателя": corr_account,
            "корр счет банка получателя": corr_account,
            "корр. счёт банка получателя": corr_account,
            "корр счёт банка получателя": corr_account,
            "адвокат корр счет": corr_account,

            # Суммы
            "заявлено адвокатом": format_money(state.lawyer_claimed_amount),
            "адвокатом заявлена выплата вознаграждения": format_money(state.lawyer_claimed_amount),

            "вознаграждение": format_money(reward_base),
            "вознаграждение с процентами": format_money(reward_with_coefficients),

            "количество услуг": str(len(state.services)),
            "вознаграждение за услуги": format_money(services_total),
            "вознаграждение за услуги прописью": money_words_only(services_total),
            "вознаграждение за услуги рублей копеек": money_units_text(services_total),
            "вознаграждение за услуги с прописью": money_with_words(services_total),

            "сумма дополнительных постановлений": format_money(extra_total),
            "итоговая сумма взыскания": format_money(full_total),
            "итоговая сумма взыскания прописью": money_words_only(full_total),
            "итоговая сумма взыскания рублей копеек": money_units_text(full_total),
            "итоговая сумма взыскания с прописью": money_with_words(full_total),

            # Правило оплаты
            "из пп. ст. 22 о возмещении процессуальных издержек": rule_display_letter,

            # Большие текстовые блоки
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
            context["+ 30% (непрерывный стаж работы)"] = " + 30% (непрерывный стаж работы) "
            context["+30% (непрерывный стаж работы)"] = "+30% (непрерывный стаж работы)"
        else:
            context["+ 30% (непрерывный стаж работы)"] = ""
            context["+30% (непрерывный стаж работы)"] = ""

        return context

    def _build_intro_text(self, state):
        if state.use_custom_intro and state.custom_intro_text:
            return state.custom_intro_text

        return (
            "Благовещенский городской суд Амурской области в составе:\n\n"
            "председательствующего - судьи {судья тп ио},\n\n"
            "при секретаре {секретарь тп ио},\n\n"
            "с участием:\n\n"
            "государственного обвинителя {гос обвинитель тп ио},\n"
            "подсудимого {подсудимый тп ио},\n"
            "его защитника – адвоката {адвокат тп ио},\n\n"
            "рассмотрев в открытом судебном заседании уголовное дело в отношении:\n\n"
            "{подсудимый тп}, {родился пол},\n\n"
            "обвиняемого в совершении преступления, предусмотренного {основная статья},"
        )

    def _build_conviction_word(self, state):
        defendant = state.selected_defendant
        if defendant is None:
            return "осуждён"

        sex = (defendant.sex or "").lower()
        if "жен" in sex:
            return "осуждена"

        return "осуждён"

    @staticmethod
    def _get_payment_rule_display_letter(rule_letter):
        for display_text, value in PAYMENT_RULE_OPTIONS:
            if value == rule_letter:
                return display_text
        return rule_letter or ""

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

            grouped[source]["amount"] += item.amount or 0

        lines = []

        for source, data in grouped.items():
            dates_text = format_russian_dates_list(data["dates"])
            amount = data["amount"]
            amount_text = format_money(amount)
            amount_units = money_units_text(amount)

            if source == "от следователя":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями следователя от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу адвокату "
                        "{{адвокат дп ио}} выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением следователя от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу адвокату "
                        "{{адвокат дп ио}} выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )

            elif source == "от судьи Благовещенского городского суда Амурской области":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями Благовещенского городского суда Амурской области от {0} "
                        "за осуществление защиты {{подсудимый рп ио}} на досудебной стадии производства "
                        "по делу при обжаловании постановления о продлении срока содержания под стражей "
                        "адвокату {{адвокат дп ио}} выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением судьи Благовещенского городского суда Амурской области "
                        "от {0} за осуществление защиты {{подсудимый рп ио}} на досудебной стадии производства "
                        "по делу при обжаловании постановления о продлении срока содержания под стражей "
                        "адвокату {{адвокат дп ио}} выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )

            elif source == "от судьи Амурского областного суда":
                if len(data["dates"]) > 1:
                    lines.append(
                        "Кроме того, постановлениями Амурского областного суда от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу при обжаловании "
                        "постановления о продлении срока содержания под стражей адвокату {{адвокат дп ио}} "
                        "выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )
                else:
                    lines.append(
                        "Кроме того, постановлением судьи Амурского областного суда от {0} за осуществление защиты "
                        "{{подсудимый рп ио}} на досудебной стадии производства по делу при обжаловании "
                        "постановления о продлении срока содержания под стражей адвокату {{адвокат дп ио}} "
                        "выплачено вознаграждение в сумме {1} {2}.".format(
                            dates_text,
                            amount_text,
                            amount_units,
                        )
                    )

            else:
                lines.append(
                    "Кроме того, постановлением {0} от {1} адвокату {{адвокат дп ио}} выплачено "
                    "вознаграждение в сумме {2} {3}.".format(
                        source,
                        dates_text,
                        amount_text,
                        amount_units,
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
                "федерального бюджета Российской Федерации следует взыскать {0} {1}."
            ).format(format_money(full_total), money_units_text(full_total),)

        if defendant is None:
            return "Подсудимый освобождается от взыскания."

        return "{подсудимый рп ио} освобождается от взыскания."

    def _build_recovery_result_text(self, state, full_total):
        if state.use_extra_decrees:
            return (
                "Взыскать с {{подсудимый тп}} процессуальные издержки в сумме "
                "{0} ({1}) {2}."
            ).format(
                format_money(full_total),
                money_words_only(full_total),
                money_units_text(full_total),
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