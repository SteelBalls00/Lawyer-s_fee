# -*- coding: utf-8 -*-

import html
import re


class TagResolver(object):
    TAG_RE = re.compile(r"\{([^{}]+)\}", re.UNICODE)

    CASES = set(["ип", "рп", "дп", "вп", "тп", "пп"])

    BOLD_WORDS = set(["bold", "жирный", "жирн"])

    SPECIAL_TAGS = set([
        "родился пол",
    ])

    HIGHLIGHT_CLASSES = ("hl-a", "hl-b", "hl-c", "hl-d")

    def __init__(self, morphology_service):
        self.morphology = morphology_service

    def render(self, template_text, context):
        previous = None
        current = template_text or ""

        for _ in range(8):
            if previous == current:
                break

            previous = current
            current = self.TAG_RE.sub(
                lambda match: self._replace_tag(match, context),
                current,
            )

        return current

    def render_html(self, template_text, context, depth=0):
        if template_text is None:
            return ""

        text = str(template_text)

        if depth > 8:
            return self._plain_to_html(text)

        parts = []
        position = 0

        for match in self.TAG_RE.finditer(text):
            parts.append(self._plain_to_html(text[position:match.start()]))

            raw_tag = match.group(1).strip()
            resolved = self.resolve_tag(raw_tag, context)

            # Неизвестный тег оставляем видимым
            if resolved == "{" + raw_tag + "}":
                parts.append(self._unknown_tag_html(raw_tag))
            else:
                resolved_text = "" if resolved is None else str(resolved)

                if resolved_text:
                    if "{" in resolved_text and "}" in resolved_text:
                        rendered_value = self.render_html(
                            resolved_text,
                            context,
                            depth=depth + 1,
                        )
                    else:
                        rendered_value = self._plain_to_html(resolved_text)

                    parsed = self._parse_tag(raw_tag)
                    css_class = self._css_class_for_tag(raw_tag)

                    if parsed.get("bold"):
                        rendered_value = "<b>{0}</b>".format(rendered_value)

                    parts.append(
                        '<span class="tag-value {0}" title="{1}">{2}</span>'.format(
                            css_class,
                            html.escape(raw_tag, quote=True),
                            rendered_value,
                        )
                    )

            position = match.end()

        parts.append(self._plain_to_html(text[position:]))

        return "".join(parts)

    def is_known_tag(self, raw_tag, context):
        raw_tag = (raw_tag or "").strip()
        low = raw_tag.lower()

        if low in self.SPECIAL_TAGS:
            return True

        parsed = self._parse_tag(raw_tag)
        return parsed["base_key"] in context

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

        if base_key not in context:
            return "{" + raw_tag + "}"

        value = context.get(base_key, "")

        if value is None:
            value = ""

        value = str(value)

        if case_short:
            if base_key in (
                "подсудимый",
                "адвокат",
                "фио адвоката",
                "судья",
                "секретарь",
                "гос обвинитель",
                "гос. обвинитель",
                "государственный обвинитель",
            ):
                value = self.morphology.decline_fio(
                    value,
                    case_short,
                    initials=initials,
                )
            else:
                value = self.morphology.decline_text(value, case_short)

        elif initials:
            value = self.morphology.to_initials(value)

        return value

    def _parse_tag(self, raw_tag):
        parts = raw_tag.split()

        case_short = None
        initials = False
        bold = False

        cleaned = []

        for part in parts:
            low = part.lower()

            if low in self.CASES:
                case_short = low
            elif low == "ио":
                initials = True
            elif low in self.BOLD_WORDS:
                bold = True
            else:
                cleaned.append(part)

        base_key = " ".join(cleaned).lower()

        return {
            "base_key": base_key,
            "case_short": case_short,
            "initials": initials,
            "bold": bold,
        }

    def render_segments(self, template_text, context, depth=0, inherited_bold=False):
        """
        Возвращает список частей текста для docx:
        [
            {"text": "обычный текст", "bold": False},
            {"text": "подставленное значение", "bold": True},
        ]

        Важно: метод рекурсивно обрабатывает вложенные теги.
        Это нужно для случаев вроде {вводная часть}, где внутри текста
        есть {судья тп ио bold}, {подсудимый тп bold} и т.д.
        """
        result = []
        text = template_text or ""

        if depth > 8:
            return [{
                "text": text,
                "bold": inherited_bold,
            }]

        position = 0

        for match in self.TAG_RE.finditer(text):
            if match.start() > position:
                result.append({
                    "text": text[position:match.start()],
                    "bold": inherited_bold,
                })

            raw_tag = match.group(1).strip()
            parsed = self._parse_tag(raw_tag)

            resolved = self.resolve_tag(raw_tag, context)

            if resolved is None:
                resolved = ""

            resolved = str(resolved)

            current_bold = inherited_bold or bool(parsed.get("bold"))

            # Если значение тега само содержит теги, обрабатываем их повторно.
            # Например {вводная часть} содержит {судья тп ио bold}.
            if "{" in resolved and "}" in resolved:
                nested_segments = self.render_segments(
                    resolved,
                    context,
                    depth=depth + 1,
                    inherited_bold=current_bold,
                )
                result.extend(nested_segments)
            else:
                result.append({
                    "text": resolved,
                    "bold": current_bold,
                })

            position = match.end()

        if position < len(text):
            result.append({
                "text": text[position:],
                "bold": inherited_bold,
            })

        return result

    def _resolve_special(self, raw_tag, context):
        low = raw_tag.lower().strip()

        if low == "родился пол":
            sex = (context.get("подсудимый пол") or "").lower()
            if "жен" in sex:
                return "родившейся"
            return "родившегося"

        return None

    def _plain_to_html(self, text):
        safe = html.escape(text or "")
        safe = safe.replace("\n", "<br/>")

        while "  " in safe:
            safe = safe.replace("  ", "&nbsp; ")

        return safe

    def _unknown_tag_html(self, raw_tag):
        safe = html.escape("{" + raw_tag + "}", quote=True)
        return (
            '<span class="tag-unknown" title="Неизвестный тег">{0}</span>'.format(
                safe
            )
        )

    def _css_class_for_tag(self, raw_tag):
        tag = (raw_tag or "").lower()

        if any(word in tag for word in (
                "номер дела",
                "дело",
                "уид",
                "дата постановления",
                "дата приговора",
        )):
            return "hl-case"

        if any(word in tag for word in (
                "подсудимый",
                "осуждение",
                "родился",
                "дата рождения",
                "уроженец",
                "основная статья",
        )):
            return "hl-defendant"

        if any(word in tag for word in (
                "адвокат",
                "фио адвоката",
                "наименование получателя",
                "инн",
                "кпп",
                "счет",
                "счёт",
                "банк",
                "бик",
        )):
            return "hl-lawyer"

        if any(word in tag for word in (
                "вознаграждение",
                "сумма",
                "рублей",
                "копеек",
                "заявлено",
                "взыскания",
        )):
            return "hl-money"

        if any(word in tag for word in (
                "заседания",
                "услуги",
                "дополнительные постановления",
                "взыскание",
                "освободить",
                "под стражей",
        )):
            return "hl-block"

        return "hl-other"