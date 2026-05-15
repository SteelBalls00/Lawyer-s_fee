# -*- coding: utf-8 -*-
# pyinstaller --onedir --noconsole --name AdvokatOplata --clean --add-data "config.ini;." --add-data "payment_to_lawyers.txt;." --add-data "template_01.docx;." --add-data ".venv\Lib\site-packages\pymorphy2_dicts_ru\data;pymorphy2_dicts_ru\data" --hidden-import=pymorphy2_dicts_ru --hidden-import=pymorphy2 --hidden-import=fdb --hidden-import=docx main.py
# pyinstaller --onedir --noconsole --name AdvokatOplata --clean --add-data "lawyer_fee.ico;." --icon=lawyer_fee.ico --add-data "config.ini;." --add-data "payment_to_lawyers.txt;." --add-data "template_01.docx;." --add-data "resources;resources" --add-data ".venv\Lib\site-packages\pymorphy2_dicts_ru\data;pymorphy2_dicts_ru\data" --hidden-import=pymorphy2_dicts_ru --hidden-import=pymorphy2 --hidden-import=fdb --hidden-import=docx main.py

import os
import sys

from PyQt5.QtWidgets import QApplication

from app.state import AppState
from app.db.firebird_client import FirebirdClient
from app.db.repositories import CaseRepository
from app.controllers.case_controller import CaseController
from app.controllers.save_controller import SaveController

from app.services.payment_rates import PaymentRates
from app.services.payment_calculator import PaymentCalculator
from app.services.context_builder import ContextBuilder
from app.services.morphology import MorphologyService
from app.services.tag_resolver import TagResolver
from app.services.preview_renderer import PreviewRenderer
from app.services.docx_renderer import DocxRenderer
from app.services.declension_word_cache import DeclensionWordCache
from app.services.user_settings import UserSettings

from app.ui.main_window import MainWindow


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_dir, "config.ini")
    rates_path = os.path.join(base_dir, "payment_to_lawyers.txt")
    template_path = os.path.join(base_dir, "template_01.docx")
    declensions_path = os.path.join(base_dir, "declensions.ini")
    settings_path = os.path.join(base_dir, "settings.ini")

    app = QApplication(sys.argv)

    state = AppState()

    db_client = FirebirdClient(config_path)
    repository = CaseRepository(db_client)
    case_controller = CaseController(state, repository)

    payment_rates = PaymentRates(rates_path)
    payment_calculator = PaymentCalculator(payment_rates)

    morphology_service = MorphologyService()
    context_builder = ContextBuilder(payment_calculator)
    tag_resolver = TagResolver(morphology_service)

    user_settings = UserSettings(settings_path)
    declension_cache = DeclensionWordCache(
        declensions_path,
        network_path=user_settings.get_network_declensions_path(),
    )
    # Подтянуть свежие склонения из сетевого файла при старте
    declension_cache.sync_from_network()
    morphology_service.word_cache = declension_cache

    preview_renderer = PreviewRenderer(
        context_builder=context_builder,
        tag_resolver=tag_resolver,
        template_path=template_path,
    )

    docx_renderer = DocxRenderer(
        context_builder=context_builder,
        tag_resolver=tag_resolver,
    )

    save_controller = SaveController(
        state=state,
        docx_renderer=docx_renderer,
        template_path=template_path,
    )

    window = MainWindow(
        state=state,
        case_controller=case_controller,
        payment_calculator=payment_calculator,
        preview_renderer=preview_renderer,
        save_controller=save_controller,
        declension_cache=declension_cache,
        user_settings=user_settings,
    )
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()