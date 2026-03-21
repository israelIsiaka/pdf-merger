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
        # PyQt6 sub-modules are not always auto-detected on Windows
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=pypdf",
        "--collect-all=PyQt6",
        f"--distpath={os.path.join(DIST_DIR, 'windows')}",
        f"--workpath={os.path.join(BUILD_DIR, 'windows')}",
        f"--specpath={os.path.join(BUILD_DIR, 'windows')}",
        "merge_pdfs.py",
    ]

    # Bundle whichever logo files exist so _load_icon() can find them at runtime
    if os.path.exists(ico_path):
        cmd.insert(-1, "--add-data")
        cmd.insert(-1, f"{ico_path}{os.pathsep}.")
    if os.path.exists(png_path):
        cmd.insert(-1, "--add-data")
        cmd.insert(-1, f"{png_path}{os.pathsep}.")

    # Prefer ICO for the EXE icon; fall back to PNG (requires Pillow installed)
    if os.path.exists(ico_path):
        cmd.insert(-1, f"--icon={ico_path}")
    elif os.path.exists(png_path):
        cmd.insert(-1, f"--icon={png_path}")

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
    """Build macOS app bundle using PyInstaller, then package as DMG."""
    print("Building PDF Merger macOS Application (.dmg)...")

    icns_path = os.path.join(PROJECT_DIR, "Logo.icns")
    png_path  = os.path.join(PROJECT_DIR, "Logo.png")
    src_data  = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PDF Merger",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--add-data", src_data,
        "--add-data", f"{png_path}{os.pathsep}.",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=pypdf",
        "--collect-all=PyQt6",
        f"--distpath={os.path.join(DIST_DIR, 'macos')}",
        f"--workpath={os.path.join(BUILD_DIR, 'macos')}",
        f"--specpath={os.path.join(BUILD_DIR, 'macos')}",
        "merge_pdfs.py",
    ]

    # Prefer ICNS for macOS, fall back to PNG
    if os.path.exists(icns_path):
        cmd.insert(-1, f"--icon={icns_path}")
    elif os.path.exists(png_path):
        cmd.insert(-1, f"--icon={png_path}")

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("FAILED to build app bundle")
        return False

    app_path = os.path.join(DIST_DIR, "macos", "PDF Merger.app")
    dmg_path = os.path.join(DIST_DIR, "PDF-Merger.dmg")

    print("App bundle created")
    print("Creating DMG installer...")

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


def build_linux():
    """Build Linux application using PyInstaller."""
    print("Building PDF Merger Linux Application...")

    png_path = os.path.join(PROJECT_DIR, "Logo.png")
    src_data = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PDF Merger",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--add-data", src_data,
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=pypdf",
        "--collect-all=PyQt6",
        f"--distpath={os.path.join(DIST_DIR, 'linux')}",
        f"--workpath={os.path.join(BUILD_DIR, 'linux')}",
        f"--specpath={os.path.join(BUILD_DIR, 'linux')}",
        "merge_pdfs.py",
    ]

    if os.path.exists(png_path):
        idx = cmd.index("merge_pdfs.py")
        cmd[idx:idx] = ["--add-data", f"{png_path}{os.pathsep}.", f"--icon={png_path}"]

    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        output_dir = os.path.join(DIST_DIR, "linux", "PDF Merger")
        if os.path.exists(output_dir):
            print("Linux build created successfully")
            print("")
            print("=" * 40)
            print("Build Complete!")
            print("=" * 40)
            print("")
            print(f"Output location: {output_dir}")
            print("")
            print("Distribution for Linux:")
            print("   1. Direct folder: Share the 'PDF Merger' folder")
            print("   2. TAR: Compress the dist/linux/ folder")
            print("")
            return True

    print("FAILED to create Linux build")
    return False


def detect_and_build():
    """Detect platform and build appropriate binary."""
    system = platform.system()
    print(f"Detected platform: {system}")

    if system == "Windows":
        return build_windows_exe()
    elif system == "Darwin":
        return build_macos_dmg()
    elif system == "Linux":
        return build_linux()
    else:
        print("ERROR: Unsupported platform for automated building")
        print("Use: python build.py windows  OR  python build.py macos  OR  python build.py linux")
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
        elif target == "linux":
            success = build_linux()
        else:
            print(f"ERROR: Unknown target: {target}")
            print("Usage: python build.py [windows|windows-installer|macos|linux]")
            print("")
            print("  windows           - Create portable Windows folder")
            print("  windows-installer - Create Windows installer (.exe) with NSIS")
            print("  macos             - Create macOS .dmg installer")
            print("  linux             - Create portable Linux folder")
            success = False
    else:
        success = detect_and_build()

    sys.exit(0 if success else 1)
