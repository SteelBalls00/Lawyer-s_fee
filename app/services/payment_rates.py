# -*- coding: utf-8 -*-

import configparser
from datetime import datetime


class PaymentRates(object):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._rates = {}
        self.load()

    def load(self):
        parser = configparser.ConfigParser()
        parser.optionxform = str

        read_files = parser.read(self.file_path, encoding="utf-8")
        if not read_files:
            raise FileNotFoundError(
                "Не найден файл ставок оплаты: {0}".format(self.file_path)
            )

        rates = {}

        for section in parser.sections():
            section_name = section.strip().upper()
            section_rates = []

            for key, value in parser.items(section):
                start_date = datetime.strptime(key.strip(), "%d.%m.%Y").date()
                amount = int(str(value).strip())
                section_rates.append((start_date, amount))

            section_rates.sort(key=lambda x: x[0])
            rates[section_name] = section_rates

        self._rates = rates

    def get_rate(self, rule_letter: str, target_date):
        if not rule_letter or target_date is None:
            return 0

        rule_letter = rule_letter.strip().upper()
        variants = self._rates.get(rule_letter, [])

        if not variants:
            return 0

        selected_amount = 0

        for start_date, amount in variants:
            if start_date <= target_date:
                selected_amount = amount
            else:
                break

        return selected_amount