"""
OptiCleaner v4.0 - Optimization Presets Manager
Coordinates presets (Gaming, Work, Audio, Ultra) with pre-application safety snapshots.
"""

import logging
from typing import Dict, Any, List

from src.core.safety.snapshot_engine import SnapshotEngine
from src.core.windows.service_controller import ServiceController
from src.core.windows.network_tweak_engine import NetworkTweakEngine
from src.core.windows.timer_resolution import TimerResolutionEngine
from src.modules.optimizer.power_plan_manager import PowerPlanManager

logger = logging.getLogger("OptiCleaner.PresetsManager")


class PresetsManager:
    """Applies structured optimization profiles safely."""

    def __init__(self):
        self.snapshots = SnapshotEngine()
        self.services = ServiceController()
        self.network = NetworkTweakEngine()
        self.power = PowerPlanManager()
        self.timer = TimerResolutionEngine()

    def apply_gaming_preset(self) -> Dict[str, Any]:
        """
        Gaming Preset:
        - Creates safety snapshot
        - Enables Ultimate Performance Plan
        - Sets 0.5ms Timer Resolution
        - Applies low-latency network tweaks
        - Suppresses non-essential background telemetry services
        """
        logger.info("Applying Gaming Preset...")

        # 1. Snapshot original state
        snap_data = {
            "power_scheme": self.power.get_active_scheme(),
            "services": {}
        }
        for s in ["DiagTrack", "SysMain", "Wsearch"]:
            status = self.services.get_service_status(s)
            if status:
                snap_data["services"][s] = status

        self.snapshots.create_snapshot("gaming_preset", snap_data)

        # 2. Apply Tweaks
        power_ok = self.power.enable_ultimate_performance()
        timer_ok = self.timer.set_resolution(0.5)
        net_res = self.network.apply_gaming_network_tweaks()

        # Stop SysMain (Superfetch) and Diagtrack
        self.services.stop_service("DiagTrack")
        self.services.set_start_type("DiagTrack", "disabled")

        return {
            "preset": "Gaming",
            "power_plan": power_ok,
            "timer_resolution": timer_ok,
            "network": net_res,
            "services_modified": ["DiagTrack"]
        }

    def apply_work_preset(self) -> Dict[str, Any]:
        """Work Preset: Restores balanced services and standard timer resolution."""
        logger.info("Applying Work Preset...")
        self.timer.restore_resolution()
        self.services.set_start_type("Wsearch", "auto")
        self.services.start_service("Wsearch")
        return {"preset": "Work", "status": "balanced"}
