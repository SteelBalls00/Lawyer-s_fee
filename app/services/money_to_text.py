# -*- coding: utf-8 -*-


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

UNITS_FEMALE = [
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


def _three_digits_to_words(number, gender="male"):
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
                words.append(UNITS_FEMALE[units])
            else:
                words.append(UNITS_MALE[units])

    return words


def number_to_words(number):
    number = int(number)

    if number == 0:
        return "ноль"

    if number < 0:
        return "минус " + number_to_words(abs(number))

    parts = []

    millions = number // 1000000
    thousands = (number // 1000) % 1000
    rest = number % 1000

    if millions:
        parts.extend(_three_digits_to_words(millions, "male"))
        parts.append(choose_plural(millions, ["миллион", "миллиона", "миллионов"]))

    if thousands:
        parts.extend(_three_digits_to_words(thousands, "female"))
        parts.append(choose_plural(thousands, ["тысяча", "тысячи", "тысяч"]))

    if rest:
        parts.extend(_three_digits_to_words(rest, "male"))

    return " ".join(parts)


def money_to_text(amount):
    amount = int(amount or 0)

    rubles_word = choose_plural(amount, ["рубль", "рубля", "рублей"])
    return "{0} {1} 00 копеек".format(
        number_to_words(amount),
        rubles_word,
    )