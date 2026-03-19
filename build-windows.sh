#!/bin/bash
# Build Windows EXE using PyInstaller

set -e

echo "🏗️  Building PDF Merger Windows Application (.exe)..."

VENV_PATH=".venv/bin/python"
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check for Logo
if [ -f "$PROJECT_DIR/Logo.png" ]; then
    echo -e "${YELLOW}📦 Logo found${NC}"
else
    echo -e "${YELLOW}⚠️  No Logo.png found${NC}"
fi

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist" "$PROJECT_DIR/*.spec"

# Build the EXE
echo -e "${YELLOW}🔨 Building Windows EXE...${NC}"
cd "$PROJECT_DIR"

$VENV_PATH -m PyInstaller \
    --name="PDF Merger" \
    --windowed \
    --onefile \
    --icon="Logo.ico" \
    --add-data="src:src" \
    --distpath="dist/windows" \
    --buildpath="build/windows" \
    --specpath="build/windows" \
    merge_pdfs.py

# Check if build was successful
if [ -f "$PROJECT_DIR/dist/windows/PDF Merger.exe" ]; then
    echo -e "${GREEN}✅ EXE created successfully${NC}"
    
    # Display summary
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Build Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo "📍 EXE location: $PROJECT_DIR/dist/windows/PDF Merger.exe"
    echo ""
    echo "📤 Distribution for Windows:"
    echo "   1. Direct EXE: Share 'PDF Merger.exe'"
    echo "   2. ZIP: zip -r PDF-Merger-Windows.zip dist/windows/"
    echo ""
else
    echo -e "${RED}❌ Failed to create EXE${NC}"
    exit 1
fi
