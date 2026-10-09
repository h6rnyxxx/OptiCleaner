"""
OptiCleaner v4.0 - Browser Cache & History Cleaner
Scans and cleans profile caches for Chromium-based browsers and Mozilla Firefox.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("OptiCleaner.BrowserEngine")


class BrowserEngine:
    """Discovers and clears cache directories across installed browsers."""

    @classmethod
    def get_browser_targets(cls) -> List[Dict[str, Any]]:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")

        targets = []
        # Chrome
        chrome_cache = Path(local_appdata) / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
        if chrome_cache.exists():
            targets.append({"name": "Google Chrome Cache", "path": chrome_cache})

        # Edge
        edge_cache = Path(local_appdata) / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache"
        if edge_cache.exists():
            targets.append({"name": "Microsoft Edge Cache", "path": edge_cache})

        # Yandex
        yandex_cache = Path(local_appdata) / "Yandex" / "YandexBrowser" / "User Data" / "Default" / "Cache"
        if yandex_cache.exists():
            targets.append({"name": "Yandex Browser Cache", "path": yandex_cache})

        # Firefox
        ff_dir = Path(local_appdata) / "Mozilla" / "Firefox" / "Profiles"
        if ff_dir.exists():
            for p in ff_dir.glob("*"):
                c2 = p / "cache2"
                if c2.exists():
                    targets.append({"name": f"Firefox Profile Cache ({p.name})", "path": c2})

        return targets

    @classmethod
    def clean_target(cls, target_path: Path) -> int:
        """Removes contents of a browser cache directory and returns freed bytes."""
        freed = 0
        if not target_path.exists():
            return 0

        for item in target_path.glob("**/*"):
            try:
                if item.is_file():
                    freed += item.stat().st_size
                    item.unlink()
            except Exception:
                pass
        return freed
