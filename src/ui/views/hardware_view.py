"""
OptiCleaner v4.0 - Hardware & Telemetry View
Interactive live performance dashboard with native QPainter neon HUD gauges.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from src.ui.components.native_cyber_hud import CyberGauge
from src.modules.hardware.telemetry_worker import TelemetryWorker


class HardwareView(QtWidgets.QWidget):
    """View rendering real-time CPU, RAM, and Disk telemetry gauges."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Мониторинг Системы (Hardware Telemetry)")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FF;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("Нативный аппаратный телеметрический мониторинг в реальном времени с нулевым оверхедом.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # Neon Gauges Row
        gauges_frame = QtWidgets.QFrame()
        gauges_frame.setStyleSheet("background-color: #131927; border: 1px solid #1E293B; border-radius: 12px; padding: 20px;")
        g_layout = QtWidgets.QHBoxLayout(gauges_frame)
        g_layout.setSpacing(32)

        self.gauge_cpu = CyberGauge("CPU LOAD", "%", "#00E5FF")
        self.gauge_ram = CyberGauge("RAM USAGE", "%", "#A855F7")
        self.gauge_disk = CyberGauge("DISK C:", "%", "#38BDF8")

        g_layout.addStretch()
        g_layout.addWidget(self.gauge_cpu)
        g_layout.addWidget(self.gauge_ram)
        g_layout.addWidget(self.gauge_disk)
        g_layout.addStretch()

        layout.addWidget(gauges_frame)

        # Detailed Specs List
        specs_box = QtWidgets.QGroupBox("Спецификации Оборудования")
        specs_box.setStyleSheet("QGroupBox { color: #E2E8F0; font-weight: 700; border: 1px solid #1E293B; border-radius: 8px; margin-top: 10px; padding-top: 16px; }")
        s_layout = QtWidgets.QVBoxLayout(specs_box)

        self.lbl_cpu_detail = QtWidgets.QLabel("Процессор: Сбор данных...")
        self.lbl_cpu_detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        s_layout.addWidget(self.lbl_cpu_detail)

        self.lbl_ram_detail = QtWidgets.QLabel("Оперативная память: Сбор данных...")
        self.lbl_ram_detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        s_layout.addWidget(self.lbl_ram_detail)

        self.lbl_disk_detail = QtWidgets.QLabel("Накопитель C: Сбор данных...")
        self.lbl_disk_detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        s_layout.addWidget(self.lbl_disk_detail)

        layout.addWidget(specs_box)
        layout.addStretch()

    def _init_timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_metrics)
        self.timer.start(1000)
        self._update_metrics()

    def _update_metrics(self):
        try:
            data = TelemetryWorker.get_snapshot()
            self.gauge_cpu.set_value(data["cpu_percent"])
            self.gauge_ram.set_value(data["ram_percent"])
            self.gauge_disk.set_value(data["disk_percent"])

            self.lbl_cpu_detail.setText(f"Процессор: Загрузка {data['cpu_percent']}% ({data['cpu_count']} логических ядер)")
            self.lbl_ram_detail.setText(f"Оперативная память: Использовано {data['ram_used_gb']} GB из {data['ram_total_gb']} GB ({data['ram_percent']}%)")
            self.lbl_disk_detail.setText(f"Диск C: Свободно {data['disk_free_gb']} GB ({100 - data['disk_percent']}% свободно)")
        except Exception:
            pass
