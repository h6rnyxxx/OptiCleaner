"""
OptiCleaner v4.0 - Windows Memory Engine
Flushes standby lists, trims system and process working sets, reclaims active RAM.
"""

import ctypes
import os
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger("OptiCleaner.MemoryEngine")


class MemoryEngine:
    """Provides high-performance native memory purging routines via WinAPI."""

    @staticmethod
    def trim_process_working_sets() -> int:
        """
        Iterates over accessible processes and trims working sets using EmptyWorkingSet.
        Returns the number of processes successfully trimmed.
        """
        psapi = ctypes.windll.psapi
        kernel32 = ctypes.windll.kernel32
        trimmed_count = 0

        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                if pid <= 4:
                    continue
                h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, False, pid)
                if h_proc:
                    res = psapi.EmptyWorkingSet(h_proc)
                    kernel32.CloseHandle(h_proc)
                    if res:
                        trimmed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                logger.debug("Error trimming pid %s: %s", proc.info.get('pid'), e)

        return trimmed_count

    @staticmethod
    def purge_standby_list() -> bool:
        """
        Invokes NtSetSystemInformation (SystemMemoryListInformation / MemoryPurgeStandbyList)
        Requires SeProfileSingleProcessPrivilege or SeIncreaseQuotaPrivilege.
        """
        try:
            ntdll = ctypes.windll.ntdll
            # SystemMemoryListInformation = 80
            # MemoryPurgeStandbyList = 4
            command = ctypes.c_ulong(4)
            status = ntdll.NtSetSystemInformation(
                80,
                ctypes.byref(command),
                ctypes.sizeof(command)
            )
            return status == 0
        except Exception as e:
            logger.warning("Purge standby list syscall failed: %s", e)
            return False

    @classmethod
    def full_ram_optimization(cls) -> Dict[str, Any]:
        """Performs complete memory flush and reports before/after stats."""
        mem_before = psutil.virtual_memory()
        cls.purge_standby_list()
        trimmed_procs = cls.trim_process_working_sets()
        mem_after = psutil.virtual_memory()

        freed_bytes = max(0, mem_before.used - mem_after.used)
        return {
            "trimmed_processes": trimmed_procs,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "used_percent_before": mem_before.percent,
            "used_percent_after": mem_after.percent
        }
