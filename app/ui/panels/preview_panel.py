# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from app.constants import PAYMENT_RULE_OPTIONS


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._build_ui()

    def _build_ui(self):
        self.preview_browser = QTextBrowser()

        layout = QVBoxLayout()
        layout.addWidget(self.preview_browser)

        self.setLayout(layout)

    def update_preview(self, state):
        self.preview_browser.setPlainText(self._build_preview_text(state))

    def _build_preview_text(self, state):
        lines = []
        lines.append("ПРЕДПРОСМОТР")
        lines.append("")

        lines.append("Информация по делу")
        lines.append("------------------------------")
        lines.append("№ дела: {0}".format(state.case_number.value or "-"))
        lines.append("УИД: {0}".format(state.judicial_uid.value or "-"))
        lines.append("Дата постановления: {0}".format(state.decree_date.value or "-"))
        lines.append("Судья: {0}".format(state.judge.value or "-"))
        lines.append("Секретарь: {0}".format(state.secretary.value or "-"))
        lines.append("Гос. обвинитель: {0}".format(state.prosecutor.value or "-"))
        lines.append("Дата приговора: {0}".format(state.verdict_date.value or "-"))
        lines.append("")

        lines.append("Вводная часть")
        lines.append("------------------------------")
        if state.use_custom_intro:
            lines.append(state.custom_intro_text or "-")
        else:
            lines.append("Будет использована стандартная вводная часть")
        lines.append("")

        lines.append("Подсудимый")
        lines.append("------------------------------")
        defendant = state.selected_defendant
        if defendant is None:
            lines.append("Не выбран")
        else:
            lines.append("ФИО: {0}".format(defendant.fio or "-"))
            lines.append("Пол: {0}".format(defendant.sex or "-"))
            lines.append(
                "Дата рождения: {0}".format(
                    defendant.birth_date.strftime("%d.%m.%Y") if defendant.birth_date else "-"
                )
            )
            lines.append("Статья: {0}".format(defendant.article or "-"))
            lines.append("Под стражей: {0}".format("Да" if defendant.in_custody else "Нет"))
        lines.append("")

        lines.append("Адвокат")
        lines.append("------------------------------")
        lawyer = state.selected_lawyer
        if lawyer is None:
            lines.append("Не выбран")
        else:
            lines.append("ФИО: {0}".format(lawyer.fio or "-"))
            lines.append("Заявлено адвокатом: {0}".format(state.lawyer_claimed_amount or 0))
            lines.append("Получатель: {0}".format(lawyer.recipient_name or "-"))
            lines.append("ИНН: {0}".format(lawyer.inn or "-"))
            lines.append("КПП: {0}".format(lawyer.kpp or "-"))
            lines.append("Расчётный счёт: {0}".format(lawyer.account or "-"))
            lines.append("Банк: {0}".format(lawyer.bank or "-"))
            lines.append("БИК: {0}".format(lawyer.bik or "-"))
            lines.append("Корр. счёт: {0}".format(lawyer.corr_account or "-"))
        lines.append("")

        lines.append("Правило оплаты")
        lines.append("------------------------------")
        lines.append("Подпункт: {0}".format(self._rule_letter_to_text(state.payment_rule.letter)))
        lines.append("+20%: {0}".format("Да" if state.payment_rule.add_region_20 else "Нет"))
        lines.append("+30%: {0}".format("Да" if state.payment_rule.add_experience_30 else "Нет"))
        lines.append("")

        lines.append("Судебные заседания")
        lines.append("------------------------------")
        if not state.events:
            lines.append("Нет данных")
        else:
            for event in state.events:
                event_date = event.event_date.strftime("%d.%m.%Y") if event.event_date else "-"
                lines.append(
                    "{0} | {1} | {2}".format(
                        event_date,
                        event.event_name or "-",
                        event.event_result or "-"
                    )
                )

        lines.append("")
        lines.append("Услуги адвоката")
        lines.append("------------------------------")
        services_total = 0
        if not state.services:
            lines.append("Нет услуг")
        else:
            for item in state.services:
                service_date = item.service_date.strftime("%d.%m.%Y") if item.service_date else "-"
                lines.append(
                    "{0} | {1} | {2}".format(
                        service_date,
                        item.service_name or "-",
                        item.amount or 0,
                    )
                )
                services_total += int(item.amount or 0)

            lines.append("")
            lines.append("Число дней: {0}".format(len(state.services)))
            lines.append("Сумма услуг: {0}".format(services_total))

        lines.append("")
        lines.append("Дополнительные постановления")
        lines.append("------------------------------")
        extra_total = 0
        if not state.use_extra_decrees:
            lines.append("Нет")
        elif not state.extra_decrees:
            lines.append("Включены, но строки не заполнены")
        else:
            for item in state.extra_decrees:
                decree_date = item.decree_date.strftime("%d.%m.%Y") if item.decree_date else "-"
                lines.append(
                    "{0} | {1} | {2}".format(
                        item.source or "-",
                        decree_date,
                        item.amount or 0,
                    )
                )
                extra_total += int(item.amount or 0)

            lines.append("")
            lines.append("Сумма доп. постановлений: {0}".format(extra_total))

        if not state.use_extra_decrees:
            extra_total = 0

        lines.append("")
        lines.append("Итог")
        lines.append("------------------------------")
        lines.append("Сумма услуг адвоката: {0}".format(services_total))
        lines.append("Сумма доп. постановлений: {0}".format(extra_total))
        lines.append("Сумма вознаграждения в суде и на следствии: {0}".format(services_total + extra_total))

        return "\n".join(lines)

    @staticmethod
    def _rule_letter_to_text(value):
        for display_text, internal_value in PAYMENT_RULE_OPTIONS:
            if internal_value == value:
                return display_text
        return value or "-"