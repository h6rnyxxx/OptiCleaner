"""
OptiCleaner v4.0 - Hardware ID Generator
Calculates a stable, tamper-resistant hardware identifier based on CPU, Motherboard, and Disk UUIDs.
"""

import os
import sys
import hashlib
import subprocess
import logging

logger = logging.getLogger("OptiCleaner.HWID")


class HWIDGenerator:
    """Generates deterministic HWID tied strictly to physical machine components."""

    @classmethod
    def get_hwid(cls) -> str:
        """
        Returns normalized HWID in format: OC-XXXX-XXXX-XXXX-XXXX
        """
        components = [
            cls._get_cpu_id(),
            cls._get_motherboard_uuid(),
            cls._get_disk_serial()
        ]
        raw_combined = "|".join(components)
        digest = hashlib.sha256(raw_combined.encode("utf-8")).hexdigest().upper()
        # Segment into 4 chunks of 4 characters
        return f"OC-{digest[:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"

    @staticmethod
    def _run_wmic(query: str) -> str:
        try:
            cmd = ["wmic"] + query.split()
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            if len(lines) >= 2:
                return lines[1]
        except Exception:
            pass
        return ""

    @classmethod
    def _get_cpu_id(cls) -> str:
        val = cls._run_wmic("cpu get processorid")
        if not val:
            val = os.environ.get("PROCESSOR_IDENTIFIER", "GENERIC-CPU")
        return val

    @classmethod
    def _get_motherboard_uuid(cls) -> str:
        val = cls._run_wmic("csproduct get uuid")
        if not val:
            val = cls._run_wmic("baseboard get serialnumber")
        return val or "GENERIC-BASEBOARD"

    @classmethod
    def _get_disk_serial(cls) -> str:
        val = cls._run_wmic("diskdrive get serialnumber")
        return val or "GENERIC-DISK"
