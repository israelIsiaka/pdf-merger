# PDF Merger - Build & Distribution Guide

This guide explains how to build installers and distribute the PDF Merger application.

## 📦 Distribution Files

### Current Distribution Status

After building, you'll have these distribution options:

#### **macOS**
- `dist/PDF-Merger.dmg` (31 MB) - Professional DMG installer
- `dist/PDF Merger.app/` - Standalone app bundle (can be distributed directly)

#### **Windows - Option 1: Portable Folder**
- `dist/windows/PDF Merger/` (84 MB) - Standalone portable application
- Users can copy and run directly without installation
- No registry modifications, clean uninstall (just delete folder)

#### **Windows - Option 2: Installer Executable** *(requires NSIS)*
- `dist/PDF-Merger-Installer.exe` (30-40 MB) - Professional Windows installer
- Handles installation, Start Menu shortcuts, uninstall
- Recommended for professional distribution

## 🛠️ Building for Distribution

### Prerequisites

**All Platforms:**
```bash
cd /Users/user/pdf-merger
source .venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt  # Ensure dependencies are installed
```

**For Windows Installer (NSIS):**
- Download and install NSIS from: https://nsis.sourceforge.io/
- Or on Windows with Chocolatey: `choco install nsis`
- NSIS is optional - portable folder works without it

**For macOS (py2app):**
Already installed in venv, automatically used by build.sh

### Cross-Platform Building

You can build for a different platform than your current OS using PyInstaller.

**Build Windows version on macOS:**
```bash
python build.py windows
# Creates: dist/windows/PDF Merger/ (Windows-compatible)
```

**Build macOS version on Windows:**
```bash
python build.py macos
# Creates: dist/PDF-Merger.dmg (macOS-compatible)
```

**Note:** While PyInstaller can create executables for other platforms on macOS, the most reliable approach is building on the target platform itself for production releases.

### Build Commands

#### Build macOS Installer
```bash
cd /Users/user/pdf-merger
python build.py macos
# or use the convenience script:
./build.sh
```

**Output:** `dist/PDF-Merger.dmg` (ready for distribution)

#### Build Windows Portable Folder
```bash
cd /Users/user/pdf-merger
python build.py windows
```

**Output:** `dist/windows/PDF Merger/` (compress as ZIP for distribution)

#### Build Windows Professional Installer
```bash
cd /Users/user/pdf-merger
python build.py windows-installer
```

**Requirements:** NSIS must be installed
**Output:** `dist/PDF-Merger-Installer.exe` (ready for distribution)

---

## 📦 Cross-Platform Testing Workflow

### Build on macOS, Test on Windows

The recommended approach for testing the Windows build before distribution:

#### **Step 1: Build on macOS**
```bash
cd /Users/user/pdf-merger
source .venv/bin/activate
python build.py windows
```

#### **Step 2: Bundle as ZIP**
```bash
cd /Users/user/pdf-merger/dist/windows
zip -r ../PDF-Merger-Windows-Test.zip "PDF Merger"
```

#### **Step 3: Transfer to Windows**
- Email or transfer `dist/PDF-Merger-Windows-Test.zip` to Windows PC
- Or use cloud storage (Google Drive, OneDrive, Dropbox)

#### **Step 4: Extract and Test on Windows**
```powershell
# PowerShell on Windows
Expand-Archive PDF-Merger-Windows-Test.zip -DestinationPath .

# Run the app
.\"PDF Merger\\PDF Merger.exe"
```

#### **Complete One-Command Build (macOS)**
```bash
cd /Users/user/pdf-merger && source .venv/bin/activate && python build.py windows && cd dist/windows && zip -r ../PDF-Merger-Windows-Test.zip "PDF Merger" && cd /Users/user/pdf-merger && echo "✅ Ready: dist/PDF-Merger-Windows-Test.zip"
```

---

### Build on Windows, Test on macOS

Similarly, you can build on Windows for macOS testing:

#### **Step 1: Build on Windows**
```bash
cd C:\path\to\pdf-merger
.venv\Scripts\activate.bat
python build.py macos
```

#### **Step 2: Transfer DMG to macOS**
- Transfer `dist/PDF-Merger.dmg` to macOS

#### **Step 3: Test on macOS**
```bash
# Double-click to mount and test
open dist/PDF-Merger.dmg
```

#### Build Everything (macOS only)
```bash
cd /Users/user/pdf-merger
python build.py macos && python build.py windows
```

## 📤 Distribution Methods

### For macOS Users

**Method 1: DMG Installer** (Recommended)
```
1. Share: dist/PDF-Merger.dmg
2. Users double-click DMG
3. Drag app to Applications folder
4. Eject DMG
5. Run from Applications
```

**Method 2: Direct App Distribution**
```
1. Share: dist/PDF Merger.app (as ZIP or folder)
2. Users extract/copy to Applications
3. Run from Applications
```

### For Windows Users

**Method 1: Portable Folder** (No installation)
```bash
cd dist/windows
zip -r ../PDF-Merger-Windows.zip "PDF Merger"
# Share: PDF-Merger-Windows.zip
```

Users:
1. Extract ZIP anywhere
2. Run `PDF Merger.exe`
3. Works immediately, no installation needed

**Method 2: Professional Installer** (After NSIS setup)
```
# Share: dist/PDF-Merger-Installer.exe
Users:
1. Double-click installer
2. Follow prompts
3. Launches from Start Menu
```

## 📋 Distribution Package Checklist

### Before Distributing

- [ ] Test on macOS (minimum macOS 10.13)
- [ ] Test on Windows (test on Windows 10 and Windows 11)
- [ ] Test on fresh system (ensure all dependencies work)
- [ ] Verify file paths work in installer
- [ ] Test uninstall/removal process
- [ ] Check file sizes are reasonable
- [ ] Verify shortcuts work correctly

### Files to Include in Distribution

#### macOS Distribution:
```
📦 PDF-Merger-macOS-v1.0.zip
├── PDF-Merger.dmg (31 MB)
├── INSTALLATION.md
└── README.md
```

#### Windows Portable Distribution:
```
📦 PDF-Merger-Windows-Portable-v1.0.zip
├── PDF Merger/ (84 MB)
│   ├── PDF Merger.exe
│   └── _internal/
├── INSTALLATION.md
└── README.md
```

#### Windows Installer Distribution:
```
📦 PDF-Merger-Windows-Installer-v1.0.zip
├── PDF-Merger-Installer.exe (30-40 MB)
├── INSTALLATION.md
└── README.md
```

## 🔧 Troubleshooting Builds

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "py2app not found"
```bash
pip install py2app
```

### "makensis: command not found"
**Solution:** Install NSIS or skip installer build
- Download: https://nsis.sourceforge.io/
- Or: `choco install nsis` on Windows

### "Unable to read file during NSIS build"
- Ensure `windows-installer.nsi` exists in project root
- Ensure `dist/windows/PDF Merger/` was created by previous build
- Check file paths in NSIS script match actual locations

### "App won't launch after install"
- Check Python environment in venv
- Verify all dependencies in requirements.txt
- Test running `python merge_pdfs.py` from terminal first

## 📊 Build Performance

Typical build times on macOS:

| Build Type | Time | Size |
|-----------|------|------|
| Windows EXE (PyInstaller) | 30-60s | 84 MB |
| Windows Installer (NSIS) | 5-10s | 30-40 MB |
| macOS DMG (py2app) | 120-180s | 31 MB |

## 🔐 Code Signing (Optional)

### macOS Code Signing
```bash
# Sign the app bundle before creating DMG
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  ./dist/PDF\ Merger.app
```

### Windows Code Signing
```bash
# Sign the EXE (requires certificate)
signtool sign /f "certificate.pfx" \
  /p "password" \
  /t "http://timestamp.server" \
  PDF-Merger-Installer.exe
```

Code signing is optional but recommended for professional distribution.

## 📝 Version Management

### Updating Version

1. **Update version in build files:**

`build.py`:
```python
APPVERSION = "1.1"  # Update this
```

`windows-installer.nsi`:
```
!define APPVERSION "1.1"  # Update this
```

`setup.py`:
```python
version='1.1',  # Update this
```

2. **Git tag for release:**
```bash
git tag -a v1.1 -m "Release version 1.1"
git push origin v1.1
```

3. **Build for release:**
```bash
python build.py macos
python build.py windows-installer  # or just windows for portable
```

## 🚀 Automated Builds (GitHub Actions Example)

Create `.github/workflows/build.yml`:

```yaml
name: Build Release

on:
  push:
    tags: v*

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build.py macos
      - uses: actions/upload-artifact@v3
        with:
          name: macos-release
          path: dist/PDF-Merger.dmg

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build.py windows-installer
      - uses: actions/upload-artifact@v3
        with:
          name: windows-release
          path: dist/PDF-Merger-Installer.exe
```

## 📞 Support

For build issues, check:
1. [INSTALLATION.md](INSTALLATION.md) - User installation guide
2. [README.md](README.md) - Project overview
3. Project issues/discussions

---

**Last Updated:** March 2026  
**Version:** 1.0
