#!/usr/bin/env python3
"""
Build script for PDF Merger.

Default builder: Nuitka  — compiles Python to C then to native machine code.
  No .pyc files in the output. License/activation code is fully opaque.
  Significantly harder to reverse-engineer than PyInstaller.

Fallback builder: PyInstaller — faster builds, .pyc files present.

Usage:
    python build.py                      # auto-detect platform, use Nuitka
    python build.py macos                # macOS DMG via Nuitka
    python build.py windows              # Windows EXE via Nuitka
    python build.py linux                # Linux binary via Nuitka
    python build.py macos --pyinstaller  # fall back to PyInstaller
    python build.py windows-installer    # Windows NSIS installer (after EXE)

Requirements:
    pip install nuitka pyinstaller ordered-set zstandard  # zstandard = faster Nuitka compression
"""

import os
import sys
import shutil
import subprocess
import platform

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR    = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR   = os.path.join(PROJECT_DIR, "build")


# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_builds():
    """Remove previous build artifacts."""
    print("Cleaning previous builds...")
    for directory in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    for f in os.listdir(PROJECT_DIR):
        if f.endswith(".spec"):
            os.remove(os.path.join(PROJECT_DIR, f))


def _run(cmd: list, cwd=None) -> bool:
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR)
    return result.returncode == 0


def _print_success(label: str, location: str, notes: list[str]):
    print("")
    print("=" * 48)
    print(f"Build Complete!  [{label}]")
    print("=" * 48)
    print(f"Output: {location}")
    for note in notes:
        print(f"  {note}")
    print("")


# ── Nuitka builds ─────────────────────────────────────────────────────────────
#
# Nuitka compiles every .py file to a C extension (.pyd / .so).
# The result is a native binary — no Python bytecode files in the bundle.
# The license verification module becomes unreadable compiled C.
#
# Key flags:
#   --standalone          include all dependencies, no system Python needed
#   --onefile             single self-extracting executable (simpler distribution)
#   --enable-plugin=pyqt6 auto-handle PyQt6 Qt platform plugins & DLLs
#   --follow-imports      compile all imported packages, not just the entry point
#   --windows-disable-console / --macos-app-mode=windowed  — no terminal window
#   --include-package=src  ensure the whole src/ package is compiled in
# ──────────────────────────────────────────────────────────────────────────────

def _nuitka_base_cmd(output_dir: str, onefile: bool = True) -> list:
    """Common Nuitka flags shared by all platforms."""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",   # auto-download C compiler on Windows
        "--follow-imports",
        "--enable-plugin=pyqt6",
        "--include-package=src",
        "--include-package=pypdf",
        "--include-package=fitz",
        "--include-package=PIL",
        "--include-package=pdf2docx",
        # Silence informational output; warnings and errors still shown
        "--quiet",
        f"--output-dir={output_dir}",
    ]
    if onefile:
        cmd.append("--onefile")
    return cmd


def build_windows_nuitka() -> bool:
    """Build a single-file Windows EXE using Nuitka."""
    print("Building PDF Merger Windows EXE (Nuitka — native binary)...")

    out_dir  = os.path.join(DIST_DIR, "windows-nuitka")
    ico_path = os.path.join(PROJECT_DIR, "Logo.ico")
    png_path = os.path.join(PROJECT_DIR, "Logo.png")

    cmd = _nuitka_base_cmd(out_dir, onefile=True)
    cmd += [
        "--windows-console-mode=disable",
        "--windows-product-name=PDF Merger",
        "--windows-file-description=PDF Merger",
        "--windows-company-name=PDF Merger",
        "--windows-file-version=1.0.0.0",
        "--windows-product-version=1.0.0.0",
    ]
    if os.path.exists(ico_path):
        cmd.append(f"--windows-icon-from-ico={ico_path}")
    elif os.path.exists(png_path):
        cmd.append(f"--windows-icon-from-ico={png_path}")

    # Bundle logo files so _load_icon() finds them at runtime
    for asset in (ico_path, png_path):
        if os.path.exists(asset):
            cmd.append(f"--include-data-files={asset}={os.path.basename(asset)}")

    cmd.append("merge_pdfs.py")

    if not _run(cmd):
        print("FAILED — Nuitka build error (see output above)")
        return False

    exe = os.path.join(out_dir, "merge_pdfs.exe")
    if not os.path.exists(exe):
        # Nuitka may use the script stem; search for any .exe
        for f in os.listdir(out_dir):
            if f.endswith(".exe"):
                exe = os.path.join(out_dir, f)
                break

    final = os.path.join(out_dir, "PDF Merger.exe")
    if os.path.exists(exe) and exe != final:
        os.rename(exe, final)

    _print_success("Windows / Nuitka", final, [
        "Single .exe — no Python installed on target needed",
        "Contains no .pyc files — compiled to native C",
    ])
    return True


def build_macos_nuitka() -> bool:
    """Build a macOS DMG using PyInstaller.

    Nuitka explicitly blocks PyQt6 on macOS (as of Nuitka 2.x) and recommends
    PySide6 instead.  Since the entire codebase targets PyQt6 we use
    PyInstaller for macOS — it produces a fully standalone .app bundle.
    """
    print("Building PDF Merger macOS App (PyInstaller — PyQt6/macOS)...")
    return build_macos_dmg()


def build_linux_nuitka() -> bool:
    """Build a single-file Linux binary using Nuitka."""
    print("Building PDF Merger Linux binary (Nuitka — native binary)...")

    out_dir  = os.path.join(DIST_DIR, "linux-nuitka")
    png_path = os.path.join(PROJECT_DIR, "Logo.png")

    cmd = _nuitka_base_cmd(out_dir, onefile=True)
    if os.path.exists(png_path):
        cmd.append(f"--linux-icon={png_path}")
        cmd.append(f"--include-data-files={png_path}={os.path.basename(png_path)}")

    cmd.append("merge_pdfs.py")

    if not _run(cmd):
        print("FAILED — Nuitka build error (see output above)")
        return False

    binary = os.path.join(out_dir, "merge_pdfs.bin")
    if not os.path.exists(binary):
        for f in os.listdir(out_dir):
            if not f.endswith((".so", ".py", ".dist")):
                candidate = os.path.join(out_dir, f)
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    binary = candidate
                    break

    final = os.path.join(out_dir, "pdf-merger")
    if os.path.exists(binary) and binary != final:
        os.rename(binary, final)

    _print_success("Linux / Nuitka", final, [
        "Single binary — chmod +x pdf-merger then run it directly",
        "No Python required on target machine",
    ])
    return True


# ── PyInstaller builds (fallback) ─────────────────────────────────────────────

_PYINSTALLER_COMMON = [
    "--windowed", "--noconfirm",
    "--strip", "--log-level", "WARN",
    "--hidden-import=PyQt6",
    "--hidden-import=PyQt6.QtWidgets",
    "--hidden-import=PyQt6.QtCore",
    "--hidden-import=PyQt6.QtGui",
    "--hidden-import=pypdf",
    "--hidden-import=fitz",
    "--hidden-import=fitz._fitz",
    "--hidden-import=PIL",
    "--hidden-import=PIL._imaging",
    "--collect-all=PyQt6",
    "--collect-all=fitz",
    "--collect-all=PIL",
]


def build_windows_exe() -> bool:
    """Build a single-file Windows EXE using PyInstaller.

    Uses --onefile so the user gets one .exe to download and run directly.
    This avoids the _internal/python3xx.dll 'Access denied' error that
    occurs with --onedir builds when Windows memory integrity is enabled.
    """
    print("Building PDF Merger Windows EXE (PyInstaller — single file)...")

    ico_path = os.path.join(PROJECT_DIR, "Logo.ico")
    png_path = os.path.join(PROJECT_DIR, "Logo.png")
    src_data = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [sys.executable, "-m", "PyInstaller",
           "--name", "PDF Merger",
           "--onefile",               # single .exe — no _internal folder
           ] + _PYINSTALLER_COMMON + [
        "--add-data", src_data,
        f"--distpath={os.path.join(DIST_DIR, 'windows')}",
        f"--workpath={os.path.join(BUILD_DIR, 'windows')}",
        f"--specpath={os.path.join(BUILD_DIR, 'windows')}",
        "merge_pdfs.py",
    ]
    for asset in (ico_path, png_path):
        if os.path.exists(asset):
            cmd.insert(-1, "--add-data")
            cmd.insert(-1, f"{asset}{os.pathsep}.")
    if os.path.exists(ico_path):
        cmd.insert(-1, f"--icon={ico_path}")
    elif os.path.exists(png_path):
        cmd.insert(-1, f"--icon={png_path}")

    if not _run(cmd):
        print("FAILED to create EXE")
        return False

    out = os.path.join(DIST_DIR, "windows", "PDF Merger.exe")
    _print_success("Windows / PyInstaller", out, [
        "Single .exe — users download and double-click, no install needed",
    ])
    return True


def build_windows_installer() -> bool:
    """Build Windows installer using NSIS."""
    print("Building PDF Merger Windows Installer (.exe)...")
    try:
        r = subprocess.run(["makensis", "/version"], capture_output=True, timeout=5)
        if r.returncode != 0:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("WARNING: NSIS not found. Install from https://nsis.sourceforge.io/")
        return False

    nsi = os.path.join(PROJECT_DIR, "windows-installer.nsi")
    if not os.path.exists(nsi):
        print(f"ERROR: NSIS script not found: {nsi}")
        return False

    if not _run(["makensis", "/DOUTDIR=dist", nsi]):
        print("FAILED to create installer")
        return False

    installer = os.path.join(DIST_DIR, "PDF-Merger-Installer.exe")
    _print_success("Windows Installer", installer, [])
    return True


def build_macos_dmg() -> bool:
    """Build macOS DMG using PyInstaller (fallback — contains .pyc files)."""
    print("Building PDF Merger macOS Application (PyInstaller)...")
    print("NOTE: Use Nuitka build for maximum protection against reverse engineering.")

    icns_path = os.path.join(PROJECT_DIR, "Logo.icns")
    png_path  = os.path.join(PROJECT_DIR, "Logo.png")
    src_data  = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [sys.executable, "-m", "PyInstaller",
           "--name", "PDF Merger",
           "--onedir",               # .app bundle requires onedir
           ] + _PYINSTALLER_COMMON + [
        "--add-data", src_data,
        "--add-data", f"{png_path}{os.pathsep}.",
        f"--distpath={os.path.join(DIST_DIR, 'macos')}",
        f"--workpath={os.path.join(BUILD_DIR, 'macos')}",
        f"--specpath={os.path.join(BUILD_DIR, 'macos')}",
        "merge_pdfs.py",
    ]
    if os.path.exists(icns_path):
        cmd.insert(-1, f"--icon={icns_path}")
    elif os.path.exists(png_path):
        cmd.insert(-1, f"--icon={png_path}")

    if not _run(cmd):
        print("FAILED to build app bundle")
        return False

    app_path    = os.path.join(DIST_DIR, "macos", "PDF Merger.app")
    dmg_path    = os.path.join(DIST_DIR, "PDF-Merger.dmg")
    staging_dir = os.path.join(DIST_DIR, "dmg-staging")

    # Ad-hoc code sign — prevents "damaged app" error on first launch
    if not _run(["codesign", "--force", "--deep", "--sign", "-", app_path]):
        print("WARNING: Code signing failed — app may trigger Gatekeeper warnings")

    # Build installer DMG: staging dir holds .app + /Applications symlink
    # so users see the standard drag-to-install experience.
    print("Creating installer DMG...")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir)
    shutil.copytree(app_path, os.path.join(staging_dir, "PDF Merger.app"))
    os.symlink("/Applications", os.path.join(staging_dir, "Applications"))

    try:
        if not _run([
            "hdiutil", "create",
            "-volname", "PDF Merger",
            "-srcfolder", staging_dir,
            "-ov", "-format", "UDZO",
            dmg_path,
        ]):
            print("FAILED to create DMG")
            return False
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    _print_success("macOS / PyInstaller", dmg_path, [
        "Drag PDF Merger.app to Applications to install",
    ])
    return True


def build_linux() -> bool:
    """Build a single-file Linux binary using PyInstaller."""
    print("Building PDF Merger Linux binary (PyInstaller — single file)...")

    png_path = os.path.join(PROJECT_DIR, "Logo.png")
    src_data = f"{os.path.join(PROJECT_DIR, 'src')}{os.pathsep}src"

    cmd = [sys.executable, "-m", "PyInstaller",
           "--name", "pdf-merger",
           "--onefile",              # single binary — no folder needed
           ] + _PYINSTALLER_COMMON + [
        "--add-data", src_data,
        f"--distpath={os.path.join(DIST_DIR, 'linux')}",
        f"--workpath={os.path.join(BUILD_DIR, 'linux')}",
        f"--specpath={os.path.join(BUILD_DIR, 'linux')}",
        "merge_pdfs.py",
    ]
    if os.path.exists(png_path):
        idx = cmd.index("merge_pdfs.py")
        cmd[idx:idx] = ["--add-data", f"{png_path}{os.pathsep}.", f"--icon={png_path}"]

    if not _run(cmd):
        print("FAILED to create Linux build")
        return False

    binary = os.path.join(DIST_DIR, "linux", "pdf-merger")
    # Ensure executable bit is set
    if os.path.exists(binary):
        os.chmod(binary, 0o755)

    _print_success("Linux / PyInstaller", binary, [
        "Single binary — chmod +x pdf-merger then run it directly",
    ])
    return True


# ── Dispatch ──────────────────────────────────────────────────────────────────

def detect_and_build(use_nuitka: bool = True) -> bool:
    system = platform.system()
    print(f"Detected platform: {system}")
    if system == "Windows":
        return build_windows_nuitka() if use_nuitka else build_windows_exe()
    elif system == "Darwin":
        return build_macos_nuitka() if use_nuitka else build_macos_dmg()
    elif system == "Linux":
        return build_linux_nuitka() if use_nuitka else build_linux()
    print("ERROR: Unsupported platform.")
    return False


if __name__ == "__main__":
    clean_builds()

    args        = sys.argv[1:]
    use_nuitka  = "--pyinstaller" not in args
    targets     = [a for a in args if not a.startswith("--")]
    target      = targets[0].lower() if targets else None

    if target is None:
        success = detect_and_build(use_nuitka)

    elif target == "windows":
        success = build_windows_nuitka() if use_nuitka else build_windows_exe()

    elif target == "windows-installer":
        success = (build_windows_nuitka() if use_nuitka else build_windows_exe())
        if success:
            success = build_windows_installer()

    elif target == "macos":
        success = build_macos_nuitka() if use_nuitka else build_macos_dmg()

    elif target == "linux":
        success = build_linux_nuitka() if use_nuitka else build_linux()

    else:
        print(f"ERROR: Unknown target: {target}")
        print("")
        print("Usage: python build.py [target] [--pyinstaller]")
        print("")
        print("  (no target)          Auto-detect platform, Nuitka build")
        print("  windows              Windows EXE  (Nuitka by default)")
        print("  windows-installer    Windows EXE + NSIS installer")
        print("  macos                macOS DMG    (Nuitka by default)")
        print("  linux                Linux binary (Nuitka by default)")
        print("")
        print("  --pyinstaller        Use PyInstaller instead of Nuitka")
        print("                       (faster build, but .pyc files present)")
        success = False

    sys.exit(0 if success else 1)
