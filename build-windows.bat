@echo off
REM PDF Merger Windows Build Script
REM This script builds the Windows installer for PDF Merger

REM Optional: Install NSIS if not already installed
REM Download from: https://nsis.sourceforge.io/
REM Or: choco install nsis

echo.
echo ════════════════════════════════════════
echo PDF Merger - Windows Build
echo ════════════════════════════════════════
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or newer.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✓ Virtual environment activated
) else (
    echo WARNING: Virtual environment not found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo ✓ Virtual environment created and activated
)

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip pyinstaller >nul 2>&1
pip install -r requirements.txt >nul 2>&1

echo ✓ Dependencies installed
echo.

REM Build options menu
echo Choose build type:
echo  1. Portable folder (no installation required)
echo  2. Professional installer (requires NSIS)
echo  3. Both portable and installer
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Building portable folder...
    python build.py windows
    if errorlevel 1 goto error
    echo.
    echo ✓ Build complete! Check dist\windows\PDF Merger\
    echo.
) else if "%choice%"=="2" (
    echo.
    echo Building professional installer...
    python build.py windows-installer
    if errorlevel 1 goto error
    echo.
    echo ✓ Build complete! Check dist\PDF-Merger-Installer.exe
    echo.
) else if "%choice%"=="3" (
    echo.
    echo Building portable folder...
    python build.py windows
    if errorlevel 1 goto error
    echo.
    echo Building professional installer...
    python build.py windows-installer
    if errorlevel 1 goto error
    echo.
    echo ✓ Both builds complete!
    echo   Portable: dist\windows\PDF Merger\
    echo   Installer: dist\PDF-Merger-Installer.exe
    echo.
) else (
    echo Invalid choice. Exiting.
    goto end
)

echo.
echo Distribution tips:
echo  - Portable: Zip the dist\windows\PDF Merger folder
echo  - Installer: Share PDF-Merger-Installer.exe directly
echo.

goto end

:error
echo.
echo ERROR: Build failed!
echo See messages above for details.
echo.

:end
pause
