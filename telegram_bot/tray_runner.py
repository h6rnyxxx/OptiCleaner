import sys
import os
import subprocess
import threading
import queue
import time
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
LOG_FILE = os.path.join(BASE_DIR, "bot_tray.log")
LOCK_FILE = os.path.join(BASE_DIR, "bot_tray.lock")
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")

class BotProcessWorker(QtCore.QObject):
    sig_log = QtCore.pyqtSignal(str)
    sig_status_changed = QtCore.pyqtSignal(bool, str) # is_running, status_text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self._is_terminating = False
        self._read_thread = None

    def start_bot(self):
        if self.is_alive():
            self.sig_log.emit("[TRAY] Бот уже запущен.")
            return

        self._is_terminating = False
        py_exe = sys.executable
        # Prefer python.exe for subprocess worker to avoid window creation issues
        if "pythonw" in py_exe.lower():
            candidate = py_exe.lower().replace("pythonw.exe", "python.exe")
            if os.path.exists(candidate):
                py_exe = candidate

        cflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        # Terminate any previously running main.py in this bot dir to prevent conflicts
        try:
            import psutil
            cur_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == cur_pid:
                        continue
                    cmdline = " ".join(proc.info.get('cmdline') or [])
                    if "main.py" in cmdline and ("telegram_bot" in cmdline or os.path.basename(MAIN_SCRIPT) in cmdline):
                        self.sig_log.emit(f"[TRAY] Завершение предыдущего процесса бота (PID {proc.info['pid']})...")
                        proc.kill()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.sig_log.emit(f"[TRAY] Запуск процесса бота: {py_exe} main.py...")
            self.process = subprocess.Popen(
                [py_exe, "-u", MAIN_SCRIPT],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=cflags
            )
            self.sig_status_changed.emit(True, "В сети • Работает")

            self._read_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._read_thread.start()
        except Exception as e:
            self.sig_log.emit(f"[TRAY ОШИБКА] Не удалось запустить бота: {e}")
            self.sig_status_changed.emit(False, f"Ошибка: {e}")

    def _reader_loop(self):
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f_log:
                f_log.write(f"\n--- СЕССИЯ БОТА ЗАПУЩЕНА {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f_log.flush()
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    clean_line = line.rstrip()
                    f_log.write(clean_line + "\n")
                    f_log.flush()
                    self.sig_log.emit(clean_line)
        except Exception as e:
            self.sig_log.emit(f"[TRAY] Поток вывода закрыт: {e}")
        finally:
            if self.process:
                self.process.poll()
            if not self._is_terminating:
                self.sig_status_changed.emit(False, "Остановлен")
                self.sig_log.emit("[TRAY] Процесс бота завершил работу.")

    def stop_bot(self):
        if not self.is_alive():
            self.sig_status_changed.emit(False, "Остановлен")
            return

        self._is_terminating = True
        self.sig_log.emit("[TRAY] Остановка бота...")
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        except Exception as e:
            self.sig_log.emit(f"[TRAY] Ошибка при завершении: {e}")
        finally:
            self.process = None
            self.sig_status_changed.emit(False, "Остановлен")
            self.sig_log.emit("[TRAY] Бот успешно остановлен.")

    def restart_bot(self):
        self.stop_bot()
        time.sleep(1)
        self.start_bot()

    def is_alive(self):
        return self.process is not None and self.process.poll() is None


class BotLogViewer(QtWidgets.QDialog):
    def __init__(self, bot_worker, parent=None):
        super().__init__(parent)
        self.bot_worker = bot_worker
        self.setWindowTitle("OptiCleaner Telegram Bot — Журнал и консоль")
        self.setMinimumSize(780, 520)
        self.resize(840, 560)
        self.setStyleSheet("""
            QDialog {
                background: #0B0F19;
                color: #F8FAFC;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header bar
        head = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QVBoxLayout()
        title_box.setSpacing(2)

        title = QtWidgets.QLabel("🤖 Telegram Bot Console & Live Monitor")
        title.setStyleSheet("color: #38BDF8; font-size: 15px; font-weight: 800;")
        sub = QtWidgets.QLabel("Фоновый режим работы • Полная изоляция от панели задач")
        sub.setStyleSheet("color: #64748B; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        head.addLayout(title_box, 1)

        self.status_badge = QtWidgets.QLabel("🟢 Инициализация...")
        self.status_badge.setStyleSheet("""
            background: rgba(16, 185, 129, 0.12);
            color: #34D399;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 6px;
            border: 1px solid rgba(16, 185, 129, 0.25);
        """)
        head.addWidget(self.status_badge)
        layout.addLayout(head)

        # Console text area
        self.console = QtWidgets.QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(4000)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background: #060910;
                color: #E2E8F0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 10px;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                border: none;
                background: #060910;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1E293B;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38BDF8;
            }
        """)
        layout.addWidget(self.console, 1)

        # Control row
        ctrl = QtWidgets.QHBoxLayout()
        ctrl.setSpacing(10)

        self.chk_autoscroll = QtWidgets.QCheckBox("Автопрокрутка вниз")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        ctrl.addWidget(self.chk_autoscroll)

        ctrl.addStretch()

        btn_clear = QtWidgets.QPushButton("Очистить экран")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #CBD5E1;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
            }
        """)
        btn_clear.clicked.connect(self.console.clear)
        ctrl.addWidget(btn_clear)

        btn_copy = QtWidgets.QPushButton("Копировать логи")
        btn_copy.setStyleSheet(btn_clear.styleSheet())
        btn_copy.clicked.connect(self._copy_logs)
        ctrl.addWidget(btn_copy)

        self.btn_restart = QtWidgets.QPushButton("🔄 Перезапустить бота")
        self.btn_restart.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.15);
                color: #38BDF8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.28);
            }
        """)
        self.btn_restart.clicked.connect(self.bot_worker.restart_bot)
        ctrl.addWidget(self.btn_restart)

        btn_hide = QtWidgets.QPushButton("Скрыть в трей")
        btn_hide.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: #064E3B;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 11px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #34D399;
            }
        """)
        btn_hide.clicked.connect(self.hide)
        ctrl.addWidget(btn_hide)

        layout.addLayout(ctrl)

        # Wire signals
        self.bot_worker.sig_log.connect(self.append_log)
        self.bot_worker.sig_status_changed.connect(self.on_status_changed)

        # Preload existing log file if available
        self._load_initial_log()

    def _load_initial_log(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    tail = lines[-120:] if len(lines) > 120 else lines
                    self.console.setPlainText("".join(tail))
                    if self.chk_autoscroll.isChecked():
                        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())
            except Exception:
                pass

    def append_log(self, text):
        self.console.appendPlainText(text)
        if self.chk_autoscroll.isChecked():
            self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def on_status_changed(self, is_running, status_text):
        if is_running:
            self.status_badge.setText(f"🟢 {status_text}")
            self.status_badge.setStyleSheet("""
                background: rgba(16, 185, 129, 0.12);
                color: #34D399;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 6px;
                border: 1px solid rgba(16, 185, 129, 0.25);
            """)
        else:
            self.status_badge.setText(f"🔴 {status_text}")
            self.status_badge.setStyleSheet("""
                background: rgba(244, 63, 94, 0.12);
                color: #FB7185;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 6px;
                border: 1px solid rgba(244, 63, 94, 0.25);
            """)

    def _copy_logs(self):
        QtWidgets.QApplication.clipboard().setText(self.console.toPlainText())
        btn = self.sender()
        if btn:
            orig = btn.text()
            btn.setText("Скопировано!")
            QtCore.QTimer.singleShot(1200, lambda: btn.setText(orig))

    def closeEvent(self, event):
        # Do not quit the app on close; just hide to tray!
        event.ignore()
        self.hide()


class BotTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.bot_worker = BotProcessWorker()
        self.log_viewer = BotLogViewer(self.bot_worker)

        # Set tray icon
        self.setIcon(self._create_bot_icon())
        self.setToolTip("OptiCleaner Telegram Bot (Инициализация...)")

        # Context menu
        self.menu = QtWidgets.QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
            }
            QMenu::item:disabled {
                color: #64748B;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1E293B;
                margin: 4px 8px;
            }
        """)

        self.act_status = self.menu.addAction("🟢 Статус: Запуск...")
        self.act_status.setEnabled(False)

        self.menu.addSeparator()

        self.act_open_logs = self.menu.addAction("📋 Журнал и консоль логов")
        self.act_open_logs.triggered.connect(self.show_log_viewer)

        self.act_restart = self.menu.addAction("🔄 Перезапустить бота")
        self.act_restart.triggered.connect(self.bot_worker.restart_bot)

        self.act_toggle = self.menu.addAction("⏹ Остановить бота")
        self.act_toggle.triggered.connect(self._toggle_bot)

        self.menu.addSeparator()

        self.act_exit = self.menu.addAction("✕ Выйти (Закрыть бота)")
        self.act_exit.triggered.connect(self._exit_all)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_tray_activated)

        self.bot_worker.sig_status_changed.connect(self._on_bot_status_changed)

        # Start bot
        QtCore.QTimer.singleShot(200, self.bot_worker.start_bot)

    def _create_bot_icon(self):
        # Try to use icon.png from project images if available
        icon_path = os.path.join(PROJECT_ROOT, "images", "icon.png")
        if os.path.exists(icon_path):
            base_pixmap = QtGui.QPixmap(icon_path)
            if not base_pixmap.isNull():
                return QtGui.QIcon(base_pixmap)

        # Fallback: create dynamic crisp circular icon with neon blue robot design
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Dark circular background with cyan glow
        grad = QtGui.QLinearGradient(0, 0, 64, 64)
        grad.setColorAt(0.0, QtGui.QColor("#0284C7"))
        grad.setColorAt(1.0, QtGui.QColor("#0369A1"))
        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(QtGui.QPen(QtGui.QColor("#38BDF8"), 2))
        painter.drawEllipse(2, 2, 60, 60)

        # Bot face / letter
        painter.setPen(QtGui.QColor("#FFFFFF"))
        font = QtGui.QFont("Segoe UI", 24, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(QtCore.QRect(0, 0, 64, 64), QtCore.Qt.AlignCenter, "TG")
        painter.end()

        return QtGui.QIcon(pixmap)

    def _on_tray_activated(self, reason):
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.show_log_viewer()

    def show_log_viewer(self):
        self.log_viewer.show()
        self.log_viewer.raise_()
        self.log_viewer.activateWindow()

    def _toggle_bot(self):
        if self.bot_worker.is_alive():
            self.bot_worker.stop_bot()
        else:
            self.bot_worker.start_bot()

    def _on_bot_status_changed(self, is_running, status_text):
        if is_running:
            self.act_status.setText(f"🟢 Бот в сети (Online)")
            self.act_toggle.setText("⏹ Остановить бота")
            self.setToolTip("OptiCleaner Telegram Bot — Онлайн (Работает)")
            self.showMessage(
                "OptiCleaner Telegram Bot",
                "Бот успешно запущен и работает в системном трее!",
                QtWidgets.QSystemTrayIcon.Information,
                2500
            )
        else:
            self.act_status.setText(f"🔴 Бот остановлен")
            self.act_toggle.setText("▶ Запустить бота")
            self.setToolTip("OptiCleaner Telegram Bot — Остановлен")

    def _exit_all(self):
        self.bot_worker.stop_bot()
        self.hide()
        self.app.quit()


def main():
    # Kill any dangling instances via PID or lock check
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Check system tray availability
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "Ошибка", "Системный трей Windows недоступен на этой системе.")
        sys.exit(1)

    tray_app = BotTrayApp(app)
    tray_app.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
