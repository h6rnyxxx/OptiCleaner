"""
OptiCleaner v4.0 - Windows High Precision Timer Resolution Engine
Uses NtSetTimerResolution via ntdll.dll to request ultra-low 0.5ms kernel timer granularity.
"""

import ctypes
import logging

logger = logging.getLogger("OptiCleaner.TimerResolution")


class TimerResolutionEngine:
    """Controls Windows multimedia and kernel timer resolution down to 0.5 ms."""

    _is_active = False

    @classmethod
    def set_resolution(cls, desired_ms: float = 0.5) -> bool:
        """
        Requests desired timer resolution in milliseconds (e.g. 0.5ms = 5000 in 100ns units).
        """
        try:
            ntdll = ctypes.windll.ntdll
            # 1 ms = 10,000 100ns units -> 0.5 ms = 5,000 units
            units = int(desired_ms * 10000)
            desired_res = ctypes.c_ulong(units)
            set_res = ctypes.c_bool(True)
            current_res = ctypes.c_ulong()

            status = ntdll.NtSetTimerResolution(desired_res, set_res, ctypes.byref(current_res))
            if status == 0:
                cls._is_active = True
                logger.info("Timer resolution set to %s ms (Status: 0, Current: %s units)", desired_ms, current_res.value)
                return True
            else:
                logger.warning("NtSetTimerResolution returned NTSTATUS: 0x%08X", status)
                return False
        except Exception as e:
            logger.error("Failed to set timer resolution: %s", e)
            return False

    @classmethod
    def restore_resolution(cls) -> bool:
        """Restores default system timer resolution."""
        if not cls._is_active:
            return True
        try:
            ntdll = ctypes.windll.ntdll
            desired_res = ctypes.c_ulong(10000)
            set_res = ctypes.c_bool(False)
            current_res = ctypes.c_ulong()

            status = ntdll.NtSetTimerResolution(desired_res, set_res, ctypes.byref(current_res))
            cls._is_active = False
            return status == 0
        except Exception as e:
            logger.error("Failed to restore timer resolution: %s", e)
            return False
