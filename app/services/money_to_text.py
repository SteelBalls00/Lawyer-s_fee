# -*- coding: utf-8 -*-

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


UNITS_MALE = [
    "",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
]

UNITS_FEMALE_NOMN = [
    "",
    "одна",
    "две",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
]

UNITS_FEMALE_ACCS = [
    "",
    "одну",
    "две",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
]

TEENS = [
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
]

TENS = [
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
]

HUNDREDS = [
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
]


def to_decimal_money(value):
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if value is None:
        return Decimal("0.00")

    text = str(value).strip()
    if not text:
        return Decimal("0.00")

    text = text.replace(" ", "").replace(",", ".")

    try:
        return Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal("0.00")


def format_rubles_only(value):
    """Целая часть суммы (рубли) с разделителем тысяч, без копеек."""
    amount = to_decimal_money(value)
    rubles = int(amount)
    # Неразрывный пробел между разрядами, чтобы сумма не разрывалась по строкам
    return "{0:,}".format(rubles).replace(",", "\u00a0")


def format_money(value):
    amount = to_decimal_money(value)

    rubles = int(amount)
    kopeks = int((amount - Decimal(rubles)) * 100)

    rubles_text = "{0:,}".format(rubles).replace(",", "\u00a0")

    if kopeks:
        return "{0},{1:02d}".format(rubles_text, kopeks)

    return rubles_text


def format_money_for_edit(value):
    amount = to_decimal_money(value)
    rubles = int(amount)
    kopeks = int((amount - Decimal(rubles)) * 100)

    if kopeks:
        return "{0},{1:02d}".format(rubles, kopeks)

    return str(rubles)


def choose_plural(number, forms):
    number = abs(int(number))
    last_two = number % 100
    last = number % 10

    if 11 <= last_two <= 19:
        return forms[2]

    if last == 1:
        return forms[0]

    if 2 <= last <= 4:
        return forms[1]

    return forms[2]


def _three_digits_to_words(number, gender="male", accusative=False):
    number = int(number)
    words = []

    hundreds = number // 100
    tens_units = number % 100
    tens = tens_units // 10
    units = tens_units % 10

    if hundreds:
        words.append(HUNDREDS[hundreds])

    if 10 <= tens_units <= 19:
        words.append(TEENS[tens_units - 10])
    else:
        if tens:
            words.append(TENS[tens])

        if units:
            if gender == "female":
                if accusative:
                    words.append(UNITS_FEMALE_ACCS[units])
                else:
                    words.append(UNITS_FEMALE_NOMN[units])
            else:
                words.append(UNITS_MALE[units])

    return words


def number_to_words_accusative(number):
    number = int(number)

    if number == 0:
        return "ноль"

    if number < 0:
        return "минус " + number_to_words_accusative(abs(number))

    parts = []

    millions = number // 1000000
    thousands = (number // 1000) % 1000
    rest = number % 1000

    if millions:
        parts.extend(_three_digits_to_words(millions, "male"))
        parts.append(choose_plural(millions, ["миллион", "миллиона", "миллионов"]))

    if thousands:
        parts.extend(_three_digits_to_words(thousands, "female", accusative=True))
        parts.append(choose_plural(thousands, ["тысячу", "тысячи", "тысяч"]))

    if rest:
        parts.extend(_three_digits_to_words(rest, "male"))

    return " ".join(parts)


def money_words_only(value):
    amount = to_decimal_money(value)
    rubles = int(amount)
    return number_to_words_accusative(rubles)


def money_units_text(value):
    amount = to_decimal_money(value)

    rubles = int(amount)
    kopeks = int((amount - Decimal(rubles)) * 100)

    ruble_word = choose_plural(rubles, ["рубль", "рубля", "рублей"])
    kopek_word = choose_plural(kopeks, ["копейка", "копейки", "копеек"])

    return "{0} {1:02d} {2}".format(ruble_word, kopeks, kopek_word)


def money_full_text(value):
    return "{0} {1}".format(
        money_words_only(value),
        money_units_text(value),
    )


def money_with_words(value):
    return "{0} ({1}) {2}".format(
        format_money(value),
        money_words_only(value),
        money_units_text(value),
    )