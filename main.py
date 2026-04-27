# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtWidgets import QApplication

from app.state import AppState
from app.db.firebird_client import FirebirdClient
from app.db.repositories import CaseRepository
from app.controllers.case_controller import CaseController
from app.services.payment_rates import PaymentRates
from app.services.payment_calculator import PaymentCalculator
from app.ui.main_window import MainWindow


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.ini")
    rates_path = os.path.join(base_dir, "payment_to_lawyers.txt")

    app = QApplication(sys.argv)

    state = AppState()
    db_client = FirebirdClient(config_path)
    repository = CaseRepository(db_client)
    case_controller = CaseController(state, repository)

    payment_rates = PaymentRates(rates_path)
    payment_calculator = PaymentCalculator(payment_rates)

    window = MainWindow(
        state=state,
        case_controller=case_controller,
        payment_calculator=payment_calculator,
    )
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()