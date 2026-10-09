"""
OptiCleaner v4.0 - Safety Snapshot Engine
Creates declarative JSON snapshots of system states (registry values, services) prior to mutation.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("OptiCleaner.SnapshotEngine")


class SnapshotEngine:
    """Records and stores pre-tweak snapshots for 100% reversible rollbacks."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(os.environ.get("LOCALAPPDATA", ".")) / "OptiCleaner" / "snapshots"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, snapshot_name: str, state_data: Dict[str, Any]) -> Path:
        """Saves a timestamped state snapshot to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{snapshot_name}_{timestamp}.json"
        target_path = self.storage_dir / filename

        payload = {
            "name": snapshot_name,
            "created_at": datetime.now().isoformat(),
            "data": state_data
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info("Safety snapshot created at %s", target_path)
        return target_path

    def load_latest_snapshot(self, snapshot_name: str) -> Optional[Dict[str, Any]]:
        """Finds and loads the latest snapshot matching the given name prefix."""
        matches = sorted(self.storage_dir.glob(f"{snapshot_name}_*.json"), reverse=True)
        if not matches:
            return None

        try:
            with open(matches[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load snapshot %s: %s", matches[0], e)
            return None
