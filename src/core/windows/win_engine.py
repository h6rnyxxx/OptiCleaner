"""
OptiCleaner v4.0 - Windows Engine Implementation
Integrates Registry, Services, Network, Memory, and Restore Point managers.
"""

import os
import sys
import platform
import ctypes
import logging
from typing import Dict, Any, Optional

from src.core.base_engine import BaseEngine
from src.core.windows.registry_manager import RegistryManager
from src.core.windows.service_controller import ServiceController
from src.core.windows.network_tweak_engine import NetworkTweakEngine
from src.core.windows.memory_engine import MemoryEngine
from src.core.windows.timer_resolution import TimerResolutionEngine
from src.core.windows.restore_point_manager import RestorePointManager

logger = logging.getLogger("OptiCleaner.WindowsEngine")


class WindowsEngine(BaseEngine):
    """Concrete implementation of BaseEngine for Windows 10 and 11."""

    def __init__(self):
        self.registry = RegistryManager()
        self.services = ServiceController()
        self.network = NetworkTweakEngine()
        self.memory = MemoryEngine()
        self.timer = TimerResolutionEngine()
        self.restore_points = RestorePointManager()

    def get_os_info(self) -> Dict[str, Any]:
        return {
            "platform": "Windows",
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "is_admin": self.is_admin(),
        }

    def is_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def create_restore_point(self, description: str) -> bool:
        return self.restore_points.create_checkpoint(description)

    def optimize_memory(self) -> Dict[str, int]:
        return self.memory.full_ram_optimization()

    def flush_dns(self) -> bool:
        return self.network.flush_dns()

    def set_timer_resolution(self, desired_ms: float = 0.5) -> bool:
        return self.timer.set_resolution(desired_ms)

    def apply_tweak(self, tweak_id: str, params: Optional[Dict[str, Any]] = None) -> bool:
        logger.info("Applying Windows tweak: %s", tweak_id)
        if tweak_id == "network_low_latency":
            res = self.network.apply_gaming_network_tweaks()
            return all(res.values())
        elif tweak_id == "flush_dns":
            return self.flush_dns()
        elif tweak_id == "disable_telemetry_services":
            for s in self.services.KNOWN_TELEMETRY_SERVICES[:4]:
                self.services.stop_service(s)
                self.services.set_start_type(s, "disabled")
            return True
        return False

    def rollback_tweak(self, tweak_id: str) -> bool:
        logger.info("Rolling back Windows tweak: %s", tweak_id)
        if tweak_id == "disable_telemetry_services":
            for s in self.services.KNOWN_TELEMETRY_SERVICES[:4]:
                self.services.set_start_type(s, "demand")
            return True
        return False
