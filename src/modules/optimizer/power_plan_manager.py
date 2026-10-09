"""
OptiCleaner v4.0 - Windows Power Plan Manager
Activates Ultimate Performance and High Performance energy profiles via powercfg.
"""

import subprocess
import logging
from typing import Dict, Any, List

logger = logging.getLogger("OptiCleaner.PowerPlan")


class PowerPlanManager:
    """Controls Windows ACPI power schemes for maximum CPU unthrottling."""

    ULTIMATE_PERF_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"
    HIGH_PERF_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"

    @classmethod
    def get_active_scheme(cls) -> str:
        """Returns the GUID of the currently active power scheme."""
        try:
            res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
            # Example output: Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c (High performance)
            if "GUID:" in res.stdout:
                parts = res.stdout.split("GUID:")
                if len(parts) > 1:
                    guid = parts[1].strip().split()[0]
                    return guid
        except Exception as e:
            logger.warning("Could not query active power scheme: %s", e)
        return ""

    @classmethod
    def enable_ultimate_performance(cls) -> bool:
        """Duplicates and activates the hidden Windows Ultimate Performance scheme."""
        try:
            # First try duplicate scheme to ensure it exists
            dup = subprocess.run(["powercfg", "-duplicatescheme", cls.ULTIMATE_PERF_GUID], capture_output=True, text=True, timeout=5)
            target_guid = cls.ULTIMATE_PERF_GUID
            if "GUID:" in dup.stdout:
                parts = dup.stdout.split("GUID:")
                target_guid = parts[1].strip().split()[0]

            # Activate
            res = subprocess.run(["powercfg", "-setactive", target_guid], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to enable Ultimate Performance plan: %s", e)
            return False
