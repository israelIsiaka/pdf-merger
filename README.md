# PDF Merger

A powerful, offline PDF processing desktop app for Mac and Windows.

## Features

- **Merge** — Combine multiple PDFs into one
- **Protect** — Add passwords and encryption
- **Compress** — Reduce file size while preserving quality
- **Split** — Extract specific pages or ranges
- **Watermark** — Add text or image watermarks
- **Convert** — PDF ↔ Word, PDF → Images, Images → PDF
- **View** — Built-in PDF viewer
- **Sign/Annotate** — Add signatures and drawings
- **100% Offline** — No uploads, no internet needed

## Installation

- **macOS**: Download `PDF-Merger.dmg` and drag to Applications
- **Windows**: Download `PDF-Merger-Installer.exe` and run it

See [INSTALLATION.md](INSTALLATION.md) for detailed instructions.

## Windows Users: Getting "Python DLL" Error?

If you see: `Failed to load Python DLL 'C:\Program Files\PDF Merger_internal\python311.dll'`

**[See WINDOWS_DLL_FIX.md](WINDOWS_DLL_FIX.md) for the fix** (usually just requires installing Visual C++ Redistributable)

## Documentation

- [Installation Guide](INSTALLATION.md) — Detailed setup for macOS & Windows
- [Windows DLL Error Fix](WINDOWS_DLL_FIX.md) — Troubleshooting startup errors
- [Building Guide](BUILD_GUIDE.md) — Build from source
- [Cross-Platform Build](CROSS_PLATFORM_BUILD.md) — Build for other platforms
- [Running Guide](RUNNING.md) — Run development version

## Run from Source

```bash
# Clone and setup
git clone https://github.com/israelIsiaka/pdf-merger.git
cd pdf-merger
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run the app
python -m src.app
```

## Build Standalone App

```bash
pip install nuitka pyinstaller

# Build for your platform
python build.py           # Linux/Windows/macOS (auto-detect, uses Nuitka)
python build.py macos     # macOS DMG
python build.py windows   # Windows (folder + installer)
