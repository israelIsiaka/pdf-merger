#!/usr/bin/env python3
"""
Build script for PDF Merger
Creates Windows EXE, macOS DMG, or Linux AppImage
Usage:
    python build.py windows  # Create Windows EXE
    python build.py macos    # Create macOS DMG
    python build.py          # Auto-detect platform
"""

import os
import sys
import shutil
import subprocess
import platform

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")


def clean_builds():
    """Remove previous build artifacts."""
    print("Cleaning previous builds...")
    for directory in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    for file in os.listdir(PROJECT_DIR):
        if file.endswith(".spec"):
            os.remove(os.path.join(PROJECT_DIR, file))


def build_windows_exe():
    """Build Windows EXE using PyInstaller."""
    print("Building PDF Merger Windows Application (.exe)...")

    # Note: must be run ON Windows to produce a valid .exe
    ico_path = os.path.join(PROJECT_DIR, "Logo.ico")
    png_path = os.path.join(PROJECT_DIR, "Logo.png")
    # Use absolute source path so PyInstaller doesn't resolve it relative to --specpath
    src_data = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PDF Merger",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--add-data", src_data,
        # Bundle logo files so _load_icon() can find them at runtime via sys._MEIPASS
        "--add-data", f"{ico_path}{os.pathsep}.",
        "--add-data", f"{png_path}{os.pathsep}.",
        # tkinter sub-modules are not always auto-detected on Windows
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageTk",
        "--hidden-import=pypdf",
        "--collect-all=PIL",
        f"--distpath={os.path.join(DIST_DIR, 'windows')}",
        f"--workpath={os.path.join(BUILD_DIR, 'windows')}",
        f"--specpath={os.path.join(BUILD_DIR, 'windows')}",
        "merge_pdfs.py",
    ]

    if os.path.exists(ico_path):
        cmd.insert(-1, f"--icon={ico_path}")

    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        output_dir = os.path.join(DIST_DIR, "windows", "PDF Merger")
        if os.path.exists(output_dir):
            print("EXE created successfully")
            print("")
            print("=" * 40)
            print("Build Complete!")
            print("=" * 40)
            print("")
            print(f"EXE location: {output_dir}")
            print("")
            print("Distribution for Windows:")
            print("   1. Direct folder: Share the 'PDF Merger' folder")
            print("   2. ZIP: Compress the dist/windows/ folder")
            print("")
            return True

    print("FAILED to create EXE")
    return False


def build_windows_installer():
    """Build Windows installer using NSIS."""
    print("Building PDF Merger Windows Installer (.exe)...")

    try:
        result = subprocess.run(["makensis", "/version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("WARNING: NSIS not found. Download from: https://nsis.sourceforge.io/")
        print("   Or install via: choco install nsis")
        print("   Alternatively, use the portable folder distribution.")
        return False

    nsi_path = os.path.join(PROJECT_DIR, "windows-installer.nsi")
    if not os.path.exists(nsi_path):
        print(f"ERROR: NSIS script not found: {nsi_path}")
        return False

    cmd = ["makensis", "/DOUTDIR=dist", nsi_path]
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        installer_path = os.path.join(DIST_DIR, "PDF-Merger-Installer.exe")
        if os.path.exists(installer_path):
            print("Installer created successfully")
            print("")
            print("=" * 40)
            print("Build Complete!")
            print("=" * 40)
            print("")
            print(f"Installer location: {installer_path}")
            print("")
            return True

    print("FAILED to create installer")
    return False


def build_macos_dmg():
    """Build macOS DMG using py2app."""
    print("Building PDF Merger macOS Application (.dmg)...")

    cmd = [sys.executable, "setup.py", "py2app"]
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        print("App bundle created")
        print("Creating DMG installer...")

        dmg_path = os.path.join(DIST_DIR, "PDF-Merger.dmg")
        app_path = os.path.join(DIST_DIR, "PDF Merger.app")

        cmd = [
            "hdiutil", "create",
            "-volname", "PDF Merger",
            "-srcfolder", app_path,
            "-ov", "-format", "UDZO",
            dmg_path,
        ]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("DMG created successfully")
            print("")
            print("=" * 40)
            print("Build Complete!")
            print("=" * 40)
            print("")
            print(f"DMG location: {dmg_path}")
            print("")
            print("Distribution for macOS:")
            print("   1. Direct DMG: Users download and drag app to Applications")
            print("   2. Direct App: Copy 'PDF Merger.app' folder")
            print("")
            return True

    print("FAILED to create DMG")
    return False


def detect_and_build():
    """Detect platform and build appropriate binary."""
    system = platform.system()
    print(f"Detected platform: {system}")

    if system == "Windows":
        return build_windows_exe()
    elif system == "Darwin":
        return build_macos_dmg()
    else:
        print("ERROR: Unsupported platform for automated building")
        print("Use: python build.py windows  OR  python build.py macos")
        return False


if __name__ == "__main__":
    clean_builds()

    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target == "windows":
            success = build_windows_exe()
        elif target == "windows-installer":
            success = build_windows_exe()
            if success:
                success = build_windows_installer()
        elif target == "macos":
            success = build_macos_dmg()
        else:
            print(f"ERROR: Unknown target: {target}")
            print("Usage: python build.py [windows|windows-installer|macos]")
            print("")
            print("  windows           - Create portable Windows folder")
            print("  windows-installer - Create Windows installer (.exe) with NSIS")
            print("  macos             - Create macOS .dmg installer")
            success = False
    else:
        success = detect_and_build()

    sys.exit(0 if success else 1)
