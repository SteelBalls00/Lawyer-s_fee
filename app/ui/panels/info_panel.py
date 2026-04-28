# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.blocks.case_search_block import CaseSearchBlock
from app.ui.blocks.case_info_block import CaseInfoBlock
from app.ui.blocks.defendant_block import DefendantBlock
from app.ui.blocks.intro_block import IntroBlock
from app.ui.blocks.lawyer_block import LawyerBlock
from app.ui.blocks.payment_rule_block import PaymentRuleBlock
from app.ui.blocks.services_block import ServicesBlock
from app.ui.blocks.extra_decrees_block import ExtraDecreesBlock
from app.ui.blocks.total_block import TotalBlock


class InfoPanel(QWidget):
    data_changed = pyqtSignal()
    status_message = pyqtSignal(str)

    def __init__(self, state, case_controller, payment_calculator, parent=None):
        super().__init__(parent)

        self.state = state
        self.case_controller = case_controller
        self.payment_calculator = payment_calculator

        self._build_ui()
        self._connect_signals()
        self.refresh_from_state()

    def _build_ui(self):
        self.case_search_block = CaseSearchBlock()
        self.case_info_block = CaseInfoBlock()
        self.intro_block = IntroBlock()
        self.defendant_block = DefendantBlock()
        self.lawyer_block = LawyerBlock()
        self.payment_rule_block = PaymentRuleBlock(payment_calculator=self.payment_calculator,)
        self.services_block = ServicesBlock(
            state=self.state,
            payment_calculator=self.payment_calculator,
        )
        self.extra_decrees_block = ExtraDecreesBlock()
        self.total_block = TotalBlock(payment_calculator=self.payment_calculator)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.case_search_block)
        content_layout.addWidget(self.case_info_block)
        content_layout.addWidget(self.intro_block)
        content_layout.addWidget(self.defendant_block)
        content_layout.addWidget(self.lawyer_block)
        content_layout.addWidget(self.payment_rule_block)
        content_layout.addWidget(self.services_block)
        content_layout.addWidget(self.extra_decrees_block)
        content_layout.addWidget(self.total_block)
        content_layout.addStretch(1)
        content_widget.setLayout(content_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)

        root = QVBoxLayout()
        root.addWidget(scroll)

        self.setLayout(root)

    def _connect_signals(self):
        self.case_search_block.search_requested.connect(self._on_search_requested)

        self.case_info_block.data_changed.connect(self._on_common_data_changed)
        self.intro_block.data_changed.connect(self._on_common_data_changed)
        self.defendant_block.data_changed.connect(self._on_common_data_changed)
        self.lawyer_block.data_changed.connect(self._on_common_data_changed)

        self.payment_rule_block.data_changed.connect(self._on_payment_rule_changed)
        self.services_block.data_changed.connect(self._on_services_changed)
        self.extra_decrees_block.data_changed.connect(self._on_extra_decrees_changed)

    def _on_search_requested(self, case_number: str):
        if not case_number:
            QMessageBox.warning(self, "Предупреждение", "Введите номер дела.")
            return

        try:
            found = self.case_controller.load_case(case_number)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось загрузить данные по делу:\n{0}".format(str(exc))
            )
            self.status_message.emit("Ошибка загрузки дела")
            return

        if not found:
            QMessageBox.information(
                self,
                "Поиск",
                "Дело с указанным номером не найдено."
            )
            self.status_message.emit("Дело не найдено")
            return

        self.refresh_from_state()
        self.data_changed.emit()
        self.status_message.emit("Данные по делу загружены")

    def _on_common_data_changed(self):
        self.save_to_state()
        self.total_block.load_from_state(self.state)
        self.data_changed.emit()

    def _on_services_changed(self):
        self.services_block.save_to_state(self.state)

        # После изменения услуг может измениться последняя дата,
        # значит надо обновить суммы в комбобоксе подпункта.
        self.payment_rule_block.load_from_state(self.state)

        self.total_block.load_from_state(self.state)
        self.data_changed.emit()

    def _on_extra_decrees_changed(self):
        self.extra_decrees_block.save_to_state(self.state)
        self.total_block.load_from_state(self.state)
        self.data_changed.emit()

    def _on_payment_rule_changed(self):
        self.payment_rule_block.save_to_state(self.state)
        self.services_block.recalculate_all_amounts()
        self.services_block.save_to_state(self.state)
        self.total_block.load_from_state(self.state)
        self.data_changed.emit()

    def refresh_from_state(self):
        self.case_search_block.set_case_number(self.state.case_number.value)
        self.case_info_block.load_from_state(self.state)
        self.intro_block.load_from_state(self.state)
        self.defendant_block.load_from_state(self.state)
        self.lawyer_block.load_from_state(self.state)
        self.payment_rule_block.load_from_state(self.state)
        self.services_block.load_from_state(self.state)
        self.extra_decrees_block.load_from_state(self.state)
        self.total_block.load_from_state(self.state)

    def save_to_state(self):
        self.case_info_block.save_to_state(self.state)
        self.intro_block.save_to_state(self.state)
        self.defendant_block.save_to_state(self.state)
        self.lawyer_block.save_to_state(self.state)
        self.payment_rule_block.save_to_state(self.state)
        self.services_block.save_to_state(self.state)
        self.extra_decrees_block.save_to_state(self.state)