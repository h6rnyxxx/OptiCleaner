"""
OptiCleaner v4.0 - Game Booster Background Daemon
Detects active game processes and automatically applies High Process Priority and Core Affinity.
"""

import threading
import time
import psutil
import logging
from typing import Set

logger = logging.getLogger("OptiCleaner.GameBooster")


class GameBoosterDaemon:
    """Monitors 3D games and elevates process scheduling priorities."""

    KNOWN_GAMES = {
        "cs2.exe", "dota2.exe", "valorant.exe", "fortniteclient-win64-shipping.exe",
        "apex.exe", "r5apex.exe", "overwatch.exe", "gta5.exe", "cyberpunk2077.exe",
        "warzone.exe", "cod.exe", "rustclient.exe", "minecraft.exe", "javaw.exe"
    }

    def __init__(self, check_interval: int = 5):
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._boosted_pids: Set[int] = set()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="GameBoosterThread")
        self._thread.start()
        logger.info("Game Booster Daemon started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Game Booster Daemon stopped.")

    def _loop(self):
        while self._running:
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    p_name = (proc.info['name'] or '').lower()
                    pid = proc.info['pid']

                    if p_name in self.KNOWN_GAMES and pid not in self._boosted_pids:
                        try:
                            # Set HIGH priority
                            p = psutil.Process(pid)
                            p.nice(psutil.HIGH_PRIORITY_CLASS)
                            self._boosted_pids.add(pid)
                            logger.info("Elevated gaming priority for %s (PID: %s)", p_name, pid)
                        except Exception as err:
                            logger.debug("Could not boost %s: %s", p_name, err)
            except Exception as e:
                logger.debug("Game booster scan error: %s", e)

            time.sleep(self.check_interval)
