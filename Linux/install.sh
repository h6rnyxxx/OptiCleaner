#!/bin/bash
# ==============================================================================
# OptiCleaner Linux Professional Installer
# Automatically installs OptiCleaner, Desktop Shortcut, and Icons
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_SRC="${SCRIPT_DIR}/OptiCleaner.AppImage"
ICON_SRC="${SCRIPT_DIR}/opticleaner.png"
DESKTOP_SRC="${SCRIPT_DIR}/opticleaner.desktop"

INSTALL_BIN_DIR="${HOME}/.local/bin"
INSTALL_APPS_DIR="${HOME}/.local/share/applications"
INSTALL_ICONS_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

echo "========================================================"
echo "    OptiCleaner Linux Installation by h6rnyx 3^"
echo "========================================================"

# 1. Create target directories
mkdir -p "${INSTALL_BIN_DIR}"
mkdir -p "${INSTALL_APPS_DIR}"
mkdir -p "${INSTALL_ICONS_DIR}"

# 2. Check and copy AppImage
if [ -f "${APPIMAGE_SRC}" ]; then
    echo "[+] Installing OptiCleaner executable..."
    cp -f "${APPIMAGE_SRC}" "${INSTALL_BIN_DIR}/OptiCleaner"
    chmod +x "${INSTALL_BIN_DIR}/OptiCleaner"
else
    echo "[-] Warning: OptiCleaner.AppImage not found in ${SCRIPT_DIR}"
fi

# 3. Copy Icon
if [ -f "${ICON_SRC}" ]; then
    echo "[+] Installing application icon..."
    cp -f "${ICON_SRC}" "${INSTALL_ICONS_DIR}/opticleaner.png"
fi

# 4. Install Desktop File
echo "[+] Configuring desktop application launcher..."
cat > "${INSTALL_APPS_DIR}/opticleaner.desktop" << EOF
[Desktop Entry]
Type=Application
Name=OptiCleaner
GenericName=System Optimizer & Cleaner
Comment=Professional System Cleanup and Optimization Suite
Exec=${INSTALL_BIN_DIR}/OptiCleaner %F
Icon=opticleaner
Categories=System;Utility;Settings;
Terminal=false
StartupNotify=true
StartupWMClass=OptiCleaner
EOF

chmod +x "${INSTALL_APPS_DIR}/opticleaner.desktop"

# 5. Create Desktop icon on ~/Desktop if directory exists
if [ -d "${HOME}/Desktop" ]; then
    cp -f "${INSTALL_APPS_DIR}/opticleaner.desktop" "${HOME}/Desktop/opticleaner.desktop"
    chmod +x "${HOME}/Desktop/opticleaner.desktop"
    if which gio >/dev/null 2>&1; then
        gio set "${HOME}/Desktop/opticleaner.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "[+] Desktop shortcut created on ${HOME}/Desktop"
fi

# 6. Update desktop databases
if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${INSTALL_APPS_DIR}" 2>/dev/null || true
fi
if which gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "========================================================"
echo "✓ OptiCleaner installed successfully!"
echo "  Run via application menu or terminal command: OptiCleaner"
echo "========================================================"
