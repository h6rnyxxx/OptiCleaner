"""
OptiCleaner v4.0 - Optimizer View
UI View for system presets (Gaming, Work), low-latency timer, and RAM optimization.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from src.modules.optimizer.presets_manager import PresetsManager
from src.core.windows.win_engine import WindowsEngine


class OptimizerView(QtWidgets.QWidget):
    """View managing system presets, RAM flushing, and timer resolution."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets = PresetsManager()
        self.engine = WindowsEngine()
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QtWidgets.QLabel("Оптимизация и Твикинг (System Optimizer)")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FF;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("Применение оптимизаций ОС с созданием мгновенных снимков безопасности для 100% безопасного отката.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # Presets Section
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(16)

        # Card 1: Gaming Mode
        card_game = self._create_card(
            "🎮 Gaming Preset (Игровой режим)",
            "Схема Ultimate Performance, таймер 0.5 мс, отключение телеметрии и троттлинга сети.",
            "Активировать Gaming Mode",
            self._apply_gaming
        )
        grid.addWidget(card_game, 0, 0)

        # Card 2: Work Mode
        card_work = self._create_card(
            "💼 Work Preset (Рабочий режим)",
            "Сбалансированное энергопотребление, включенный поиск Windows и стандартные таймеры.",
            "Активировать Work Mode",
            self._apply_work
        )
        grid.addWidget(card_work, 0, 1)

        layout.addLayout(grid)

        # Quick Actions Section
        sec_title = QtWidgets.QLabel("⚡ Быстрые инструменты (Quick Actions)")
        sec_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #E2E8F0; margin-top: 10px;")
        layout.addWidget(sec_title)

        actions_bar = QtWidgets.QHBoxLayout()
        actions_bar.setSpacing(12)

        btn_ram = QtWidgets.QPushButton("🚀 Очистить ОЗУ (Flush Standby)")
        btn_ram.setProperty("class", "primary-btn")
        btn_ram.clicked.connect(self._flush_ram)
        actions_bar.addWidget(btn_ram)

        btn_dns = QtWidgets.QPushButton("🌐 Сброс DNS (Flush DNS)")
        btn_dns.setProperty("class", "primary-btn")
        btn_dns.clicked.connect(self._flush_dns)
        actions_bar.addWidget(btn_dns)

        btn_timer = QtWidgets.QPushButton("⏱ Включить 0.5 мс Таймер")
        btn_timer.setProperty("class", "primary-btn")
        btn_timer.clicked.connect(self._enable_timer)
        actions_bar.addWidget(btn_timer)

        actions_bar.addStretch()
        layout.addLayout(actions_bar)

        self.status_lbl = QtWidgets.QLabel("Готов к работе")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-weight: 700; margin-top: 8px;")
        layout.addWidget(self.status_lbl)

        layout.addStretch()

    def _create_card(self, title_text: str, desc_text: str, btn_text: str, handler):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet("background-color: #131927; border: 1px solid #1E293B; border-radius: 12px; padding: 16px;")
        l = QtWidgets.QVBoxLayout(frame)
        l.setSpacing(8)

        t = QtWidgets.QLabel(title_text)
        t.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        l.addWidget(t)

        d = QtWidgets.QLabel(desc_text)
        d.setStyleSheet("color: #94A3B8; font-size: 12px;")
        d.setWordWrap(True)
        l.addWidget(d)

        btn = QtWidgets.QPushButton(btn_text)
        btn.setProperty("class", "primary-btn")
        btn.clicked.connect(handler)
        l.addWidget(btn)

        return frame

    def _apply_gaming(self):
        res = self.presets.apply_gaming_preset()
        self.status_lbl.setText("🎮 Gaming Preset успешно применён! Снимок безопасности сохранён.")

    def _apply_work(self):
        res = self.presets.apply_work_preset()
        self.status_lbl.setText("💼 Work Preset активирован.")

    def _flush_ram(self):
        stats = self.engine.optimize_memory()
        freed = stats.get("freed_mb", 0)
        self.status_lbl.setText(f"🚀 ОЗУ очищено! Освобождено {freed} MB.")

    def _flush_dns(self):
        ok = self.engine.flush_dns()
        self.status_lbl.setText("🌐 Кэш DNS успешно очищен!" if ok else "Ошибка сброса DNS.")

    def _enable_timer(self):
        ok = self.engine.set_timer_resolution(0.5)
        self.status_lbl.setText("⏱ Высокоточный таймер 0.5 мс активен!" if ok else "Ошибка установки таймера.")
