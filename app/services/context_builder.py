# -*- coding: utf-8 -*-

from app.constants import PAYMENT_RULE_OPTIONS
from app.services.date_service import (
    format_date,
    format_russian_date,
    format_dates_list_numeric,
    format_russian_dates_list,
)
from app.services.money_to_text import (
    format_money,
    money_words_only,
    money_units_text,
    money_with_words,
)


# Добавить как отдельную функцию перед классом ContextBuilder:
def _days_word(n):
    """Возвращает число + правильную форму слова 'день'."""
    last_two = n % 100
    last_one = n % 10
    if 11 <= last_two <= 14:
        word = "дней"
    elif last_one == 1:
        word = "день"
    elif 2 <= last_one <= 4:
        word = "дня"
    else:
        word = "дней"
    return "{0} {1}".format(n, word)


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
        defendant_native = defendant.native if defendant else ""
        defendant_birth_date = defendant.birth_date if defendant else None
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

            # Только для материалов
            "сущность": getattr(state, "case_sub_type", None).value if getattr(state, "case_sub_type", None) else "",
            "ходатайство/представление": self._build_petition_word(state),
            "приговор или постановление": self._build_verdict_or_decree_text(state),

            # Вводная часть
            "вводная часть": self._build_intro_text(state),
            "сведения о подсудимом во вводной части": self._build_defendant_intro_text(state),
            "данные подсудимого во вводной части": self._build_defendant_intro_text(state),
            "__use_custom_intro": state.use_custom_intro,
            "__custom_intro_segments": state.custom_intro_segments,

            # Подсудимый
            "подсудимый": defendant_fio,
            "подсудимый пол": defendant_sex,
            "подсудимый дата рождения": format_date(defendant_birth_date),
            "дата рождения": format_russian_date(defendant_birth_date),
            "уроженец": defendant_native,
            "подсудимый уроженец": defendant_native,
            "подсудимый статья": defendant_article,
            "основная статья": defendant_article,
            "осуждение": self._build_conviction_word(state),

            # Словоформы по полу подсудимого
            "подсудимого пол": self._gender_word(defendant_sex, "подсудимого", "подсудимой"),
            "обвиняемого пол": self._gender_word(defendant_sex, "обвиняемого", "обвиняемой"),
            "осужденного пол": self._gender_word(defendant_sex, "осуждённого", "осуждённой"),
            "осуждённого пол": self._gender_word(defendant_sex, "осуждённого", "осуждённой"),
            "осуждённым пол": self._gender_word(defendant_sex, "осуждённым", "осуждённой"),
            "содержащимся пол": self._gender_word(defendant_sex, "содержащимся", "содержащейся"),
            "который пол": self._gender_word(defendant_sex, "который", "которая"),
            "его/её пол": self._gender_word(defendant_sex, "его", "её"),
            "него/неё пол": self._gender_word(defendant_sex, "него", "неё"),

            # Адвокат
            "адвокат": lawyer_fio,
            "фио адвоката": lawyer_fio,

            # Получатель / реквизиты — нижний регистр, потому что TagResolver приводит тег к lower()
            # Каждый реквизит включает свой разделитель ", ЛЕЙБЛ ЗНАЧЕНИЕ" или пустую строку
            "наименование получателя": recipient_name,
            "адвокат получатель": recipient_name,
            "получатель": recipient_name,

            "инн": self._labeled("ИНН", inn),
            "адвокат инн": self._labeled("ИНН", inn),

            "кпп": self._labeled("КПП", kpp),
            "адвокат кпп": self._labeled("КПП", kpp),

            "расчетный счет": self._labeled("р/счёт", account),
            "адвокат счет": self._labeled("р/счёт", account),
            "счет": self._labeled("р/счёт", account),

            "банк получателя": self._labeled("", bank),
            "адвокат банк": self._labeled("", bank),
            "банк": self._labeled("", bank),

            "бик": self._labeled("БИК", bik),
            "адвокат бик": self._labeled("БИК", bik),

            "корр. счет банка получателя": self._labeled("кор. счёт", corr_account),
            "корр счет банка получателя": self._labeled("кор. счёт", corr_account),
            "корр. счёт банка получателя": self._labeled("кор. счёт", corr_account),
            "корр счёт банка получателя": self._labeled("кор. счёт", corr_account),
            "адвокат корр счет": self._labeled("кор. счёт", corr_account),

            # Суммы
            "заявлено адвокатом": format_money(state.lawyer_claimed_amount),
            "адвокатом заявлена выплата вознаграждения": format_money(state.lawyer_claimed_amount),

            "вознаграждение": format_money(reward_base),
            "вознаграждение с процентами": format_money(reward_with_coefficients),

            "количество услуг": str(len(state.services)),
            "количество дней": _days_word(len(state.services)),
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
            "мнение сторон о взыскании": self._build_prosecution_opinion_text(state),
            "заявление адвоката удовлетворить": self._build_application_acceptance_text(state),
            "основания размера оплаты": self._build_payment_grounds_text(state),
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

        # Ручные правки склонений (используются в tag_resolver до автосклонения)
        context["__declension_overrides"] = dict(getattr(state, "declension_overrides", {}))

        return context

    def _build_intro_text(self, state):
        mode = getattr(state, "intro_mode", "default")

        if mode == "chamber":
            return (
                "Судья Благовещенского городского суда Амурской области "
                "{судья ио bold}, рассмотрев заявление адвоката {фио адвоката рп} "
                "о выплате вознаграждения за осуществление защиты "
                "{обвиняемого пол} {подсудимый рп},"
            )

        if state.use_custom_intro and state.custom_intro_text:
            return state.custom_intro_text

        return (
            "Благовещенский городской суд Амурской области в составе:\n"
            "председательствующего - судьи {судья рп ио bold},\n"
            "при секретаре {секретарь пп ио bold},\n"
            "с участием:\n"
            "государственного обвинителя {гос обвинитель рп ио bold},\n"
            "{подсудимого пол} {подсудимый рп ио bold},\n"
            "его защитника – адвоката {адвокат рп ио bold},\n"
            "рассмотрев в открытом судебном заседании уголовное дело в отношении:"
        )

    def _build_application_acceptance_text(self, state):
        """Текст для маркера {заявление адвоката удовлетворить} —
        зависит от режима «Кабинетно».
        """
        if getattr(state, "intro_mode", "default") == "chamber":
            return (
                "Заявление адвоката {фио адвоката рп ио} подлежит "
                "удовлетворению по следующим основаниям."
            )
        return (
            "Выслушав участников процесса, суд находит заявление адвоката "
            "{фио адвоката рп ио} подлежащим удовлетворению по следующим основаниям."
        )

    def _build_defendant_intro_text(self, state):
        # В кабинетном режиме строка не заполняется — абзац удалится
        if getattr(state, "intro_mode", "default") == "chamber":
            return ""

        return (
            "{подсудимый рп bold}, {родился пол} {дата рождения} в {уроженец},\n"
            "{обвиняемого пол} в совершении преступления, предусмотренного {основная статья},"
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
    def _build_petition_word(state):
        """Возвращает «ходатайство» или «представление» для маркера материалов."""
        choice = getattr(state, "petition_or_representation", "petition")
        return "представление" if choice == "representation" else "ходатайство"

    def _build_verdict_or_decree_text(self, state):
        """Текст для маркера {приговор или постановление}.

        - Уголовные дела: «Приговором … от {дата приговора} {осуждение} {подсудимый ио}.»
        - Материалы:      «Постановлением … от {дата приговора} разрешено {ходатайство/представление} {сущность}.»
        """
        source = getattr(state, "case_source", "")
        if source == "m":
            return (
                "Постановлением Благовещенского городского суда Амурской области "
                "от {дата приговора} разрешено {ходатайство/представление} {сущность}."
            )
        return (
            "Приговором Благовещенского городского суда Амурской области "
            "от {дата приговора} {осуждение} {подсудимый ио}."
        )

    @staticmethod
    def _gender_word(sex, male_form, female_form):
        """Возвращает мужскую или женскую форму слова по полу подсудимого."""
        if "жен" in (sex or "").lower():
            return female_form
        return male_form

    @staticmethod
    def _labeled(label, value):
        """Возвращает ', ЛЕЙБЛ ЗНАЧЕНИЕ' (с ведущей запятой) или пустую строку.

        Если label пустой — возвращает ', ЗНАЧЕНИЕ' без названия.
        Шаблон должен иметь маркеры без запятых между ними:
        {наименование получателя}{инн}{кпп}{расчетный счет}{банк получателя}{бик}{корр. счёт}
        """
        value = (value or "").strip()
        if not value:
            return ""
        label = (label or "").strip()
        if label:
            return ", {0} {1}".format(label, value)
        return ", {0}".format(value)

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
        return format_dates_list_numeric(dates)

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

        return " ".join(lines)

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

        return " ".join(lines)

    def _build_prosecution_opinion_text(self, state):
        """Строит текст для маркера {мнение сторон о взыскании}."""
        # В кабинетном режиме мнение сторон не учитывается — абзац удалится.
        if getattr(state, "intro_mode", "default") == "chamber":
            return ""

        if state.prosecutor_proposes_recovery:
            action = "взыскать с {осужденного пол}"
        else:
            action = "освободить {осужденного пол} от взыскания процессуальных издержек"

        reaction = "возражал" if state.defendant_objected else "не возражал"

        # В материалах — «Прокурор», в уголовных делах — «Государственный обвинитель»
        if getattr(state, "case_source", "") == "m":
            subject = "Прокурор"
        else:
            subject = "Государственный обвинитель"

        return (
            "{0} предлагал процессуальные издержки {1}, "
            "{{который пол}} {2}.".format(subject, action, reaction)
        )

    def _build_payment_grounds_text(self, state):
        """Строит текст для маркера {основания размера оплаты} из выбранных галочек."""
        grounds = state.payment_rule.grounds or []
        return " ".join(grounds)

    def _build_recovery_reasoning_text(self, state, full_total):
        """Строит текст для маркера {взыскание или освобождение} по выбранному режиму."""
        mode = getattr(state, "recovery_mode", "recovery")

        if mode == "recovery":
            if getattr(state, "defendant_objected", True):
                # Подсудимый возражал — с расширенным текстом
                return (
                    "Обязанность по возмещению процессуальных издержек, связанных с выплатой "
                    "вознаграждения адвокату, суд возлагает на осуждённого {подсудимый ио}, "
                    "который является трудоспособным и способным к возмещению судебных издержек. "
                    "Препятствия для их взыскания с осуждённого отсутствуют. Вопреки доводам "
                    "осуждённого, ни в одной из стадий производства по делу от услуг защитника "
                    "он не отказывался. Данных о том, что адвокаты фактически не оказывали ему "
                    "юридическую помощь, материалы дела не содержат. Само по себе назначенное "
                    "судом наказание, при установленных обстоятельствах, препятствием для взыскания "
                    "с осуждённого процессуальных издержек не является."
                )
            else:
                # Подсудимый не возражал — краткий текст
                return (
                    "Обязанность по возмещению процессуальных издержек, связанных с выплатой "
                    "вознаграждения адвокату, суд возлагает на осуждённого {подсудимый ио}, "
                    "который является трудоспособным и способным к возмещению судебных издержек. "
                    "Препятствия для их взыскания с осуждённого отсутствуют. Само по себе назначенное "
                    "судом наказание, при установленных обстоятельствах, препятствием для взыскания "
                    "с осуждённого процессуальных издержек не является."
                )

        elif mode == "exempt_insolvency":
            return (
                "В соответствии с ч. 6 ст. 132 УПК РФ, учитывая возраст, семейное положение и состояние здоровья "
                "{подсудимый рп ио}, суд считает необходимым освободить {его/её пол} от взыскания процессуальных "
                "издержек в связи с имущественной несостоятельностью. "
            )

        elif mode == "exempt_special":
            return (
                "Уголовное дело в отношении {подсудимый рп ио} рассмотрено судом в особом порядке, "
                "предусмотренном главой 40 УПК РФ. При таких обстоятельствах, в соответствии с ч.10 ст.316 "
                "УПК РФ осуждённый подлежит освобождению от взыскания с него процессуальных издержек."
            )

        elif mode == "not_considered":
            return (
                "Поскольку уголовное дело в отношении {подсудимый рп} по существу не рассмотрено, "
                "вопрос о взыскании с {него/неё пол} процессуальных издержек обсуждению не подлежит."
            )

        return ""

    def _build_recovery_result_text(self, state, full_total):
        """Строит текст для маркера {взыскать или освободить}."""
        mode = getattr(state, "recovery_mode", "recovery")

        if mode == "not_considered":
            # Маркер не заполняется — абзац удалится
            return ""

        if mode == "recovery":
            return (
                "Взыскать с {{подсудимый рп}} процессуальные издержки в сумме "
                "{0} ({1}) {2}."
            ).format(
                format_money(full_total),
                money_words_only(full_total),
                money_units_text(full_total),
            )

        return (
            "Освободить {подсудимый вп} от взыскания с {него/неё пол} процессуальных издержек, "
            "связанных с выплатой вознаграждения адвокату."
        )

    def _build_custody_text(self, state):
        defendant = state.selected_defendant

        if defendant is not None and defendant.in_custody:
            return (
                "Постановление может быть обжаловано в апелляционном порядке в судебную "
                "коллегию по уголовным делам Амурского областного суда через Благовещенский "
                "городской суд Амурской области в течение 15 суток со дня его вынесения, "
                "а {осуждённым пол}, {содержащимся пол} под стражей, - в тот же срок со дня вручения "
                "ему копии постановления."
            )

        return (
            "Постановление может быть обжаловано в апелляционном порядке в судебную "
            "коллегию по уголовным делам Амурского областного суда через Благовещенский "
            "городской суд Амурской области в течение 15 суток со дня его вынесения."
        )