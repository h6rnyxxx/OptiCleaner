"""
OptiCleaner v4.0 - Remnant Hunter
Scans residual artifacts, empty directories, and registry keys left behind by uninstallers.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("OptiCleaner.RemnantHunter")


class RemnantHunter:
    """Finds orphan folders in AppData and ProgramData matching uninstalled app names."""

    COMMON_LOCATIONS = [
        Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path(os.environ.get("APPDATA", "")),
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
    ]

    @classmethod
    def scan_remnants_for_app(cls, app_name: str) -> List[Path]:
        """Searches for folders matching the app name across common install roots."""
        remnants = []
        name_lower = app_name.lower().strip()
        if len(name_lower) < 3:
            return []

        for base_dir in cls.COMMON_LOCATIONS:
            if not base_dir.exists():
                continue
            try:
                for entry in base_dir.iterdir():
                    if entry.is_dir() and name_lower in entry.name.lower():
                        remnants.append(entry)
            except Exception:
                continue

        return remnants

    @classmethod
    def delete_remnant(cls, path: Path) -> bool:
        """Deletes remnant folder cleanly."""
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                return not path.exists()
            elif path.is_file():
                path.unlink()
                return True
        except Exception as e:
            logger.error("Failed to delete remnant %s: %s", path, e)
        return False
