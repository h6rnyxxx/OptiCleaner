"""
OptiCleaner v4.0 - Application Scanner
Discovers installed Win32 software and UWP/AppX packages via Windows Registry.
"""

import os
import logging
from typing import List, Dict, Any

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger("OptiCleaner.AppScanner")


class AppScanner:
    """Enumerates installed programs across system and user registry hives."""

    UNINSTALL_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
    ] if winreg else []

    @classmethod
    def get_installed_apps(cls) -> List[Dict[str, Any]]:
        """Returns list of installed applications with metadata."""
        if not winreg:
            return []

        apps = []
        seen_names = set()

        for hkey, subkey_path in cls.UNINSTALL_PATHS:
            try:
                with winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ) as root_key:
                    num_subkeys = winreg.QueryInfoKey(root_key)[0]
                    for i in range(num_subkeys):
                        try:
                            sub_name = winreg.EnumKey(root_key, i)
                            with winreg.OpenKey(root_key, sub_name, 0, winreg.KEY_READ) as app_key:
                                def get_val(name):
                                    try:
                                        return winreg.QueryValueEx(app_key, name)[0]
                                    except Exception:
                                        return ""

                                display_name = get_val("DisplayName")
                                if not display_name or display_name in seen_names:
                                    continue

                                # Filter system components
                                if get_val("SystemComponent") == 1:
                                    continue

                                uninstall_str = get_val("UninstallString")
                                if not uninstall_str:
                                    continue

                                seen_names.add(display_name)
                                size_kb = get_val("EstimatedSize") or 0
                                apps.append({
                                    "name": display_name,
                                    "version": get_val("DisplayVersion"),
                                    "publisher": get_val("Publisher"),
                                    "install_location": get_val("InstallLocation"),
                                    "uninstall_string": uninstall_str,
                                    "quiet_uninstall": get_val("QuietUninstallString"),
                                    "size_mb": round(size_kb / 1024, 2) if isinstance(size_kb, (int, float)) else 0.0
                                })
                        except Exception:
                            continue
            except Exception as err:
                logger.debug("Could not read registry hive %s: %s", subkey_path, err)

        return sorted(apps, key=lambda x: x["name"].lower())
