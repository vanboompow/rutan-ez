#!/usr/bin/env bash
# install_openvsp.sh
# ==================
# Install OpenVSP 3.48.2 Python bindings for macOS ARM64 (Apple Silicon).
#
# IMPORTANT: OpenVSP is NOT available on pip or conda-forge.
# It ships as a macOS application bundle with embedded Python bindings.
# This script downloads the bundle, extracts the .so bindings, and wires
# them into the active Python environment via a .pth file.
#
# Requirements:
#   - macOS ARM64 (Apple Silicon)
#   - Python 3.13 (OpenVSP 3.48.2 bundles Python 3.13 bindings)
#     Install via: brew install python@3.13
#   - curl and unzip (system tools, always present on macOS)
#
# Usage:
#   bash scripts/install_openvsp.sh
#
# After installation, verify with:
#   python3 -c "import openvsp as vsp; print(vsp.GetVSPVersion())"

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENVSP_VERSION="3.48.2"
OPENVSP_DOWNLOAD_URL="https://openvsp.org/download.php?file=zips/current/mac/OpenVSP-${OPENVSP_VERSION}-macos-14-ARM64-Python3.13.zip"
INSTALL_DIR="${HOME}/.local/openvsp"
OPENVSP_EXTRACT_DIR="${INSTALL_DIR}/OpenVSP-${OPENVSP_VERSION}-macos-14-ARM64-Python3.13"
ZIP_PATH="${INSTALL_DIR}/openvsp-${OPENVSP_VERSION}-macos-arm64.zip"

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# Step 0: Verify Python 3.13 (matches OpenVSP bundled bindings)
# ---------------------------------------------------------------------------
info "Checking Python 3.13..."

PYTHON313=""
for candidate in python3.13 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" == "3" && "$minor" == "13" ]]; then
            PYTHON313="$candidate"
            info "Found Python 3.13: $PYTHON313 ($ver)"
            break
        fi
    fi
done

if [[ -z "$PYTHON313" ]]; then
    error "Python 3.13 not found. OpenVSP ${OPENVSP_VERSION} bundles Python 3.13 bindings."
    error "Install it with: brew install python@3.13"
    error "Then re-run this script."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 1: Create install directory
# ---------------------------------------------------------------------------
info "Creating install directory: ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"

# ---------------------------------------------------------------------------
# Step 2: Download OpenVSP
# ---------------------------------------------------------------------------
if [[ -f "${ZIP_PATH}" ]]; then
    info "Archive already downloaded: ${ZIP_PATH}"
else
    info "Downloading OpenVSP ${OPENVSP_VERSION} macOS ARM64..."
    info "URL: ${OPENVSP_DOWNLOAD_URL}"
    info "(This is ~100MB — may take a moment)"
    curl -L --progress-bar -o "${ZIP_PATH}" "${OPENVSP_DOWNLOAD_URL}" || {
        error "Download failed. Check your internet connection and the URL:"
        error "  ${OPENVSP_DOWNLOAD_URL}"
        error "You can also manually download from https://openvsp.org/download.php"
        error "and place the ZIP at: ${ZIP_PATH}"
        exit 1
    }
    info "Download complete."
fi

# ---------------------------------------------------------------------------
# Step 3: Extract the bundle
# ---------------------------------------------------------------------------
if [[ -d "${OPENVSP_EXTRACT_DIR}" ]]; then
    info "Bundle already extracted: ${OPENVSP_EXTRACT_DIR}"
else
    info "Extracting OpenVSP bundle..."
    unzip -q "${ZIP_PATH}" -d "${INSTALL_DIR}"

    # Detect actual extracted directory name (in case naming differs)
    EXTRACTED=$(find "${INSTALL_DIR}" -maxdepth 1 -type d -name "OpenVSP-*" | head -1)
    if [[ -z "$EXTRACTED" ]]; then
        error "Could not find extracted OpenVSP directory in ${INSTALL_DIR}"
        error "Archive contents:"
        unzip -l "${ZIP_PATH}" | head -20
        exit 1
    fi

    if [[ "$EXTRACTED" != "$OPENVSP_EXTRACT_DIR" ]]; then
        warn "Extracted to ${EXTRACTED} (expected ${OPENVSP_EXTRACT_DIR})"
        OPENVSP_EXTRACT_DIR="$EXTRACTED"
    fi
    info "Extracted to: ${OPENVSP_EXTRACT_DIR}"
fi

# ---------------------------------------------------------------------------
# Step 4: Locate the Python bindings directory
# ---------------------------------------------------------------------------
info "Locating OpenVSP Python bindings..."

# OpenVSP 3.48+ bundles bindings as a Python package:
#   .../python/openvsp/openvsp/__init__.py  (the importable package)
#   .../python/openvsp/setup.py
# The .pth file must point to .../python/openvsp/ so `import openvsp` finds __init__.py
PYTHON_BINDINGS_DIR=""

# Strategy 1: Look for the package-style layout (3.48+)
for candidate in \
    "${OPENVSP_EXTRACT_DIR}/python/openvsp" \
    "${OPENVSP_EXTRACT_DIR}/OpenVSP.app/Contents/python/openvsp"; do
    if [[ -f "$candidate/openvsp/__init__.py" ]]; then
        PYTHON_BINDINGS_DIR="$candidate"
        break
    fi
done

# Strategy 2: Look for flat .so layout (older versions)
if [[ -z "$PYTHON_BINDINGS_DIR" ]]; then
    for candidate in \
        "${OPENVSP_EXTRACT_DIR}/python" \
        "${OPENVSP_EXTRACT_DIR}/OpenVSP.app/Contents/python"; do
        if ls "$candidate"/openvsp*.so &>/dev/null 2>&1 || ls "$candidate"/_openvsp*.so &>/dev/null 2>&1; then
            PYTHON_BINDINGS_DIR="$candidate"
            break
        fi
    done
fi

# Strategy 3: Search for __init__.py or .so
if [[ -z "$PYTHON_BINDINGS_DIR" ]]; then
    warn "Could not auto-detect bindings directory. Searching..."
    INIT_PY=$(find "${OPENVSP_EXTRACT_DIR}" -path "*/openvsp/__init__.py" 2>/dev/null | head -1)
    if [[ -n "$INIT_PY" ]]; then
        # Point to parent of the openvsp/ package dir
        PYTHON_BINDINGS_DIR=$(dirname "$(dirname "$INIT_PY")")
    else
        PYTHON_BINDINGS_DIR=$(find "${OPENVSP_EXTRACT_DIR}" -name "openvsp*.so" -o -name "_openvsp*.so" 2>/dev/null \
            | head -1 | xargs dirname 2>/dev/null || true)
    fi
fi

if [[ -z "$PYTHON_BINDINGS_DIR" ]]; then
    error "Could not find OpenVSP Python bindings in the bundle."
    error "Bundle structure:"
    find "${OPENVSP_EXTRACT_DIR}" -maxdepth 5 \( -name "*.so" -o -name "__init__.py" \) | head -20
    error ""
    error "Please check the OpenVSP bundle structure and update this script,"
    error "or manually add the python/ directory to your PYTHONPATH:"
    error "  export PYTHONPATH=/path/to/openvsp/python:\$PYTHONPATH"
    exit 1
fi

info "Found Python bindings: ${PYTHON_BINDINGS_DIR}"

# ---------------------------------------------------------------------------
# Step 5: Install OpenVSP packages via pip
# ---------------------------------------------------------------------------
info "Installing OpenVSP Python packages via pip..."

PYTHON_ROOT="${OPENVSP_EXTRACT_DIR}/python"

# Install packages in dependency order
for pkg in openvsp_config utilities degen_geom vsp_airfoils openvsp; do
    PKG_DIR="${PYTHON_ROOT}/${pkg}"
    if [[ -d "$PKG_DIR" && -f "$PKG_DIR/setup.py" ]]; then
        info "Installing ${pkg}..."
        "$PYTHON313" -m pip install --break-system-packages "$PKG_DIR" 2>&1 | tail -1
    else
        warn "Package ${pkg} not found at ${PKG_DIR}, skipping"
    fi
done

# ---------------------------------------------------------------------------
# Step 6: Smoke test
# ---------------------------------------------------------------------------
info "Running smoke test: import openvsp as vsp; print(vsp.GetVSPVersion())"

VSP_VERSION=$("$PYTHON313" -c "import openvsp as vsp; print(vsp.GetVSPVersion())" 2>&1) || {
    error "Smoke test FAILED. The import succeeded but threw an error:"
    error "  ${VSP_VERSION}"
    error ""
    error "Troubleshooting:"
    error "  1. Check that the .so file is for macOS ARM64 (not x86_64)"
    error "  2. Check macOS Gatekeeper: xattr -d com.apple.quarantine '${PYTHON_BINDINGS_DIR}'/*.so"
    error "  3. Try: PYTHONPATH='${PYTHON_BINDINGS_DIR}' python3 -c 'import openvsp'"
    exit 1
}

echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}  OpenVSP ${OPENVSP_VERSION} installed successfully!${NC}"
echo -e "${GREEN}  Version: ${VSP_VERSION}${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
info "Verify anytime with:"
info "  python3 -c \"import openvsp as vsp; print(vsp.GetVSPVersion())\""
echo ""
info "Bindings location: ${PYTHON_BINDINGS_DIR}"
info "PTH file: ${PTH_FILE}"
echo ""
warn "NOTE: If you switch Python environments (venv, conda, etc.),"
warn "you may need to add ${PYTHON_BINDINGS_DIR} to PYTHONPATH manually,"
warn "or re-run this script to install the .pth in the new environment."
