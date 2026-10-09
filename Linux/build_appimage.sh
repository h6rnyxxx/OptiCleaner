#!/bin/bash
# ==============================================================================
# OptiCleaner Linux AppImage Builder
# Builds a self-contained portable AppImage for Linux x86_64
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/AppDir"

echo "[1/4] Preparing AppDir structure..."
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib"
mkdir -p "${APP_DIR}/usr/share/opticleaner/images"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"

echo "[2/4] Copying application assets..."
cp -f "${SCRIPT_DIR}/../src/app.py" "${APP_DIR}/usr/share/opticleaner/app.py"
cp -rf "${SCRIPT_DIR}/../src/images/"* "${APP_DIR}/usr/share/opticleaner/images/"
cp -f "${SCRIPT_DIR}/opticleaner.desktop" "${APP_DIR}/"
cp -f "${SCRIPT_DIR}/opticleaner.desktop" "${APP_DIR}/usr/share/applications/"
cp -f "${SCRIPT_DIR}/opticleaner.png" "${APP_DIR}/"
cp -f "${SCRIPT_DIR}/opticleaner.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/"
cp -f "${SCRIPT_DIR}/AppRun" "${APP_DIR}/AppRun"
chmod +x "${APP_DIR}/AppRun"

echo "[3/4] Checking appimagetool..."
if which appimagetool >/dev/null 2>&1; then
    echo "[+] Running appimagetool..."
    appimagetool "${APP_DIR}" "${SCRIPT_DIR}/OptiCleaner.AppImage"
else
    echo "[!] appimagetool not found, generating portable standalone bundle..."
    # Create portable self-extracting bundle
    cd "${SCRIPT_DIR}"
    tar -czf "${SCRIPT_DIR}/appdir.tar.gz" -C "${APP_DIR}" .
fi

echo "[4/4] Done! OptiCleaner package ready in ${SCRIPT_DIR}"
