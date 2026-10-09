"""
OptiCleaner v4.0 - Software Catalog & Package Installer
Installs curated system tools and utilities silently using Windows Package Manager (winget).
"""

import subprocess
import shutil
import logging
from typing import List, Dict, Any

logger = logging.getLogger("OptiCleaner.SoftwareCatalog")


class WingetManager:
    """Installs curated free utility software silently."""

    CURATED_CATALOG = [
        {"id": "7zip.7zip", "name": "7-Zip Archiver", "category": "Archive"},
        {"id": "Notepad++.Notepad++", "name": "Notepad++ Editor", "category": "Editor"},
        {"id": "voidtools.Everything", "name": "Everything Search", "category": "Search"},
        {"id": "CPUID.CPU-Z", "name": "CPU-Z Hardware Info", "category": "Hardware"},
        {"id": "VideoLAN.VLC", "name": "VLC Media Player", "category": "Media"},
        {"id": "Mozilla.Firefox", "name": "Firefox Browser", "category": "Browser"},
        {"id": "GeekUninstaller.GeekUninstaller", "name": "Geek Uninstaller", "category": "Tool"},
    ]

    @classmethod
    def is_winget_available(cls) -> bool:
        return shutil.which("winget") is not None

    @classmethod
    def install_package(cls, package_id: str) -> bool:
        """Installs package silently via winget."""
        if not cls.is_winget_available():
            logger.warning("winget CLI not found on system.")
            return False

        try:
            cmd = [
                "winget", "install", "--id", package_id, "-e",
                "--silent", "--accept-source-agreements", "--accept-package-agreements"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to install %s: %s", package_id, e)
            return False
