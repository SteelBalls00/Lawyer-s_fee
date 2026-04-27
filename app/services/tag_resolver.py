# -*- coding: utf-8 -*-

import re


class TagResolver(object):
    TAG_RE = re.compile(r"\{([^{}]+)\}", re.UNICODE)

    CASES = set(["ип", "рп", "дп", "вп", "тп", "пп"])

    def __init__(self, morphology_service):
        self.morphology = morphology_service

    def render(self, template_text, context):
        previous = None
        current = template_text or ""

        # Несколько проходов нужны потому, что некоторые сгенерированные блоки
        # сами содержат теги, например {подсудимый рп ио}.
        for _ in range(5):
            if previous == current:
                break

            previous = current
            current = self.TAG_RE.sub(
                lambda match: self._replace_tag(match, context),
                current,
            )

        return current

    def _replace_tag(self, match, context):
        raw_tag = match.group(1).strip()
        return self.resolve_tag(raw_tag, context)

    def resolve_tag(self, raw_tag, context):
        raw_tag = (raw_tag or "").strip()

        if not raw_tag:
            return ""

        special = self._resolve_special(raw_tag, context)
        if special is not None:
            return special

        parsed = self._parse_tag(raw_tag)
        base_key = parsed["base_key"]
        case_short = parsed["case_short"]
        initials = parsed["initials"]

        value = context.get(base_key, "")

        if value is None:
            value = ""

        value = str(value)

        if case_short:
            if base_key in ("подсудимый", "адвокат", "судья", "секретарь", "гос обвинитель", "государственный обвинитель"):
                value = self.morphology.decline_fio(value, case_short, initials=initials)
            else:
                value = self.morphology.decline_text(value, case_short)

        elif initials:
            value = self.morphology.to_initials(value)

        return value

    def _parse_tag(self, raw_tag):
        parts = raw_tag.split()

        case_short = None
        initials = False

        cleaned = []

        for part in parts:
            low = part.lower()

            if low in self.CASES:
                case_short = low
            elif low == "ио":
                initials = True
            else:
                cleaned.append(part)

        base_key = " ".join(cleaned).lower()

        return {
            "base_key": base_key,
            "case_short": case_short,
            "initials": initials,
        }

    def _resolve_special(self, raw_tag, context):
        low = raw_tag.lower().strip()

        if low == "родился пол":
            sex = (context.get("подсудимый пол") or "").lower()
            if "жен" in sex:
                return "родившейся"
            return "родившегося"

        return None