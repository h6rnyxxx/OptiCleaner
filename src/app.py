"""
OptiCleaner v4.0 - Modular Application Forwarder
Redirects to src.main:main()
"""

import sys
from pathlib import Path

# Set up paths
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.main import main

if __name__ == "__main__":
    main()