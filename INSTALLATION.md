# PDF Merger - Installation Guide

A fast, professional PDF merger application for macOS and Windows with a modern, user-friendly interface.

## 📋 System Requirements

### macOS
- **OS**: macOS 10.13 or newer
- **Architecture**: Intel (x86_64) or Apple Silicon (ARM64)
- **RAM**: 512 MB minimum, 2 GB recommended
- **Disk Space**: 50 MB for installation

### Windows
- **OS**: Windows 10 or newer (64-bit recommended)
- **RAM**: 512 MB minimum, 2 GB recommended
- **Disk Space**: 100 MB for installation
- **.NET Framework**: Not required (fully standalone)

## 🍎 macOS Installation

### Method 1: Using the DMG Installer (Recommended)

1. **Download** the `PDF-Merger.dmg` file
2. **Double-click** the DMG file to mount it
3. **Drag** the "PDF Merger" app to your Applications folder
4. **Eject** the DMG (after copying completes)
5. **Launch** the app from Applications folder or Spotlight (Cmd+Space, type "PDF Merger")

### Method 2: Command Line Installation

```bash
# Mount the DMG
hdiutil mount PDF-Merger.dmg

# Copy to Applications
cp -r "/Volumes/PDF Merger/PDF Merger.app" /Applications/

# Eject
hdiutil eject "/Volumes/PDF Merger"

# Run
open /Applications/PDF\ Merger.app
```

### First Launch on macOS

If you see "PDF Merger cannot be opened because the developer cannot be verified":

1. **Open System Preferences** → **Security & Privacy**
2. **Click Lock** icon to unlock
3. **Find PDF Merger** in the "Allow apps from..." list
4. **Click "Allow Anyway"**
5. **Alternatively**: Right-click the app, select "Open", then "Open" again

This is normal for apps not signed with an Apple Developer certificate. It's a security feature, not an error.

---

## 🪟 Windows Installation

### Method 0: Testing on macOS-Built Version

If you received a ZIP file built on macOS:

1. **Extract the ZIP**
   ```powershell
   Expand-Archive PDF-Merger-Windows-Test.zip -DestinationPath .
   ```

2. **Run the application**
   ```powershell
   .\"PDF Merger\\PDF Merger.exe"
   ```

3. **First Run (if Windows security warning appears)**
   - Click "More info"
   - Click "Run anyway"
   - This is normal for apps not signed with Microsoft certificates

4. **After Testing**
   - If it works, all good! The app is compatible
   - If issues occur, let the developer know
   - You can delete the folder anytime (no installation)

**Note:** This is a test/portable version. No installation or uninstall needed - just delete the folder.

---

### Method 1: Using the Installer (Recommended)

1. **Download** the `PDF-Merger-Installer.exe` file
2. **Double-click** to run the installer
3. **Follow** the on-screen prompts
4. **Select** an installation location (default: `C:\Program Files\PDF Merger`)
5. **Complete** the installation
6. **Launch** from Start Menu or Desktop shortcut

### Method 2: Portable Folder (No Installation Needed)

1. **Download** the `PDF-Merger-Windows.zip` file
2. **Extract** anywhere on your computer
3. **Open** the extracted folder
4. **Double-click** `PDF Merger.exe` to run

### Method 3: Command Line

```bash
# Using installer
PDF-Merger-Installer.exe /S /D=C:\Program Files\PDF Merger

# Running portable version
.\PDF\ Merger\PDF\ Merger.exe
```

---

## 🚀 Quick Start

### Using PDF Merger

1. **Launch** the application
2. **Add Files**:
   - Click "Add Files" button to select individual PDF files
   - Or drag & drop PDFs directly into the app
   - Or use "Add Folder" to include all PDFs in a folder
3. **Reorder** (if needed):
   - Click "Move Up" or "Move Down" to change page order
   - Or drag files in the list
4. **Remove Files**:
   - Select a file and click "Remove" or press Delete
5. **Merge**:
   - Click the large "Merge PDFs" button
   - Choose output location and filename
   - Wait for completion (progress bar shows status)
6. **View Result**:
   - Merged PDF opens automatically in your default PDF viewer

---

## 🔧 Troubleshooting

### Application Won't Start

**macOS:**
```bash
# Check if app has execute permissions
chmod +x /Applications/PDF\ Merger.app/Contents/MacOS/PDF\ Merger

# Run from Terminal for error messages
/Applications/PDF\ Merger.app/Contents/MacOS/PDF\ Merger
```

**Windows:**
- Try running as Administrator (right-click → "Run as administrator")
- Ensure Windows Defender isn't blocking the app (Check Settings → Virus & protection)
- If using portable version, extract to a folder the app can write to (avoid Program Files)

### "File Not Found" Error

- Ensure the selected PDF files still exist at their locations
- Move PDFs to same folder as app if using network drives
- Check file permissions (app needs read access)

### Merged PDF is Corrupted or Incomplete

- Try merging fewer files at a time
- Ensure all source PDFs are valid (open in other PDF readers first)
- Check available disk space for output file
- Try saving to a different location

### Very Slow Performance

- Close other applications to free up RAM
- Try merging smaller batches of PDFs
- Check if your disk is full or fragmented
- Ensure PDFs aren't password-protected

### "Permission Denied" Error

**macOS:**
```bash
# Fix by allowing full disk access
# System Preferences → Security & Privacy → Full Disk Access
# Add PDF Merger to the list
```

**Windows:**
- Try running as Administrator
- Save merged PDF to Documents or Desktop instead of Program Files
- Check folder permissions

---

## 📁 Installation Locations

### macOS
- **Installed Location**: `/Applications/PDF Merger.app`
- **Settings/Cache**: `~/Library/Application Support/PDF Merger/`
- **Uninstall**: Drag app to Trash, or use Finder → Applications → Delete

### Windows (Installer)
- **Default Location**: `C:\Program Files\PDF Merger\`
- **Start Menu**: Start → Programs → PDF Merger
- **Uninstall**: Control Panel → Programs → Uninstall a program → PDF Merger

### Windows (Portable)
- **Location**: Wherever you extract the ZIP file
- **Uninstall**: Simply delete the folder (no registry changes)

---

## 🔄 Updating

### Check for Updates
Currently checking for updates must be done manually by visiting the releases page.

### Update Process
1. **Download** the new version
2. **macOS**: Replace the old app with the new one in Applications folder
3. **Windows (Installer)**: Uninstall the old version, then run the new installer
4. **Windows (Portable)**: Replace the old folder with the new extracted folder

Your saved settings are preserved during updates.

---

## ⚙️ Advanced Features

### Keyboard Shortcuts

| Action | macOS | Windows |
|--------|-------|---------|
| Add Files | Cmd+O | Ctrl+O |
| Clear List | Cmd+Delete | Ctrl+Delete |
| Merge | Cmd+M | Ctrl+M |
| Move Up | Cmd+↑ | Ctrl+↑ |
| Move Down | Cmd+↓ | Ctrl+↓ |

### Drag & Drop
- Drag PDF files onto the app window to add them
- Drag files within the list to reorder them
- Drop folders to add all containing PDFs

### Folder Processing
- Use "Add Folder" to include all PDFs in a directory
- Subfolders are not processed (only top-level files)
- PDFs are merged in alphabetical order

---

## 🆘 Getting Help

### Common Issues & Solutions

**Q: Can I merge PDFs that are password-protected?**  
A: No, you must remove the password first using another tool.

**Q: What's the maximum number of PDFs I can merge?**  
A: Theoretically unlimited, but 100+ files may slow down the merge process.

**Q: Does the app work offline?**  
A: Yes, completely offline. No internet required.

**Q: Can I undo a merge?**  
A: The original PDFs are never deleted. You can always merge again.

**Q: What PDF versions are supported?**  
A: PDF 1.4 and newer. Very old PDFs may have issues.

**Q: Does it preserve PDF links and metadata?**  
A: Links and metadata are preserved from the source PDFs.

---

## 📝 License

PDF Merger is provided as-is for personal and commercial use.

---

## 💻 System Information

To help troubleshoot issues, you can check:

**macOS:**
```bash
system_profiler SPSoftwareDataType
```

**Windows:**
```powershell
Get-ComputerInfo | Select-Object CsSystemType, OsVersion, OsTotalVisibleMemorySize
```

Include this information when reporting issues.

---

**Last Updated**: March 2026  
**Version**: 1.0  
**Support**: Check the project repository for latest versions and updates
