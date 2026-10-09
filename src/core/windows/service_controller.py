"""
OptiCleaner v4.0 - Windows Service Controller
Controls Windows background services (sc.exe / WinAPI), supporting state saving and safe rollback.
"""

import subprocess
import logging
from typing import Dict, Optional, List

logger = logging.getLogger("OptiCleaner.ServiceController")


class ServiceController:
    """Manages Windows Services lifecycle and startup configuration."""

    KNOWN_TELEMETRY_SERVICES = [
        "DiagTrack",         # Connected User Experiences and Telemetry
        "dmwappushservice",  # WAP Push Message Routing Service
        "diagnosticshub.standardcollector.service",
        "WerSvc",            # Windows Error Reporting Service
        "SysMain",           # SuperFetch (disables on NVMe/SSD to reduce background I/O)
        "Wsearch",           # Windows Search Indexer
        "XblAuthManager",    # Xbox Live Auth (optional)
        "XblGameSave",       # Xbox Live Game Save (optional)
    ]

    @staticmethod
    def get_service_status(service_name: str) -> Optional[Dict[str, str]]:
        """Queries current service status and start type via sc qc and sc query."""
        try:
            query = subprocess.run(["sc", "query", service_name], capture_output=True, text=True, timeout=5)
            if query.returncode != 0:
                return None

            qc = subprocess.run(["sc", "qc", service_name], capture_output=True, text=True, timeout=5)
            state = "STOPPED"
            if "RUNNING" in query.stdout:
                state = "RUNNING"

            start_type = "DEMAND_START"
            if "AUTO_START" in qc.stdout:
                start_type = "AUTO_START"
            elif "DISABLED" in qc.stdout:
                start_type = "DISABLED"

            return {"name": service_name, "state": state, "start_type": start_type}
        except Exception as e:
            logger.debug("Service %s query error: %s", service_name, e)
            return None

    @staticmethod
    def set_start_type(service_name: str, start_type: str = "disabled") -> bool:
        """
        Sets service startup type: 'auto', 'demand' (manual), or 'disabled'.
        """
        try:
            res = subprocess.run(["sc", "config", service_name, f"start={start_type}"], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception as err:
            logger.error("Failed to config service %s: %s", service_name, err)
            return False

    @staticmethod
    def stop_service(service_name: str) -> bool:
        """Stops a running Windows service."""
        try:
            res = subprocess.run(["sc", "stop", service_name], capture_output=True, text=True, timeout=8)
            return res.returncode == 0
        except Exception as err:
            logger.error("Failed to stop service %s: %s", service_name, err)
            return False

    @staticmethod
    def start_service(service_name: str) -> bool:
        """Starts a stopped Windows service."""
        try:
            res = subprocess.run(["sc", "start", service_name], capture_output=True, text=True, timeout=8)
            return res.returncode == 0
        except Exception as err:
            logger.error("Failed to start service %s: %s", service_name, err)
            return False
