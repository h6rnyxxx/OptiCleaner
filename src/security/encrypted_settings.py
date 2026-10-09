"""
OptiCleaner v4.0 - Encrypted Settings Storage
Stores user configuration, license tokens, and preferences encrypted with Windows DPAPI.
"""

import os
import json
import ctypes
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("OptiCleaner.EncryptedSettings")


class EncryptedSettings:
    """Manages DPAPI-encrypted user settings persisted on disk."""

    def __init__(self, config_path: Path = None):
        if not config_path:
            config_path = Path(os.environ.get("LOCALAPPDATA", ".")) / "OptiCleaner" / "settings.dat"
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _dpapi_protect(data: bytes) -> bytes:
        """Encrypts binary payload via CryptProtectData (bound to current user login)."""
        try:
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.c_void_p)]

            data_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.c_void_p))
            data_out = DATA_BLOB()

            res = ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(data_in),
                "OptiCleanerConfig",
                None, None, None, 0,
                ctypes.byref(data_out)
            )
            if res:
                out_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)
                ctypes.windll.kernel32.LocalFree(data_out.pbData)
                return out_bytes
        except Exception as e:
            logger.debug("DPAPI encryption unavailable: %s", e)
        return data

    @staticmethod
    def _dpapi_unprotect(data: bytes) -> bytes:
        """Decrypts binary payload via CryptUnprotectData."""
        try:
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.c_void_p)]

            data_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.c_void_p))
            data_out = DATA_BLOB()

            res = ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(data_in),
                None, None, None, None, 0,
                ctypes.byref(data_out)
            )
            if res:
                out_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)
                ctypes.windll.kernel32.LocalFree(data_out.pbData)
                return out_bytes
        except Exception as e:
            logger.debug("DPAPI decryption unavailable: %s", e)
        return data

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Serializes and saves settings encrypted to disk."""
        try:
            raw_json = json.dumps(settings, indent=2).encode("utf-8")
            encrypted = self._dpapi_protect(raw_json)
            with open(self.config_path, "wb") as f:
                f.write(encrypted)
            return True
        except Exception as err:
            logger.error("Failed to save settings: %s", err)
            return False

    def load_settings(self) -> Dict[str, Any]:
        """Loads and decrypts settings from disk."""
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "rb") as f:
                encrypted = f.read()
            decrypted = self._dpapi_unprotect(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as err:
            logger.warning("Could not decrypt settings, returning empty: %s", err)
            return {}
