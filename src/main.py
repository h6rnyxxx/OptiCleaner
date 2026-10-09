"""
OptiCleaner v4.0 - Primary Application Entry Point
Initializes crash hooks, single-instance mutex, High-DPI scaling, and starts the PyQt GUI.
"""

import sys
import os
import ctypes
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

# Ensure src package root is on sys.path
SRC_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SRC_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.safety.crash_reporter import CrashReporter
from src.ui.main_window import MainWindow


def acquire_single_instance_mutex(mutex_name: str = "OptiCleaner_SingleInstance_Mutex"):
    """Creates a Windows named mutex to ensure only one instance is active."""
    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            return None
        return mutex
    except Exception:
        return True


def is_elevated() -> bool:
    """Verifies whether the current process holds Administrator rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main():
    # 1. Setup local crash reporting
    CrashReporter.setup()

    # 2. Acquire single-instance lock
    mutex = acquire_single_instance_mutex()
    if mutex is None:
        print("[!] Another instance of OptiCleaner is already running.")
        sys.exit(0)

    # 3. Configure High-DPI Display Scaling
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("OptiCleaner")
    app.setApplicationVersion("4.0.0")

    # Set Application Icon if available
    icon_path = REPO_ROOT / "images" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # 4. Initialize and show Main Window
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
