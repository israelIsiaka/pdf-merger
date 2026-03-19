#!/bin/bash
# Build and package PDF Merger for macOS

set -e

echo "Building PDF Merger macOS Application..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VENV_PATH=".venv/bin/python"
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

# Check if Logo.png exists and convert to ICNS if needed
if [ -f "$PROJECT_DIR/Logo.png" ]; then
    echo -e "${YELLOW}Converting Logo.png to Logo.icns...${NC}"
    if [ ! -f "$PROJECT_DIR/Logo.icns" ]; then
        $VENV_PATH "$PROJECT_DIR/convert_icon.py"
    else
        echo -e "${GREEN}Logo.icns already exists${NC}"
    fi
else
    echo -e "${YELLOW}WARNING: No Logo.png found. Using default icon.${NC}"
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist"

# Build the app bundle
echo -e "${YELLOW}Building app bundle...${NC}"
cd "$PROJECT_DIR"
$VENV_PATH setup.py py2app 2>&1 | grep -E "(building|error|Error|successfully)" || true

# Check if build was successful
if [ -d "$PROJECT_DIR/dist/PDF Merger.app" ]; then
    echo -e "${GREEN}App bundle created successfully${NC}"
else
    echo -e "${RED}FAILED: Could not create app bundle${NC}"
    exit 1
fi

# Create DMG
echo -e "${YELLOW}Creating DMG installer...${NC}"

DMG_FILE="$PROJECT_DIR/dist/PDF-Merger.dmg"
APP_PATH="$PROJECT_DIR/dist/PDF Merger.app"

# Remove existing DMG if it exists
[ -f "$DMG_FILE" ] && rm "$DMG_FILE"

# Create the DMG
hdiutil create -volname "PDF Merger" \
    -srcfolder "$PROJECT_DIR/dist/PDF Merger.app" \
    -ov -format UDZO "$DMG_FILE"

echo -e "${GREEN}DMG created successfully: $DMG_FILE${NC}"

# Print summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "App location: $APP_PATH"
echo "DMG location: $DMG_FILE"
echo ""
echo "Distribution options:"
echo "   1. Direct app: Copy 'PDF Merger.app' from dist/ folder"
echo "   2. DMG: Share 'PDF-Merger.dmg' (easiest for users)"
echo "   3. ZIP: zip -r PDF-Merger.zip dist/'PDF Merger.app'"
echo ""
echo "To test locally: open dist/'PDF Merger.app'"
echo ""
