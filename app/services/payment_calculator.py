# -*- coding: utf-8 -*-

from decimal import Decimal, ROUND_HALF_UP

from app.services.money_to_text import to_decimal_money


class PaymentCalculator(object):
    def __init__(self, rates):
        self.rates = rates

    @staticmethod
    def _round_money(value):
        value = to_decimal_money(value)
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_base_rate(self, rule_letter: str, target_date):
        return to_decimal_money(self.rates.get_rate(rule_letter, target_date))

    def apply_coefficients(self, base_amount, add_region_20: bool, add_experience_30: bool):
        base_amount = to_decimal_money(base_amount)

        multiplier = Decimal("1.00")

        if add_region_20:
            multiplier += Decimal("0.20")

        if add_experience_30:
            multiplier += Decimal("0.30")

        return self._round_money(base_amount * multiplier)

    def get_amount_for_date(self, payment_rule, target_date):
        base_amount = self.get_base_rate(payment_rule.letter, target_date)
        return self.apply_coefficients(
            base_amount=base_amount,
            add_region_20=payment_rule.add_region_20,
            add_experience_30=payment_rule.add_experience_30,
        )

    @staticmethod
    def get_services_total(services):
        total = Decimal("0.00")
        for item in services:
            total += to_decimal_money(item.amount)
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def get_extra_decrees_total(extra_decrees):
        total = Decimal("0.00")
        for item in extra_decrees:
            total += to_decimal_money(item.amount)
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_full_total(self, services, extra_decrees):
        return self.get_services_total(services) + self.get_extra_decrees_total(extra_decrees)