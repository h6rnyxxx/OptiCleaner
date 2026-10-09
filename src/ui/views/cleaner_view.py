"""
OptiCleaner v4.0 - Cleaner View
UI View for system audit, scanning, and reclaiming storage space.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from src.modules.cleaner.disk_scanner import DiskScanner


class CleanerView(QtWidgets.QWidget):
    """View containing Scan and Clean buttons, progress bar, and category breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = DiskScanner()
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        title = QtWidgets.QLabel("Системная Очистка (System Cleaner)")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FF;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("Интеллектуальное сканирование и удаление временных файлов, кэша браузеров и системного мусора.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # Top Control Card
        control_card = QtWidgets.QFrame()
        control_card.setProperty("class", "card")
        control_card.setStyleSheet("background-color: #131927; border-radius: 12px; padding: 16px;")
        card_layout = QtWidgets.QHBoxLayout(control_card)

        self.btn_scan = QtWidgets.QPushButton("🔍 Начать Сканирование")
        self.btn_scan.setProperty("class", "primary-btn")
        self.btn_scan.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self._run_scan)
        card_layout.addWidget(self.btn_scan)

        self.btn_clean = QtWidgets.QPushButton("🧹 Очистить Мусор")
        self.btn_clean.setProperty("class", "danger-btn")
        self.btn_clean.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self._run_clean)
        card_layout.addWidget(self.btn_clean)

        self.lbl_stats = QtWidgets.QLabel("Готов к анализу")
        self.lbl_stats.setStyleSheet("color: #E2E8F0; font-weight: 700; margin-left: 16px;")
        card_layout.addWidget(self.lbl_stats)
        card_layout.addStretch()

        layout.addWidget(control_card)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Category Table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Категория", "Файлов", "Размер"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

    def _run_scan(self):
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.lbl_stats.setText("Сканирование диска...")

        # Run scan
        res = self.scanner.scan_all()
        self.progress.setVisible(False)

        self.table.setRowCount(0)
        for row, cat in enumerate(res.get("categories", [])):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(cat["name"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(cat["files"])))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{cat['mb']} MB"))

        mb = res.get("total_mb", 0)
        files = res.get("total_files", 0)
        self.lbl_stats.setText(f"Найдено: {mb} MB в {files} файлах")
        self.btn_clean.setEnabled(files > 0)

    def _run_clean(self):
        reclaimed = 0
        for cat in ["system_temp", "windows_cache", "browser_cache"]:
            reclaimed += self.scanner.clean_category(cat)
        reclaimed_mb = round(reclaimed / (1024 * 1024), 2)
        self.lbl_stats.setText(f"Успешно освобождено: {reclaimed_mb} MB!")
        self.table.setRowCount(0)
        self.btn_clean.setEnabled(False)
