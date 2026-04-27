# -*- coding: utf-8 -*-

from collections import defaultdict


MONTHS_GENITIVE = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def format_date(value):
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


def format_russian_date(value):
    if value is None:
        return ""

    month_name = MONTHS_GENITIVE.get(value.month, "")
    return "{0} {1} {2} года".format(
        value.day,
        month_name,
        value.year,
    )


def group_dates_by_month_year(dates):
    cleaned_dates = [item for item in dates if item is not None]
    cleaned_dates.sort()

    if not cleaned_dates:
        return ""

    grouped = defaultdict(list)

    for item in cleaned_dates:
        grouped[(item.year, item.month)].append(item.day)

    parts = []

    for year, month in sorted(grouped.keys()):
        days = grouped[(year, month)]
        days_text = ", ".join("{0:02d}".format(day) for day in days)
        month_name = MONTHS_GENITIVE.get(month, "")
        parts.append("{0} {1} {2} года".format(days_text, month_name, year))

    return ", ".join(parts)


def format_russian_dates_list(dates):
    cleaned_dates = [item for item in dates if item is not None]
    cleaned_dates.sort()

    return ", ".join(format_russian_date(item) for item in cleaned_dates)