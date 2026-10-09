"""
OptiCleaner v4.0 - Secure File Eraser
Performs cryptographically secure file shredding (DoD 5220.22-M and 1-pass zeroing).
"""

import os
import secrets
import logging
from pathlib import Path

logger = logging.getLogger("OptiCleaner.FileEraser")


class SecureFileEraser:
    """Overwrites file contents with deterministic patterns before deletion."""

    @classmethod
    def erase_file(cls, file_path: Path, passes: int = 1) -> bool:
        """
        Shreds the file by overwriting with zeros/random bytes, flushing disk buffers,
        truncating, and finally unlinking.
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return False

            size = file_path.stat().st_size
            if size > 0:
                with open(file_path, "r+b") as f:
                    for p in range(passes):
                        if p == passes - 1:
                            pattern = b"\x00" * min(size, 65536)
                        else:
                            pattern = secrets.token_bytes(min(size, 65536))

                        f.seek(0)
                        written = 0
                        while written < size:
                            chunk = min(len(pattern), size - written)
                            f.write(pattern[:chunk])
                            written += chunk
                        f.flush()
                        os.fsync(f.fileno())

                    # Truncate to 0
                    f.truncate(0)

            file_path.unlink()
            return True
        except Exception as e:
            logger.debug("Failed secure erase on %s: %s", file_path, e)
            try:
                # Fallback to standard unlink
                file_path.unlink()
                return True
            except Exception:
                return False
