# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.money_to_text import format_money


class ArchivePanel(QWidget):
    """Список ранее созданных постановлений текущего пользователя.

    - Клик по записи → сигнал record_selected(id): поля слева заполняются.
    - Кнопка «Загрузить по делу\nновые данные» → сигнал record_chosen(id): обновление дела из БД
      и возврат к предпросмотру.
    - Раскрытие записи показывает услуги адвоката и доп. постановления.
    """

    record_selected = pyqtSignal(int)
    record_chosen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        title = QLabel("АРХИВ ПОСТАНОВЛЕНИЙ")
        title.setStyleSheet(
            "color: #1e3a5f; font-weight: bold; font-size: 13px; "
            "letter-spacing: 0.5px;"
        )

        self.choose_btn = QPushButton("Загрузить по делу\nновые данные")
        self.choose_btn.setMinimumWidth(120)
        self.choose_btn.clicked.connect(self._on_choose)

        top_row = QHBoxLayout()
        top_row.addWidget(title)
        top_row.addStretch(1)
        top_row.addWidget(self.choose_btn)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels([
            "Дата", "№ дела", "Адвокат", "Обвиняемый", "Сумма услуг", "Автор",
        ])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.itemClicked.connect(self._on_item_clicked)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                border: 1px solid #9aafc0;
                color: #1c2b3a;
            }
            QTreeWidget::item {
                padding: 3px 4px;
            }
            QTreeWidget::item:selected {
                background-color: #c8daea;
                color: #1c2b3a;
            }
            QHeaderView::section {
                background-color: #d4dfe8;
                border: none;
                border-right: 1px solid #9aafc0;
                border-bottom: 2px solid #8fa3b8;
                padding: 4px 6px;
                font-weight: bold;
                color: #1e3a5f;
            }
        """)

        self.empty_label = QLabel("Постановлений пока нет.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #7a8fa0; padding: 24px;")
        self.empty_label.setVisible(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)
        root.addLayout(top_row)
        root.addWidget(self.tree, 1)
        root.addWidget(self.empty_label)

    # ─── Наполнение ─────────────────────────────────────────────────────

    def set_records(self, records):
        self.tree.clear()

        has_records = bool(records)
        self.tree.setVisible(has_records)
        self.empty_label.setVisible(not has_records)
        self.choose_btn.setEnabled(has_records)

        for rec in records or []:
            created = rec.get("created_at")
            created_str = created.strftime("%d.%m.%Y %H:%M") if created else ""

            total = rec.get("services_total")
            total_str = format_money(total) if total is not None else ""

            item = QTreeWidgetItem([
                created_str,
                rec.get("case_number") or "",
                rec.get("lawyer_fio") or "",
                rec.get("defendant_fio") or "",
                total_str,
                rec.get("username") or "",
            ])
            item.setData(0, Qt.UserRole, int(rec["id"]))

            # ── Дочерние строки: услуги ──
            services = rec.get("services") or []
            if services:
                svc_header = QTreeWidgetItem(["Услуги адвоката:"])
                svc_header.setFirstColumnSpanned(True)
                svc_header.setFlags(Qt.ItemIsEnabled)
                item.addChild(svc_header)

                for s in services:
                    d = s.get("date")
                    d_str = d.strftime("%d.%m.%Y") if d else ""
                    amount = s.get("amount")
                    a_str = format_money(amount) if amount is not None else ""
                    child = QTreeWidgetItem([
                        d_str, "", s.get("name") or "", "", a_str,
                    ])
                    child.setFlags(Qt.ItemIsEnabled)
                    item.addChild(child)

            # ── Дочерние строки: доп. постановления ──
            extras = rec.get("extras") or []
            if extras:
                ext_header = QTreeWidgetItem(["Дополнительные постановления:"])
                ext_header.setFirstColumnSpanned(True)
                ext_header.setFlags(Qt.ItemIsEnabled)
                item.addChild(ext_header)

                for x in extras:
                    d = x.get("date")
                    d_str = d.strftime("%d.%m.%Y") if d else ""
                    amount = x.get("amount")
                    a_str = format_money(amount) if amount is not None else ""
                    child = QTreeWidgetItem([
                        d_str, "", x.get("source") or "", "", a_str,
                    ])
                    child.setFlags(Qt.ItemIsEnabled)
                    item.addChild(child)

            self.tree.addTopLevelItem(item)

    # ─── Обработчики ────────────────────────────────────────────────────

    @staticmethod
    def _top_level_of(item):
        while item is not None and item.parent() is not None:
            item = item.parent()
        return item

    def _on_item_clicked(self, item, _column):
        top = self._top_level_of(item)
        if top is None:
            return
        decree_id = top.data(0, Qt.UserRole)
        if decree_id is not None:
            self.record_selected.emit(int(decree_id))

    def _on_choose(self):
        top = self._top_level_of(self.tree.currentItem())
        if top is None:
            return
        decree_id = top.data(0, Qt.UserRole)
        if decree_id is not None:
            self.record_chosen.emit(int(decree_id))
