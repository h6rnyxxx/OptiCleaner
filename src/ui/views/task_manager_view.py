"""
OptiCleaner v4.0 - Task Manager View
Interactive process manager for inspecting resource hogs and killing tasks.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from src.modules.task_manager.process_monitor import ProcessMonitor


class TaskManagerView(QtWidgets.QWidget):
    """View rendering active processes with CPU and RAM indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Диспетчер Задач (Task Manager)")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FF;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("Анализ ресурсоёмких процессов в реальном времени и оптимизация системных приоритетов.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # Top Bar
        top_bar = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("🔄 Обновить сейчас")
        self.btn_refresh.setProperty("class", "primary-btn")
        self.btn_refresh.clicked.connect(self._refresh_processes)
        top_bar.addWidget(self.btn_refresh)

        self.btn_kill = QtWidgets.QPushButton("⛔ Завершить процесс")
        self.btn_kill.setProperty("class", "danger-btn")
        self.btn_kill.clicked.connect(self._kill_selected)
        top_bar.addWidget(self.btn_kill)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["PID", "Имя процесса", "Память (MB)", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_lbl = QtWidgets.QLabel("Мониторинг активен")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(self.status_lbl)

    def _init_timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._refresh_processes)
        self.timer.start(3000)
        self._refresh_processes()

    def _refresh_processes(self):
        procs = ProcessMonitor.get_processes()[:50]  # Top 50 by RAM
        self.table.setRowCount(0)
        for row, p in enumerate(procs):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(p["pid"])))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(p["name"]))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(p["mem_mb"])))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(p["status"]))

    def _kill_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        pid = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        ok = ProcessMonitor.terminate_process(pid)
        self.status_lbl.setText(f"Процесс {name} (PID {pid}) завершён." if ok else f"Не удалось завершить PID {pid}.")
        self._refresh_processes()
