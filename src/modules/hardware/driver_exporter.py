"""
OptiCleaner v4.0 - Hardware Driver Exporter
Exports installed third-party OEM drivers to backup folder using DISM.
"""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("OptiCleaner.DriverExporter")


class DriverExporter:
    """Exports all installed third-party device drivers (.inf files) via DISM."""

    @staticmethod
    def export_drivers(destination_dir: Path) -> bool:
        """Invokes dism.exe /online /export-driver /destination:<path>."""
        destination_dir.mkdir(parents=True, exist_ok=True)
        try:
            cmd = [
                "dism.exe", "/online", "/export-driver",
                f"/destination:{str(destination_dir)}"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                logger.info("Drivers successfully exported to %s", destination_dir)
                return True
            else:
                logger.warning("DISM export failed: %s", res.stderr)
                return False
        except Exception as e:
            logger.error("Failed to execute DISM driver export: %s", e)
            return False
