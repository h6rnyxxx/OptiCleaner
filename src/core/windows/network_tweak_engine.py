"""
OptiCleaner v4.0 - Network & TCP/IP Optimization Engine
Low-latency esports network tweaks, DNS cache flush, Winsock catalog repair.
"""

import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger("OptiCleaner.NetworkEngine")


class NetworkTweakEngine:
    """Configures TCP stack parameters for reduced ping and optimal packet throughput."""

    @staticmethod
    def flush_dns() -> bool:
        """Flushes the local DNS client cache."""
        try:
            res = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to flush DNS: %s", e)
            return False

    @staticmethod
    def reset_winsock() -> bool:
        """Resets the Winsock catalog back to default clean configuration."""
        try:
            res = subprocess.run(["netsh", "winsock", "reset"], capture_output=True, text=True, timeout=8)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to reset Winsock: %s", e)
            return False

    @staticmethod
    def apply_gaming_network_tweaks() -> Dict[str, bool]:
        """
        Applies network tweaks optimized for low latency & gaming:
        - TCP Auto-Tuning: normal
        - Receive Side Scaling (RSS): enabled
        - Receive Segment Coalescing (RSC): enabled
        - ECN Capability: enabled
        """
        results = {}
        tweaks = [
            ("autotuning", ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"]),
            ("rss", ["netsh", "int", "tcp", "set", "global", "rss=enabled"]),
            ("rsc", ["netsh", "int", "tcp", "set", "global", "rsc=enabled"]),
            ("ecn", ["netsh", "int", "tcp", "set", "global", "ecncapability=enabled"]),
            ("timestamps", ["netsh", "int", "tcp", "set", "global", "timestamps=disabled"]),
        ]

        for name, cmd in tweaks:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                results[name] = (res.returncode == 0)
            except Exception as err:
                logger.warning("Network tweak %s failed: %s", name, err)
                results[name] = False

        return results
