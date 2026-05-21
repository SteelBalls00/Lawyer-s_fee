# -*- coding: utf-8 -*-

import os

from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph


class PreviewRenderer(object):
    def __init__(self, context_builder, tag_resolver, template_path=None):
        self.context_builder = context_builder
        self.tag_resolver = tag_resolver
        self.template_path = template_path

    def render(self, state):
        context = self.context_builder.build(state)

        if self.template_path and os.path.exists(self.template_path):
            return self._render_template_preview(context)

        return self._render_fallback_preview(context)

    def _render_template_preview(self, context):
        document = Document(self.template_path)

        parts = [self._html_begin()]

        for block in self._iter_block_items(document):
            if isinstance(block, Paragraph):
                parts.append(self._render_paragraph(block, context))
            elif isinstance(block, Table):
                parts.append(self._render_table(block, context))

        parts.append(self._html_end())

        return "".join(parts)

    def _render_fallback_preview(self, context):
        text = "Шаблон template_01.docx не найден."
        return (
            self._html_begin()
            + '<p class="warning">{0}</p>'.format(text)
            + self._html_end()
        )

    def _render_paragraph(self, paragraph, context):
        text = self._get_paragraph_text(paragraph)

        if not text.strip():
            return '<p class="doc-paragraph empty-line">&nbsp;</p>'

        if self._is_custom_intro_placeholder(text, context):
            rendered = self.tag_resolver.render_rich_segments_html(
                context.get("__custom_intro_segments") or [],
                context,
            )
        else:
            rendered = self.tag_resolver.render_html(text, context)
        align = self._get_alignment(paragraph)

        indent_style = "text-indent:47px;" if align == "justify" else ""

        # В кабинетном режиме абзац вводной части — обычный абзац с отступом
        is_intro = (text or "").strip().lower() == "{вводная часть}"
        if is_intro and context.get("__intro_mode") == "chamber":
            indent_style = "text-indent:47px;"

        return (
            '<p class="doc-paragraph" style="text-align:{0};{1}">{2}</p>'.format(
                align,
                indent_style,
                rendered,
            )
        )

    @staticmethod
    def _is_custom_intro_placeholder(text, context):
        if not context.get("__use_custom_intro"):
            return False

        return (text or "").strip().lower() == "{вводная часть}"

    def _render_table(self, table, context):
        rows_html = []

        for row in table.rows:
            cells_html = []

            for cell in row.cells:
                cell_parts = []

                for block in self._iter_block_items(cell):
                    if isinstance(block, Paragraph):
                        text = self._get_paragraph_text(block)
                        if text.strip():
                            cell_parts.append(
                                '<div class="table-paragraph">{0}</div>'.format(
                                    self.tag_resolver.render_html(text, context)
                                )
                            )

                if not cell_parts:
                    cell_parts.append("&nbsp;")

                cells_html.append(
                    "<td>{0}</td>".format("".join(cell_parts))
                )

            rows_html.append("<tr>{0}</tr>".format("".join(cells_html)))

        return (
            '<table class="doc-table">{0}</table>'.format("".join(rows_html))
        )

    @staticmethod
    def _get_paragraph_text(paragraph):
        if paragraph.runs:
            return "".join(run.text for run in paragraph.runs)
        return paragraph.text or ""

    @staticmethod
    def _get_alignment(paragraph):
        alignment = paragraph.alignment

        if alignment == 1:
            return "center"
        if alignment == 2:
            return "right"
        if alignment == 3:
            return "justify"

        return "left"

    def _html_begin(self):
        return """
<html>
<head>
<meta charset="utf-8">
<style>
    body {
        background: #eef1f4;
        margin: 0;
        padding: 18px;
    }

    .page {
        max-width: 900px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #d7dde5;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
        padding: 52px 62px;
        color: #1f2933;
        font-family: "Times New Roman", serif;
        font-size: 14pt;
        line-height: 1.45;
    }

    .doc-paragraph {
        margin: 0 0 10pt 0;
        white-space: normal;
    }

    .empty-line {
        min-height: 14pt;
    }

    .doc-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10pt 0;
    }

    .doc-table td {
        border: 1px solid #cfd6df;
        padding: 6px 8px;
        vertical-align: top;
    }

    .table-paragraph {
        margin: 0 0 4pt 0;
    }

    .tag-value {
        padding: 0 2px;
        border-radius: 4px;
    }

    /* мягкие, не кислотные цвета */
    .hl-case {
    background: #edf3ff;
    color: #274c77;
    }
    
    .hl-defendant {
        background: #edf7f0;
        color: #2f5d50;
    }
    
    .hl-lawyer {
        background: #faf1e7;
        color: #8a5a44;
    }
    
    .hl-money {
        background: #f2eef8;
        color: #5f4b7a;
    }
    
    .hl-block {
        background: #f4f4ee;
        color: #5f5a3d;
    }
    
    .hl-other {
        background: #f1f1f1;
        color: #444444;
    }
    
    .tag-unknown {
        background: #f8e8e8;
        color: #8a3d3d;
        padding: 0 2px;
        border-radius: 4px;
    }

    .warning {
        color: #8a3d3d;
    }
</style>
</head>
<body>
<div class="page">
"""

    @staticmethod
    def _html_end():
        return """
</div>
</body>
</html>
"""

    def _iter_block_items(self, parent):
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            return

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)