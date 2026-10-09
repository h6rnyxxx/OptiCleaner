"""
OptiCleaner v4.0 - Process Monitor & Task Manager
Enumerates active processes, CPU/RAM footprints, and allows priority tuning or termination.
"""

import psutil
import logging
from typing import List, Dict, Any

logger = logging.getLogger("OptiCleaner.ProcessMonitor")


class ProcessMonitor:
    """Provides process list and process lifecycle controls."""

    @staticmethod
    def get_processes() -> List[Dict[str, Any]]:
        """Returns sorted list of top processes by memory usage."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                mem_mb = round(p.info['memory_info'].rss / (1024 * 1024), 1)
                procs.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "cpu_percent": p.info['cpu_percent'] or 0.0,
                    "mem_mb": mem_mb,
                    "status": p.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x['mem_mb'], reverse=True)

    @staticmethod
    def terminate_process(pid: int) -> bool:
        """Kills a process by PID."""
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=3)
            return True
        except Exception as e:
            logger.error("Failed to terminate PID %s: %s", pid, e)
            return False

    @staticmethod
    def set_priority(pid: int, priority_class: int) -> bool:
        """Adjusts scheduling priority of a process."""
        try:
            p = psutil.Process(pid)
            p.nice(priority_class)
            return True
        except Exception as e:
            logger.error("Failed to set priority for PID %s: %s", pid, e)
            return False
