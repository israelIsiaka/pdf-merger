# Cross-Platform Build & Test Workflow

Quick reference for building on macOS and testing on Windows (or vice versa).

## 📤 macOS → Windows Workflow

### **Step 1: Build on macOS**
```bash
cd /Users/user/pdf-merger
source .venv/bin/activate
python build.py windows
```

**Output:** `dist/windows/PDF Merger/` (Windows executable + dependencies)

### **Step 2: Bundle as ZIP**
```bash
cd /Users/user/pdf-merger/dist/windows
zip -r ../PDF-Merger-Windows-Test.zip "PDF Merger"
```

**Output:** `dist/PDF-Merger-Windows-Test.zip` (ready to transfer)

### **Step 3: Transfer to Windows PC**
- Email the ZIP file
- Use cloud storage (Google Drive, OneDrive, Dropbox)
- USB transfer
- Network share

### **Step 4: Extract and Test on Windows**
```powershell
# Extract the ZIP
Expand-Archive PDF-Merger-Windows-Test.zip -DestinationPath .

# Run the app
.\\"PDF Merger\\PDF Merger.exe"
```

**Done!** The app runs directly without installation.

---

## 📥 Windows → macOS Workflow

### **Step 1: Build on Windows**
```cmd
cd C:\path\to\pdf-merger
.venv\Scripts\activate.bat
python build.py macos
```

**Output:** `dist/PDF-Merger.dmg` (macOS installer)

### **Step 2: Transfer to macOS**
- Email the DMG file
- Use cloud storage
- USB transfer

### **Step 3: Test on macOS**
```bash
# Double-click to mount
open dist/PDF-Merger.dmg

# Or mount from terminal
hdiutil mount dist/PDF-Merger.dmg
```

---

## ⚡ One-Command Builds

### **macOS (Build & ZIP for Windows)**
```bash
cd /Users/user/pdf-merger && \
source .venv/bin/activate && \
python build.py windows && \
cd dist/windows && \
zip -r ../PDF-Merger-Windows-Test.zip "PDF Merger" && \
cd .. && \
echo "✅ Ready: PDF-Merger-Windows-Test.zip"
```

### **Windows (Build DMG for macOS)**
```cmd
cd C:\path\to\pdf-merger & ^
.venv\Scripts\activate.bat & ^
python build.py macos & ^
echo ✅ Ready: dist\PDF-Merger.dmg
```

---

## 📋 What Gets Built

### **macOS Build (on macOS)**
```
dist/
├── PDF-Merger.dmg          ← Professional installer (31 MB)
└── PDF Merger.app/         ← App bundle
```

### **Windows Build (on any platform)**
```
dist/windows/
└── PDF Merger/             ← Portable app (84 MB)
    ├── PDF Merger.exe      ← Main executable
    └── _internal/          ← Dependencies
```

---

## 🔍 Troubleshooting

### Windows Build: "Failed to load Python DLL" Error at Runtime

**Problem:** Users get an error when running the built app on their Windows machine.

**Cause:** PyInstaller's `--onefile` mode extracts DLLs to `%TEMP%`, which Windows Defender blocks.

**Solution:** Always use `--onedir` for Windows builds:

```bash
# ✅ CORRECT — uses --onedir + NSIS installer
python build.py windows            # creates dist/windows/PDF Merger/ folder
python build.py windows-installer  # packages into NSIS installer

# ❌ WRONG — do not use --onefile on Windows
```

**For End Users:** 
1. Install Visual C++ Redistributable for Visual Studio 2022 (x64)
2. Use the NSIS installer (not the portable folder)
3. Install to `C:\Program Files\PDF Merger` (not elsewhere)

### ZIP creation fails on macOS
```bash
# If you get permission errors, use ditto instead
ditto -c -k --sequesterRsrc "dist/windows/PDF Merger" "dist/windows/PDF-Merger-Windows-Test.zip"
```

### ZIP extraction on Windows fails
```powershell
# Use 7-Zip or other tools if Expand-Archive fails
# Or try right-click → Extract All
```

### App won't run after extraction on Windows
1. Right-click → Properties → Check if blocked
2. Properties → General → Click "Unblock" if present
3. Try running as Administrator

### App won't run after mounting on macOS
1. Right-click app → Open (first time)
2. System Preferences → Security & Privacy → Allow

---

## ✅ Testing Checklist

After building and testing on the other platform:

- [ ] App launches without errors
- [ ] Can add PDF files
- [ ] Can drag & drop files
- [ ] Can reorder files
- [ ] Can merge files
- [ ] Merged PDF is valid
- [ ] No crashes or freezes
- [ ] UI looks correct
- [ ] All buttons work

---

## 📝 Notes

- PyInstaller can create Windows binaries on macOS, but it's not native
- For production, build on the target platform when possible
- The portable folders (dist/windows/PDF Merger/) don't require installation
- Always test on the target platform before final release

---

**Last Updated:** March 2026
