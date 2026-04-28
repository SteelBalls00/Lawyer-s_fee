# -*- coding: utf-8 -*-

import re


class SaveController(object):
    def __init__(self, state, docx_renderer, template_path):
        self.state = state
        self.docx_renderer = docx_renderer
        self.template_path = template_path

    def save_to_docx(self, output_path):
        output_path = output_path or ""

        if not output_path:
            raise ValueError("Не указан путь для сохранения документа")

        if not output_path.lower().endswith(".docx"):
            output_path += ".docx"

        return self.docx_renderer.render_to_file(
            template_path=self.template_path,
            output_path=output_path,
            state=self.state,
        )

    def get_default_file_name(self):
        case_number = self.state.case_number.value or "без номера"

        defendant = self.state.selected_defendant
        lawyer = self.state.selected_lawyer

        defendant_text = defendant.fio if defendant else "без подсудимого"
        lawyer_text = lawyer.fio if lawyer else "без адвоката"

        name = "Постановление оплата адвоката {0} {1} {2}.docx".format(
            case_number,
            defendant_text,
            lawyer_text,
        )

        return self._sanitize_file_name(name)

    def get_template_tags(self):
        return self.docx_renderer.get_template_tags(self.template_path)

    def get_unknown_template_tags(self):
        return self.docx_renderer.get_unknown_tags_in_template(
            template_path=self.template_path,
            state=self.state,
        )

    def get_last_unknown_tags(self):
        return list(self.docx_renderer.last_unknown_tags)

    def get_last_unresolved_tags(self):
        return list(self.docx_renderer.last_unresolved_tags)

    @staticmethod
    def _sanitize_file_name(value):
        value = value or "Постановление.docx"

        value = re.sub(r'[\\/:*?"<>|]+', " ", value)
        value = re.sub(r"\s+", " ", value)
        value = value.strip()

        if not value.lower().endswith(".docx"):
            value += ".docx"

        return value