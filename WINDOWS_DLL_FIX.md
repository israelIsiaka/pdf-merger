# Windows Installation & DLL Error - Troubleshooting Guide

## How It's Fixed (Fully Automatic ✅)

**The latest installer handles everything for you:**

1. When you run `PDF-Merger-Installer.exe`, it checks if Visual C++ 2022 Redistributable is installed
2. If it's **already installed** → Installation proceeds immediately (you don't even see a message)
3. If it's **not installed** → Installer automatically:
   - Downloads it from Microsoft (requires internet)
   - Installs it silently in the background
   - Shows progress so you know what's happening
   - Continues with PDF Merger installation
   - **Everything is done in one go!**

**Just run the installer and it handles the rest. You don't need to do anything manually.**

---

## Quick Fix for "Failed to load Python DLL" Error

If you still see this error when launching PDF Merger on Windows:

```
Failed to load Python DLL 'C:\Program Files\PDF Merger_internal\python311.dll'
LoadLibrary: Invalid access to memory location.
```

**This means Visual C++ Redistributable isn't installed yet.**

### Solution

**Option 1: Download from the installer (Recommended)**
- Our latest installer will prompt you to download it - just follow the prompts

**Option 2: Manual Install**
1. Go to: https://support.microsoft.com/en-us/help/2977003
2. Download **Visual C++ Redistributable for Visual Studio 2022** 
3. Choose the **x64** version (for 64-bit Windows)
4. Run the installer
5. Click "Install" and wait
6. **Restart your computer**
7. Try PDF Merger again

---

## If That Doesn't Work

### **Option A: Reinstall PDF Merger**

1. **Uninstall the app:**
   - Open Control Panel
   - Go to Programs → Uninstall a program
   - Find "PDF Merger" and click it
   - Click "Uninstall" and follow prompts

2. **Delete leftover files:**
   - Open File Explorer
   - Navigate to: `C:\Program Files`
   - Delete the `PDF Merger` folder if it still exists

3. **Reinstall:**
   - Download the latest `PDF-Merger-Installer.exe`
   - Run it as Administrator (right-click → "Run as administrator")
   - Follow the installer prompts (it will check for VC++ Redistributable)
   - **Restart your computer**

### **Option B: Use the Portable Version**

If the installer still doesn't work, use the portable version instead:

1. Download `PDF-Merger-Windows.zip` (not the installer)
2. Extract it to: `C:\Users\YourUsername\Documents\PDF-Merger`
3. First, install Visual C++ Redistributable from the link above
4. Then double-click `PDF Merger.exe` to run it
5. No installation needed — just delete the folder to uninstall

---

## Advanced Troubleshooting

### **Check Windows Defender/Antivirus**

Your antivirus might be blocking DLL files:

1. **Temporarily disable antivirus** and test PDF Merger
2. If it works, add PDF Merger to antivirus whitelist:
   - Folder: `C:\Program Files\PDF Merger`
   - File: `C:\Program Files\PDF Merger\PDF Merger.exe`

### **Run Windows System File Checker**

If none of the above work, Windows system files might be corrupted:

1. Press `Windows + X` and select "Terminal (Admin)" (or "Command Prompt (Admin)")
2. Type this command:
   ```cmd
   sfc /scannow
   ```
3. Press Enter and wait (this takes 10-15 minutes)
4. If it finds errors, Windows will repair them
5. Restart your computer
6. Try PDF Merger again

---

## System Requirements (Windows)

If you're on a very old Windows version, PDF Merger might not work:

- **Minimum:** Windows 10 (64-bit)
- **Recommended:** Windows 10/11 (64-bit, fully updated)

To check your Windows version:
1. Press `Windows + R`
2. Type `winver` and press Enter
3. Update Windows if you're not on the latest version

---

## Contact & Report Issues

If you've tried all the above and PDF Merger still won't start:

1. **Save the error message** (take a screenshot)
2. **Note your Windows version** (winver command above)
3. **Check if you have Visual C++ installed:**
   - Open Control Panel → Programs
   - Look for "Visual C++ Redistributable"
   - Note which versions are installed
4. **Report the issue** at: https://github.com/israelIsiaka/pdf-merger/issues
   - Include the screenshot, Windows version, and VC++ info
   - We'll help you fix it!

---

## Why This Happens

PDF Merger is built using PyInstaller, which bundles Python and all dependencies into a standalone executable. On Windows, this requires:

- **Visual C++ Runtime**: Provides core system libraries for Python
- **Correct Installation Location**: `C:\Program Files` (not Downloads, Desktop, etc.)
- **Administrator Rights**: Needed for first-time Windows file loading

The Visual C++ Redistributable provides the missing system libraries that Python needs to run.

The latest installer now automatically checks for this and guides users through installation if needed!
