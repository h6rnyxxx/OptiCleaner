"""
OptiCleaner v4.0 - Local Crash Reporter
Intercepts unhandled exceptions, writes structured anonymized crash dumps locally.
"""

import sys
import os
import traceback
import platform
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("OptiCleaner.CrashReporter")


class CrashReporter:
    """Installs sys.excepthook to capture and log crashes safely without telemetry leakage."""

    @classmethod
    def setup(cls, log_dir: Path = None):
        if not log_dir:
            log_dir = Path(os.environ.get("LOCALAPPDATA", ".")) / "OptiCleaner" / "crash_reports"
        log_dir.mkdir(parents=True, exist_ok=True)
        cls.log_dir = log_dir
        sys.excepthook = cls.handle_exception

    @classmethod
    def handle_exception(cls, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = cls.log_dir / f"crash_{timestamp}.log"

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        sys_info = f"OS: {platform.system()} {platform.release()} ({platform.version()})\nPython: {sys.version}\n"

        # Sanitize sensitive username paths
        user_name = os.environ.get("USERNAME", "")
        if user_name:
            error_msg = error_msg.replace(user_name, "<USER>")

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("=== OptiCleaner v4.0 Crash Report ===\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(sys_info)
                f.write("\n=== Traceback ===\n")
                f.write(error_msg)
            logger.critical("Application crashed. Report written to %s", report_file)
        except Exception:
            pass

        sys.__excepthook__(exc_type, exc_value, exc_traceback)
