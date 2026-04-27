# -*- coding: utf-8 -*-

import re

import pymorphy2


CASE_MAP = {
    "ип": "nomn",
    "рп": "gent",
    "дп": "datv",
    "вп": "accs",
    "тп": "ablt",
    "пп": "loct",
}


class MorphologyService(object):
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    def decline_text(self, text, case_short):
        text = text or ""
        case_tag = CASE_MAP.get(case_short)

        if not case_tag:
            return text

        return self._decline_preserving_quotes(text, case_tag)

    def decline_fio(self, fio, case_short, initials=False):
        fio = (fio or "").strip()
        case_tag = CASE_MAP.get(case_short)

        if not fio:
            return ""

        if not case_tag:
            return self.to_initials(fio) if initials else fio

        parts = fio.split()
        gender = self._detect_gender(parts)

        if initials:
            return self._decline_fio_with_initials(parts, case_tag, gender)

        result_name = []

        for part in parts:
            if "." in part:
                result_name.append(part)
            else:
                result_name.append(self._decline_word(part, case_tag, gender))

        return " ".join(result_name)

    def to_initials(self, fio):
        fio = (fio or "").strip()
        if not fio:
            return ""

        parts = fio.split()

        if len(parts) == 1:
            return fio

        surname = parts[0]
        initials = []

        for part in parts[1:]:
            clean = part.strip()
            if not clean:
                continue

            if "." in clean:
                initials.append(clean)
            else:
                initials.append(clean[0].upper() + ".")

        return "{0} {1}".format(surname, "".join(initials))

    def _detect_gender(self, parts):
        # Сначала пытаемся определить род по отчеству,
        # потому что это самый надёжный признак.
        for part in parts:
            clean = self._clean_word(part)
            if not clean or "." in part:
                continue

            parses = self.morph.parse(clean)
            for parsed in parses:
                if "Patr" in parsed.tag:
                    if "masc" in parsed.tag:
                        return "masc"
                    if "femn" in parsed.tag:
                        return "femn"

        # Если отчества нет, пробуем определить род по имени.
        for part in parts:
            clean = self._clean_word(part)
            if not clean or "." in part:
                continue

            parses = self.morph.parse(clean)
            for parsed in parses:
                if "Name" in parsed.tag:
                    if "masc" in parsed.tag:
                        return "masc"
                    if "femn" in parsed.tag:
                        return "femn"

        return None

    def _decline_fio_with_initials(self, parts, case_tag, gender):
        if not parts:
            return ""

        surname = parts[0]
        declined_surname = self._decline_word(surname, case_tag, gender)

        if len(parts) == 1:
            return declined_surname

        initials = []
        for part in parts[1:]:
            clean = part.strip()
            if not clean:
                continue

            if "." in clean:
                initials.append(clean)
            else:
                initials.append(clean[0].upper() + ".")

        return "{0} {1}".format(declined_surname, "".join(initials))

    def _decline_preserving_quotes(self, text, case_tag):
        parts = re.split(r"(«[^»]*»|\"[^\"]*\")", text)
        result = []

        for part in parts:
            if not part:
                continue

            if part.startswith("«") or part.startswith('"'):
                result.append(part)
            else:
                result.append(self._decline_plain_text(part, case_tag))

        return "".join(result)

    def _decline_plain_text(self, text, case_tag):
        tokens = re.split(r"(\W+)", text, flags=re.UNICODE)
        result = []

        for token in tokens:
            if not token:
                continue

            if re.match(r"^[А-Яа-яЁё]+$", token, flags=re.UNICODE):
                result.append(self._decline_word(token, case_tag, gender=None))
            else:
                result.append(token)

        return "".join(result)

    def _decline_word(self, word, case_tag, gender=None):
        if not word:
            return word

        clean_word = self._clean_word(word)
        if not clean_word:
            return word

        parses = self.morph.parse(clean_word)

        parsed = parses[0]

        if gender:
            for item in parses:
                if gender in item.tag:
                    parsed = item
                    break

        if gender:
            inflected = parsed.inflect({case_tag, gender})
            if inflected is None:
                inflected = parsed.inflect({case_tag})
        else:
            inflected = parsed.inflect({case_tag})

        if inflected is None:
            return word

        result = inflected.word

        if word[:1].isupper():
            result = result[:1].upper() + result[1:]

        return result

    @staticmethod
    def _clean_word(value):
        return re.sub(r"[^А-Яа-яЁё-]", "", value or "", flags=re.UNICODE)