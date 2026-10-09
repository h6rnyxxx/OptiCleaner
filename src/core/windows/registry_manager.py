"""
OptiCleaner v4.0 - Transactional Windows Registry Manager
Ensures all registry tweaks are backed up as valid .reg files before mutation.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Any, Optional, Tuple

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger("OptiCleaner.RegistryManager")


class RegistryManager:
    """Provides safe, transactional modifications to the Windows Registry."""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path(os.environ.get("LOCALAPPDATA", ".")) / "OptiCleaner" / "reg_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_key(self, root_key_name: str, subkey: str, filename: str) -> Optional[Path]:
        """
        Exports a registry key to a .reg file using reg.exe export.
        Enables 1-click restore in case of rollback.
        """
        full_key = f"{root_key_name}\\{subkey}"
        target_file = self.backup_dir / f"{filename}.reg"
        try:
            cmd = ["reg", "export", full_key, str(target_file), "/y"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                logger.debug("Backed up registry key %s -> %s", full_key, target_file)
                return target_file
        except Exception as e:
            logger.warning("Could not export reg key %s: %s", full_key, e)
        return None

    def get_value(self, root_key, subkey: str, value_name: str) -> Optional[Tuple[Any, int]]:
        """Reads a value from Windows Registry safely."""
        if not winreg:
            return None
        try:
            with winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ) as key:
                return winreg.QueryValueEx(key, value_name)
        except (FileNotFoundError, OSError):
            return None

    def set_value(self, root_key, subkey: str, value_name: str, value_type: int, value: Any, backup: bool = True) -> bool:
        """Sets a registry key value, creating subkeys if necessary."""
        if not winreg:
            return False
        if backup:
            root_name = "HKLM" if root_key == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            safe_name = subkey.replace("\\", "_")
            self.backup_key(root_name, subkey, f"{safe_name}_{value_name}")

        try:
            with winreg.CreateKeyEx(root_key, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value)
                return True
        except Exception as err:
            logger.error("Failed to set registry value %s\\%s: %s", subkey, value_name, err)
            return False

    def delete_value(self, root_key, subkey: str, value_name: str) -> bool:
        """Deletes a registry value safely."""
        if not winreg:
            return False
        try:
            with winreg.OpenKey(root_key, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
                return True
        except FileNotFoundError:
            return True
        except Exception as err:
            logger.error("Failed to delete registry value %s\\%s: %s", subkey, value_name, err)
            return False

    def restore_from_reg_file(self, reg_path: Path) -> bool:
        """Imports a previously backed-up .reg file using reg.exe import."""
        if not reg_path.exists():
            return False
        try:
            cmd = ["reg", "import", str(reg_path)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to restore from %s: %s", reg_path, e)
            return False
