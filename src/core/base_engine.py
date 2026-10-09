"""
OptiCleaner v4.0 - Core Base Engine Interface
Defines the abstract interface for OS-specific optimizations, tweaks, and maintenance tasks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseEngine(ABC):
    """Abstract Base Class for OS-level tuning and system management."""

    @abstractmethod
    def get_os_info(self) -> Dict[str, Any]:
        """Returns details about the underlying OS version, kernel, and architecture."""
        pass

    @abstractmethod
    def is_admin(self) -> bool:
        """Checks if current process has root / administrator privileges."""
        pass

    @abstractmethod
    def create_restore_point(self, description: str) -> bool:
        """Creates an OS rollback / restore point before applying destructive changes."""
        pass

    @abstractmethod
    def optimize_memory(self) -> Dict[str, int]:
        """Flushes standby lists, working sets, and system caches to reclaim RAM."""
        pass

    @abstractmethod
    def flush_dns(self) -> bool:
        """Flushes the system resolver cache and resets network sockets."""
        pass

    @abstractmethod
    def set_timer_resolution(self, desired_ms: float = 0.5) -> bool:
        """Requests high-precision system timer resolution for minimal input latency."""
        pass

    @abstractmethod
    def apply_tweak(self, tweak_id: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Applies an individual optimization tweak transactionally."""
        pass

    @abstractmethod
    def rollback_tweak(self, tweak_id: str) -> bool:
        """Rolls back an individual optimization tweak from saved snapshots."""
        pass
