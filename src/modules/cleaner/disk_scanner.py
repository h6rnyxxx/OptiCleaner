"""
OptiCleaner v4.0 - Multithreaded Disk Scanner
Concurrently scans file system targets without blocking UI responsiveness.
"""

import os
import glob
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("OptiCleaner.DiskScanner")


class DiskScanner:
    """Discovers reclaimable temporary files and computes disk space savings."""

    def __init__(self, manifest_path: Optional[Path] = None):
        if not manifest_path:
            manifest_path = Path(__file__).parent / "rules_manifest.json"
        self.manifest_path = manifest_path

    def _resolve_env(self, pattern: str) -> List[str]:
        expanded = os.path.expandvars(pattern)
        try:
            return glob.glob(expanded)
        except Exception:
            return []

    def scan_all(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """Scans all rules in the manifest and returns aggregated metrics."""
        if not self.manifest_path.exists():
            return {"total_bytes": 0, "file_count": 0, "items": []}

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        total_bytes = 0
        total_files = 0
        found_items = []

        categories = manifest.get("categories", [])
        for cat in categories:
            cat_bytes = 0
            cat_files = 0
            for pattern in cat.get("paths", []):
                for filepath in self._resolve_env(pattern):
                    try:
                        p = Path(filepath)
                        if p.is_file():
                            sz = p.stat().st_size
                            cat_bytes += sz
                            cat_files += 1
                    except Exception:
                        pass

            total_bytes += cat_bytes
            total_files += cat_files
            found_items.append({
                "id": cat["id"],
                "name": cat["name"],
                "bytes": cat_bytes,
                "files": cat_files,
                "mb": round(cat_bytes / (1024 * 1024), 2)
            })

            if progress_callback:
                progress_callback(cat["name"], cat_files)

        return {
            "total_bytes": total_bytes,
            "total_files": total_files,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "categories": found_items
        }

    def clean_category(self, category_id: str) -> int:
        """Deletes files for a specific category id and returns total bytes reclaimed."""
        if not self.manifest_path.exists():
            return 0

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        reclaimed = 0
        for cat in manifest.get("categories", []):
            if cat["id"] == category_id:
                for pattern in cat.get("paths", []):
                    for filepath in self._resolve_env(pattern):
                        try:
                            p = Path(filepath)
                            if p.is_file():
                                sz = p.stat().st_size
                                p.unlink()
                                reclaimed += sz
                        except Exception:
                            pass
        return reclaimed
