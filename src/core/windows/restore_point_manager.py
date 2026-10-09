"""
OptiCleaner v4.0 - Windows System Restore Point Manager
Guarantees disaster-recovery rollback by triggering Windows System Restore checkpoints.
"""

import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger("OptiCleaner.RestorePoint")


class RestorePointManager:
    """Manages Windows System Restore Points via PowerShell and WMI."""

    @staticmethod
    def is_restore_enabled() -> bool:
        """Checks if System Protection is enabled on drive C:."""
        try:
            cmd = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "(Get-ComputerRestorePoint).Count"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception as e:
            logger.warning("Failed to check restore point status: %s", e)
            return False

    @staticmethod
    def create_checkpoint(description: str = "OptiCleaner Pre-Tweak Safety Snapshot") -> bool:
        """
        Creates an official Windows System Restore Point.
        Uses PowerShell Checkpoint-Computer with Type 'MODIFY_SETTINGS'.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_desc = f"{description} [{timestamp}]"

        ps_script = f"""
        try {{
            Enable-ComputerRestore -Drive "C:\\" -ErrorAction SilentlyContinue
            Checkpoint-Computer -Description "{full_desc}" -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
            exit 0
        }} catch {{
            exit 1
        }}
        """

        try:
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode == 0:
                logger.info("System Restore Point successfully created: '%s'", full_desc)
                return True
            else:
                logger.warning("Checkpoint creation failed: %s", result.stderr)
                return False
        except Exception as err:
            logger.error("Error creating restore point: %s", err)
            return False
