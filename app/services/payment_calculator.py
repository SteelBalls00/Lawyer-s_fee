# -*- coding: utf-8 -*-

from decimal import Decimal, ROUND_HALF_UP


class PaymentCalculator(object):
    def __init__(self, rates):
        self.rates = rates

    @staticmethod
    def _round_money(value):
        return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def get_base_rate(self, rule_letter: str, target_date):
        return self.rates.get_rate(rule_letter, target_date)

    def apply_coefficients(self, base_amount: int, add_region_20: bool, add_experience_30: bool):
        multiplier = Decimal("1.0")

        if add_region_20:
            multiplier += Decimal("0.2")

        if add_experience_30:
            multiplier += Decimal("0.3")

        result = Decimal(str(base_amount)) * multiplier
        return self._round_money(result)

    def get_amount_for_date(self, payment_rule, target_date):
        base_amount = self.get_base_rate(payment_rule.letter, target_date)
        return self.apply_coefficients(
            base_amount=base_amount,
            add_region_20=payment_rule.add_region_20,
            add_experience_30=payment_rule.add_experience_30,
        )

    @staticmethod
    def get_services_total(services):
        total = 0
        for item in services:
            total += int(item.amount or 0)
        return total

    @staticmethod
    def get_extra_decrees_total(extra_decrees):
        total = 0
        for item in extra_decrees:
            total += int(item.amount or 0)
        return total

    def get_full_total(self, services, extra_decrees):
        return self.get_services_total(services) + self.get_extra_decrees_total(extra_decrees)