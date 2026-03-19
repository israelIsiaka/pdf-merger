# PDF Merger - User & Distribution Guide

Welcome to PDF Merger! This comprehensive guide covers everything you need to know about using and distributing the application.

## 📚 Quick Navigation

- **👥 I'm a User:** See [INSTALLATION.md](INSTALLATION.md)
- **🛠️ I'm a Developer:** See [BUILD_GUIDE.md](BUILD_GUIDE.md)
- **📖 I'm a Contributor:** See [README.md](README.md)

---

## 🎯 What is PDF Merger?

PDF Merger is a fast, professional PDF merging application with:

✅ **Simple & Intuitive UI** - Modern, user-friendly interface  
✅ **Drag & Drop Support** - Easily add and reorder PDFs  
✅ **Cross-Platform** - Works on macOS and Windows  
✅ **Fast & Efficient** - Merge multiple PDFs in seconds  
✅ **No Installation Required** - Portable version available  
✅ **Offline Only** - All processing happens on your computer  

---

## 👥 For End Users

### Installation

See [INSTALLATION.md](INSTALLATION.md) for:
- System requirements
- Step-by-step installation for macOS
- Step-by-step installation for Windows
- Troubleshooting guide
- Advanced features and keyboard shortcuts

### Quick Start

1. **Launch** PDF Merger
2. **Add Files** using "Add Files" button or drag & drop
3. **Reorder** files if needed
4. **Merge** by clicking the Merge button
5. **Save** your merged PDF to a new file

### Common Questions

**Q: Is my data secure?**  
A: Yes! PDF Merger runs entirely offline on your computer. PDFs are processed locally and never sent anywhere.

**Q: How many PDFs can I merge?**  
A: Theoretically unlimited, though performance may slow with 100+ files.

**Q: Can I undo after merging?**  
A: Your original PDFs are never deleted - you can always merge again with different files.

**Q: What about password-protected PDFs?**  
A: Remove the password first using another tool, then merge with PDF Merger.

---

## 🛠️ For Developers & Packagers

### Building from Source

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for:
- Build prerequisites and setup
- Building macOS .dmg installer
- Building Windows portable folder or installer
- **Cross-platform building** (build Windows on macOS, macOS on Windows)
- Distribution methods and packaging
- Troubleshooting build issues
- Automated CI/CD integration

### Quick Build

```bash
# Setup
cd /Users/user/pdf-merger
source .venv/bin/activate
pip install -r requirements.txt

# Build for your platform
python build.py macos          # macOS .dmg
python build.py windows        # Windows portable
python build.py windows-installer  # Windows with NSIS
```

### Development Setup

```bash
git clone https://github.com/yourusername/pdf-merger
cd pdf-merger
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python merge_pdfs.py  # Run directly for development
```

### Project Structure

```
pdf-merger/
├── src/                    # Core application
│   ├── app.py             # Main UI (Tkinter)
│   ├── merger.py          # PDF logic
│   ├── theme.py           # Theme system
│   ├── utils.py           # Utilities
│   └── __init__.py
├── build.py               # Build script
├── build.sh               # macOS build convenience
├── build-windows.bat      # Windows build convenience
├── setup.py               # macOS packaging config
├── windows-installer.nsi  # Windows installer config
└── INSTALLATION.md        # User installation guide
```

### Contributing

To contribute improvements:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Test thoroughly (run `python merge_pdfs.py`)
5. Test after building (run built application)
6. Commit with clear messages
7. Push and create a Pull Request

### Code Quality

- Keep functions focused and simple
- Comment complex logic
- Follow PEP 8 style guide
- Test on both macOS and Windows
- Ensure no dependencies are added without updating requirements.txt

---

## 📦 Distribution Checklist

Before distributing to users, ensure:

### Testing ✓
- [ ] Application launches successfully
- [ ] Can add files with "Add Files" button
- [ ] Can drag & drop files
- [ ] Can reorder files
- [ ] Can remove files
- [ ] Merge produces valid PDF
- [ ] Different file sizes work (small and large PDFs)
- [ ] File paths with spaces work
- [ ] Works on actual target OS

### Packaging ✓
- [ ] Version number is updated
- [ ] INSTALLATION.md is complete
- [ ] All dependencies are bundled
- [ ] No personal files included
- [ ] Installer size is reasonable

### Distribution ✓
- [ ] Create release notes
- [ ] Upload to distribution platform
- [ ] Test download works
- [ ] Provide clear installation instructions
- [ ] Respond to user questions/issues

---

## 🔗 Distribution Platforms

### GitHub Releases (Free)
```bash
# Tag your release
git tag -a v1.0 -m "Release version 1.0"
git push origin v1.0

# Upload built files to GitHub Releases page
# Users can download from: github.com/youruser/pdf-merger/releases
```

### Alternative Distribution
- **macOS App Store** - For maximum reach on macOS
- **Windows Store** - For maximum reach on Windows  
- **Direct Download** - Web server or CDN
- **Package Managers** - Homebrew (macOS), Chocolatey (Windows)

---

## 📊 Application Statistics

### Current Version
- **Version:** 1.0
- **Release Date:** March 2026
- **macOS Size:** 31 MB (DMG)
- **Windows Size:** 84 MB (Portable), 35 MB (Installer)

### Technologies Used
- **Language:** Python 3.11+
- **GUI:** Tkinter (cross-platform)
- **PDF Library:** pypdf
- **Image Processing:** Pillow
- **Packaging:** py2app (macOS), PyInstaller (Windows), NSIS (Installer)

### Supported Platforms
- macOS 10.13+ (Intel & Apple Silicon)
- Windows 10+ (64-bit)
- Linux (code compatible, build on Linux)

---

## 🆘 Support & Issues

### Getting Help

1. **Check [INSTALLATION.md](INSTALLATION.md)** - Covers most common issues
2. **Check [BUILD_GUIDE.md](BUILD_GUIDE.md)** - Build-specific help
3. **Review [README.md](README.md)** - Project overview
4. **Open an issue** on GitHub with:
   - OS and version
   - What you were trying to do
   - Exact error message (if any)
   - Steps to reproduce the issue

### Reporting Issues

Include:
```
OS: [macOS 14.3 / Windows 11 / Linux]
Architecture: [Intel / Apple Silicon / x86_64]
App Version: [1.0]
Issue: [Description of problem]
Steps to Reproduce:
1. ...
2. ...
Expected: [What should happen]
Actual: [What actually happened]
```

---

## 📝 License

PDF Merger is provided as-is for personal and commercial use.

### Components
- **PDF Processing:** pypdf (Apache 2.0 License)
- **Image Processing:** Pillow (PIL Software License)
- **UI Framework:** Tkinter (Python License)
- **Installer (Windows):** NSIS (Zlib License)

See individual packages for their specific license terms.

---

## 🔄 Version History

### v1.0 (March 2026) - Initial Release
- ✅ Core PDF merging functionality
- ✅ Professional UI with platform-native styling
- ✅ macOS DMG installer
- ✅ Windows portable and NSIS installer
- ✅ Drag & drop support
- ✅ File reordering
- ✅ Dark/light mode support

### Future Enhancements
- 📋 Batch processing
- 🔐 Password protection for merged PDFs
- 📄 PDF splitting functionality
- 🌐 Linux AppImage distribution
- ⚙️ Advanced merging options (rotation, compression)

---

## 🙏 Acknowledgments

PDF Merger uses these excellent open-source projects:
- **Python** - Programming language
- **Tkinter** - GUI framework  
- **pypdf** - PDF processing
- **Pillow** - Image handling
- **NSIS** - Windows installer creation

Thank you to all contributors and users!

---

**Last Updated:** March 2026  
**Latest Version:** 1.0  
**Repository:** https://github.com/yourusername/pdf-merger  
**License:** Free for personal and commercial use

---

## Quick Links

- 📥 [Installation Guide](INSTALLATION.md)
- 🛠️ [Build Instructions](BUILD_GUIDE.md)  
- 📖 [Project README](README.md)
- 🐛 [Report Issues](https://github.com/yourusername/pdf-merger/issues)
- ⭐ [Star on GitHub](https://github.com/yourusername/pdf-merger)
