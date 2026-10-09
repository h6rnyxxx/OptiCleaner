"""
OptiCleaner v4.0 - Main Window
Modern Navigation Rail and Smooth QStackedWidget container for modular views.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import qtawesome as qta

from src.ui.styles.themes import CYBERPUNK_THEME
from src.ui.views.cleaner_view import CleanerView
from src.ui.views.optimizer_view import OptimizerView
from src.ui.views.hardware_view import HardwareView
from src.ui.views.uninstaller_view import UninstallerView
from src.ui.views.task_manager_view import TaskManagerView
from src.security.hwid_generator import HWIDGenerator


class MainWindow(QtWidgets.QMainWindow):
    """Primary application frame featuring modular views and Cyberpunk theme."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptiCleaner v4.0 — Ultimate PC Optimizer & System Suite")
        self.resize(1100, 720)
        self.setMinimumSize(950, 600)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(CYBERPUNK_THEME)

        central_widget = QtWidgets.QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar / Navigation Rail
        sidebar = QtWidgets.QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(240)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(12)

        # Brand Logo Header
        brand_label = QtWidgets.QLabel("⚡ OptiCleaner")
        brand_label.setStyleSheet("font-size: 20px; font-weight: 900; color: #00E5FF; padding-left: 8px;")
        sidebar_layout.addWidget(brand_label)

        sub_brand = QtWidgets.QLabel("PRO SYSTEM SUITE v4.0")
        sub_brand.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; padding-left: 8px; margin-bottom: 12px;")
        sidebar_layout.addWidget(sub_brand)

        # Navigation Buttons Group
        self.nav_group = QtWidgets.QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("Очистка системы", "fa5s.broom", 0),
            ("Оптимизация & Твики", "fa5s.rocket", 1),
            ("Мониторинг железа", "fa5s.tachometer-alt", 2),
            ("Деинсталлятор ПО", "fa5s.trash-alt", 3),
            ("Диспетчер задач", "fa5s.tasks", 4)
        ]

        for text, icon_name, idx in nav_items:
            btn = QtWidgets.QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            try:
                btn.setIcon(qta.icon(icon_name, color="#00E5FF"))
            except Exception:
                pass
            btn.clicked.connect(lambda _, index=idx: self.stacked_widget.setCurrentIndex(index))
            self.nav_group.addButton(btn, idx)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Bottom HWID and Status Card
        hwid_short = HWIDGenerator.get_hwid()
        hwid_card = QtWidgets.QFrame()
        hwid_card.setStyleSheet("background-color: #131927; border-radius: 8px; padding: 10px; border: 1px solid #1E293B;")
        hwid_l = QtWidgets.QVBoxLayout(hwid_card)
        hwid_l.setSpacing(4)
        hwid_l.setContentsMargins(8, 8, 8, 8)

        lbl_hwid_title = QtWidgets.QLabel("Аппаратный HWID:")
        lbl_hwid_title.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 700;")
        hwid_l.addWidget(lbl_hwid_title)

        lbl_hwid_val = QtWidgets.QLabel(hwid_short)
        lbl_hwid_val.setStyleSheet("color: #38BDF8; font-family: monospace; font-size: 11px; font-weight: 700;")
        lbl_hwid_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        hwid_l.addWidget(lbl_hwid_val)

        sidebar_layout.addWidget(hwid_card)
        main_layout.addWidget(sidebar)

        # 2. Right Content Area: QStackedWidget
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(CleanerView())
        self.stacked_widget.addWidget(OptimizerView())
        self.stacked_widget.addWidget(HardwareView())
        self.stacked_widget.addWidget(UninstallerView())
        self.stacked_widget.addWidget(TaskManagerView())

        main_layout.addWidget(self.stacked_widget)

        # Select first nav button by default
        first_btn = self.nav_group.button(0)
        if first_btn:
            first_btn.setChecked(True)
