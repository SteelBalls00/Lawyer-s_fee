# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class TeamSettingsDialog(QDialog):
    """Настройка составов (связок судья↔помощник). Доступно администраторам.

    Все участники одного состава видят в архиве постановления друг друга.
    Состав создаётся автоматически при добавлении в него первого участника
    и исчезает, когда удалён последний.
    """

    def __init__(self, team_service, main_db=None, parent=None):
        super().__init__(parent)
        self.team_service = team_service
        self.main_db = main_db

        self.setWindowTitle("Настройка составов")
        self.setModal(True)
        self.setMinimumSize(520, 420)

        self._build_ui()
        self._load_usernames()
        self._reload_teams()

    # ─── UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        info = QLabel(
            "Участники одного состава видят в архиве постановления друг друга. "
            "Чтобы создать новый состав — введите его название и добавьте участника."
        )
        info.setWordWrap(True)

        self.team_combo = QComboBox()
        self.team_combo.setEditable(True)
        self.team_combo.currentTextChanged.connect(self._refresh_members)

        team_row = QHBoxLayout()
        team_row.addWidget(QLabel("Состав:"))
        team_row.addWidget(self.team_combo, 1)

        self.members_list = QListWidget()

        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
        self.user_combo.setInsertPolicy(QComboBox.NoInsert)

        add_btn = QPushButton("Добавить в состав")
        add_btn.clicked.connect(self._on_add)

        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Пользователь:"))
        add_row.addWidget(self.user_combo, 1)
        add_row.addWidget(add_btn)

        remove_btn = QPushButton("Удалить выбранного из состава")
        remove_btn.clicked.connect(self._on_remove)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(remove_btn)
        bottom_row.addStretch(1)
        bottom_row.addWidget(close_btn)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 12, 16, 12)
        root.addWidget(info)
        root.addLayout(team_row)
        root.addWidget(self.members_list, 1)
        root.addLayout(add_row)
        root.addLayout(bottom_row)

    # ─── Данные ─────────────────────────────────────────────────────────

    def _load_usernames(self):
        """Заполняет список пользователей из GROUPCONTENT основной БД."""
        if self.main_db is None:
            return
        try:
            rows = self.main_db.fetch_all(
                "SELECT FIRST 1000 DISTINCT USERNAME FROM GROUPCONTENT "
                "WHERE USERNAME IS NOT NULL AND USERNAME <> '' "
                "ORDER BY USERNAME"
            )
        except Exception:
            return

        names = [(row[0] or "").strip() for row in rows if (row[0] or "").strip()]
        self.user_combo.addItems(names)

        completer = QCompleter(names, self.user_combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.user_combo.setCompleter(completer)
        self.user_combo.setCurrentText("")

    def _reload_teams(self, select_team=None):
        try:
            self._teams = self.team_service.list_teams()
        except Exception as exc:
            QMessageBox.critical(
                self, "Составы",
                "Не удалось загрузить составы:\n{0}".format(exc),
            )
            self._teams = {}

        current = select_team or self.team_combo.currentText().strip()

        self.team_combo.blockSignals(True)
        self.team_combo.clear()
        self.team_combo.addItems(sorted(self._teams.keys()))
        if current:
            self.team_combo.setCurrentText(current)
        self.team_combo.blockSignals(False)

        self._refresh_members()

    def _refresh_members(self, *_):
        team = self.team_combo.currentText().strip()
        self.members_list.clear()
        for user in self._teams.get(team, []):
            self.members_list.addItem(user)

    # ─── Действия ───────────────────────────────────────────────────────

    def _on_add(self):
        team = self.team_combo.currentText().strip()
        user = self.user_combo.currentText().strip()

        if not team:
            QMessageBox.warning(self, "Составы", "Введите название состава.")
            return
        if not user:
            QMessageBox.warning(self, "Составы", "Выберите пользователя.")
            return

        try:
            self.team_service.add_member(team, user)
        except Exception as exc:
            QMessageBox.critical(
                self, "Составы",
                "Не удалось добавить участника:\n{0}".format(exc),
            )
            return

        self.user_combo.setCurrentText("")
        self._reload_teams(select_team=team)

    def _on_remove(self):
        team = self.team_combo.currentText().strip()
        item = self.members_list.currentItem()
        if not team or item is None:
            return

        user = item.text()
        answer = QMessageBox.question(
            self, "Составы",
            "Удалить «{0}» из состава «{1}»?".format(user, team),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.team_service.remove_member(team, user)
        except Exception as exc:
            QMessageBox.critical(
                self, "Составы",
                "Не удалось удалить участника:\n{0}".format(exc),
            )
            return

        self._reload_teams(select_team=team)
