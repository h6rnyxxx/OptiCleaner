"""
OptiCleaner v4.0 - Software Uninstaller View
Discovers installed programs, launches uninstallers, and hunts leftover remnants.
"""

import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui
from src.modules.uninstaller.app_scanner import AppScanner
from src.modules.uninstaller.remnant_hunter import RemnantHunter


class UninstallerView(QtWidgets.QWidget):
    """View displaying installed applications with remnant cleaner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.apps = []
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Деинсталлятор ПО (Software Uninstaller)")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FF;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("Удаление установленных программ с автоматической зачисткой остаточных файлов в AppData и реестре.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # Controls bar
        ctrl_bar = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("🔄 Обновить список")
        self.btn_refresh.setProperty("class", "primary-btn")
        self.btn_refresh.clicked.connect(self._load_apps)
        ctrl_bar.addWidget(self.btn_refresh)

        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Поиск по названию программы...")
        self.search_box.setStyleSheet("background-color: #131927; border: 1px solid #1E293B; border-radius: 8px; padding: 8px; color: #FFFFFF;")
        self.search_box.textChanged.connect(self._filter_apps)
        ctrl_bar.addWidget(self.search_box)

        layout.addLayout(ctrl_bar)

        # Apps Table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Название программы", "Версия", "Издатель", "Размер (MB)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom Action Bar
        bot_bar = QtWidgets.QHBoxLayout()
        self.btn_uninstall = QtWidgets.QPushButton("🗑 Деинсталлировать выбранное")
        self.btn_uninstall.setProperty("class", "danger-btn")
        self.btn_uninstall.clicked.connect(self._uninstall_selected)
        bot_bar.addWidget(self.btn_uninstall)

        self.btn_remnants = QtWidgets.QPushButton("🔎 Найти хвосты (Remnant Hunter)")
        self.btn_remnants.setProperty("class", "primary-btn")
        self.btn_remnants.clicked.connect(self._hunt_remnants)
        bot_bar.addWidget(self.btn_remnants)

        bot_bar.addStretch()
        layout.addLayout(bot_bar)

        self.status_lbl = QtWidgets.QLabel("Нажмите «Обновить список» для загрузки программ")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(self.status_lbl)

    def _load_apps(self):
        self.status_lbl.setText("Сканирование установленного софта...")
        self.apps = AppScanner.get_installed_apps()
        self._render_table(self.apps)
        self.status_lbl.setText(f"Найдено программ: {len(self.apps)}")

    def _render_table(self, app_list):
        self.table.setRowCount(0)
        for row, a in enumerate(app_list):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(a["name"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(a.get("version", "")))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(a.get("publisher", "")))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(a.get("size_mb", 0))))

    def _filter_apps(self, text):
        query = text.lower().strip()
        filtered = [a for a in self.apps if query in a["name"].lower()]
        self._render_table(filtered)

    def _uninstall_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        name = self.table.item(row, 0).text()
        for a in self.apps:
            if a["name"] == name:
                uninst = a.get("uninstall_string", "")
                if uninst:
                    subprocess.Popen(uninst, shell=True)
                    self.status_lbl.setText(f"Запущен деинсталлятор для: {name}")
                break

    def _hunt_remnants(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        name = self.table.item(row, 0).text()
        remnants = RemnantHunter.scan_remnants_for_app(name)
        if remnants:
            cnt = len(remnants)
            self.status_lbl.setText(f"Обнаружено {cnt} остаточных директорий для {name}")
        else:
            self.status_lbl.setText(f"Остаточных хвостов для {name} не обнаружено (чисто)")
