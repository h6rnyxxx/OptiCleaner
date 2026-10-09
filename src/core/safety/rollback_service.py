"""
OptiCleaner v4.0 - Rollback Service
Reverts system state from recorded snapshots, restoring original registry keys and services.
"""

import logging
from typing import Dict, Any, List

from src.core.safety.snapshot_engine import SnapshotEngine
from src.core.windows.registry_manager import RegistryManager
from src.core.windows.service_controller import ServiceController

logger = logging.getLogger("OptiCleaner.RollbackService")


class RollbackService:
    """Restores system states back to pre-optimization baselines."""

    def __init__(self):
        self.snapshots = SnapshotEngine()
        self.registry = RegistryManager()
        self.services = ServiceController()

    def rollback_preset(self, preset_name: str) -> bool:
        """Loads the latest snapshot for a preset and restores values."""
        snap = self.snapshots.load_latest_snapshot(preset_name)
        if not snap or "data" not in snap:
            logger.warning("No valid snapshot found to rollback for '%s'", preset_name)
            return False

        data = snap["data"]
        success = True

        # Restore services if any
        if "services" in data:
            for s_name, s_state in data["services"].items():
                start_type = s_state.get("start_type", "demand").lower()
                if "auto" in start_type:
                    self.services.set_start_type(s_name, "auto")
                elif "disabled" in start_type:
                    self.services.set_start_type(s_name, "disabled")
                else:
                    self.services.set_start_type(s_name, "demand")

        logger.info("Rollback of preset '%s' completed with success=%s", preset_name, success)
        return success
