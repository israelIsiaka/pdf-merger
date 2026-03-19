# PDF Merger - Quick Reference Card

## 📥 USER INSTALLATION

### macOS
```
1. Download: PDF-Merger.dmg
2. Double-click DMG
3. Drag app to Applications
4. Launch from Applications folder
```

### Windows (Portable - Easy)
```
1. Download: PDF-Merger-Windows.zip
2. Extract anywhere
3. Run: PDF Merger.exe
4. No installation needed!
```

### Windows (Installer - Professional)
```
1. Download: PDF-Merger-Installer.exe
2. Run installer
3. Follow prompts
4. Launch from Start Menu
```

---

## 🚀 QUICK START (All Platforms)

1. **Add Files**: Click "Add Files" or drag PDFs into window
2. **Reorder**: Click "Move Up/Down" or drag in list
3. **Remove**: Select file and press Delete
4. **Merge**: Click "Merge PDFs" button
5. **Save**: Choose location for output file

---

## ⌨️ KEYBOARD SHORTCUTS

| Action | Shortcut |
|--------|----------|
| Add Files | Cmd/Ctrl + O |
| Merge | Cmd/Ctrl + M |
| Move Up | Cmd/Ctrl + ↑ |
| Move Down | Cmd/Ctrl + ↓ |
| Clear List | Cmd/Ctrl + Delete |

---

## 🛠️ DEVELOPER BUILD COMMANDS

### Setup (First Time)
```bash
cd /Users/user/pdf-merger
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

### Build
```bash
# macOS
./build.sh
# or
python build.py macos

# Windows (Portable)
python build.py windows

# Windows (With Installer - requires NSIS)
python build.py windows-installer

# Run directly for testing
python merge_pdfs.py
```

### Cross-Platform Build & Test
```bash
# Build Windows version on macOS, bundle as ZIP
cd /Users/user/pdf-merger && source .venv/bin/activate && \
python build.py windows && cd dist/windows && \
zip -r ../PDF-Merger-Windows-Test.zip "PDF Merger"
# Result: dist/PDF-Merger-Windows-Test.zip (send to Windows PC)

# On Windows: Extract and run
Expand-Archive PDF-Merger-Windows-Test.zip -DestinationPath .
.\"PDF Merger\\PDF Merger.exe"
```

### Output Locations
```
dist/
├── PDF-Merger.dmg           ← macOS installer
├── PDF Merger.app/          ← macOS app bundle
├── PDF-Merger-Installer.exe ← Windows installer
└── windows/
    └── PDF Merger/          ← Windows portable
```

---

## 📋 FILE LOCATIONS

### macOS
- **Install folder**: `/Applications/PDF Merger.app`
- **Remove**: Drag to Trash
- **Settings**: `~/Library/Application Support/PDF Merger/`

### Windows (Installer)
- **Install folder**: `C:\Program Files\PDF Merger\`
- **Remove**: Settings → Programs → Uninstall → PDF Merger
- **Start Menu**: Start → PDF Merger

### Windows (Portable)
- **Run from**: Wherever you extract
- **Remove**: Just delete the folder

---

## 🔧 TROUBLESHOOTING

### Won't Start
```bash
# macOS - Fix permissions
chmod +x /Applications/PDF\ Merger.app/Contents/MacOS/PDF\ Merger

# Windows - Try as Administrator
Right-click → "Run as administrator"
```

### "File Not Found" Error
- Ensure PDFs still exist
- Check file permissions
- Avoid very long file paths

### Slow Performance
- Close other applications
- Try with fewer PDFs
- Check available disk space

### macOS - "Cannot be opened"
1. System Preferences → Security & Privacy
2. Allow PDF Merger to run
3. (Or) Right-click app → Open → Open

---

## 📖 DOCUMENTATION FILES

| File | Purpose |
|------|---------|
| [INSTALLATION.md](INSTALLATION.md) | Complete installation guide for users |
| [BUILD_GUIDE.md](BUILD_GUIDE.md) | Developer build and distribution guide |
| [DISTRIBUTION.md](DISTRIBUTION.md) | Overall distribution and support guide |
| [README.md](README.md) | Project overview and features |

---

## 🌐 SUPPORT

- 📧 GitHub Issues: Report bugs and request features
- 📚 Check guides above before asking
- 🔍 Search existing issues first

---

## 🔒 Privacy & Security

✅ **100% Offline** - No internet connection needed
✅ **Local Processing** - PDFs never leave your computer
✅ **Open Source** - Code is transparent and reviewable
✅ **No Data Collection** - No tracking or analytics

---

## 📦 SYSTEM REQUIREMENTS

### macOS
- **OS**: 10.13+ 
- **Space**: 50 MB
- **RAM**: 512 MB minimum

### Windows
- **OS**: Windows 10+
- **Space**: 100 MB  
- **RAM**: 512 MB minimum

---

## 🎯 COMMON TASKS

### Merge PDFs in Specific Order
1. Add all PDFs
2. Use "Move Up/Down" buttons to reorder
3. Click "Merge PDFs"

### Merge Large Number of PDFs
1. Add first batch
2. Merge
3. Add second batch merged output + more PDFs
4. Merge again
5. Repeat as needed

### Only Merge Some Pages
1. Split PDFs elsewhere first (extract pages you want)
2. Use PDF Merger to combine split PDFs

### Remove a PDF from List
1. Select file in list
2. Press Delete key or click "Remove"

---

**Last Updated**: March 2026  
**Version**: 1.0  
**Website**: https://github.com/yourusername/pdf-merger
