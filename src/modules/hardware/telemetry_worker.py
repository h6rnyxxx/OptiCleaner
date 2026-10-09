"""
OptiCleaner v4.0 - Hardware Telemetry Worker
Real-time monitoring of CPU, RAM, Disk, and Network performance indicators.
"""

import time
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger("OptiCleaner.Telemetry")


class TelemetryWorker:
    """Collects real-time hardware metrics for UI meters and performance dials."""

    @staticmethod
    def get_snapshot() -> Dict[str, Any]:
        """Returns instantaneous snapshot of system resources."""
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        # Disk usage of system drive
        disk = psutil.disk_usage(os_drive := "C:\\" if psutil.WINDOWS else "/")

        # Net I/O
        net = psutil.net_io_counters()

        return {
            "cpu_percent": cpu_pct,
            "cpu_count": psutil.cpu_count(logical=True),
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        }
