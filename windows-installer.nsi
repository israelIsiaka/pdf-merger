; PDF Merger Windows Installer
; Built with NSIS 3.x
; This script creates a professional Windows installer for PDF Merger

!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

; ============================================================================
; Configuration
; ============================================================================

; Application info
!define APPNAME "PDF Merger"
!define APPVERSION "1.0"
!define APPDIR "PDF Merger"
!define APPEXE "PDF Merger.exe"
!define PUBLISHER "PDF Merger Project"
!define HELPURL "https://github.com/yourusername/pdf-merger"
!define UPDATEURL "https://github.com/yourusername/pdf-merger/releases"
!define UNINSTALLDIR "$PROGRAMFILES\${APPDIR}"

; Installer settings
Name "${APPNAME} ${APPVERSION}"
OutFile "PDF-Merger-Installer.exe"
InstallDir "${UNINSTALLDIR}"
InstallDirRegKey HKCU "Software\${APPNAME}" ""

; Request administrator rights
RequestExecutionLevel admin

; Compression
SetCompress auto
SetDatablockOptimize on
SetOverwrite on
CRCCheck on

; ============================================================================
; Modern UI Configuration
; ============================================================================

!define MUI_ICON "Logo.ico"
!define MUI_UNICON "Logo.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APPNAME} ${APPVERSION}.$\r$\n$\r$\nA fast, professional PDF merger with a modern interface.$\r$\n$\r$\nClick Next to continue."

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; Installation Sections
; ============================================================================

Section "Install Application" SEC_INSTALL
    SectionIn RO  ; Required section, always installed
    
    SetOutPath "$INSTDIR"
    
    ; Check if source files exist
    ${If} ${FileExists} "dist\windows\PDF Merger\*.*"
        File /r "dist\windows\PDF Merger\*.*"
    ${Else}
        MessageBox MB_ICONEXCLAMATION "Warning: Source files not found in dist\windows\PDF Merger\$\r$\nPlease ensure build.py windows was run successfully."
    ${EndIf}
    
    ; Write registry for uninstall info
    WriteRegStr HKCU "Software\${APPNAME}" "" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayName" "${APPNAME} ${APPVERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "Publisher" "${PUBLISHER}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "BuildPath" "$INSTDIR"
    WriteRegDWord HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                       "NoModify" "1"
    WriteRegDWord HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                       "NoRepair" "1"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
SectionEnd

Section "Start Menu Shortcuts" SEC_STARTMENU
    SetOutPath "$INSTDIR"
    
    ; Create Start Menu folder
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    
    ; Create shortcuts
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
    CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
SectionEnd

Section "Desktop Shortcut" SEC_DESKTOP
    SetOutPath "$INSTDIR"
    
    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
    
SectionEnd

Section "File Association (Optional)" SEC_FILEASSOC
    ; Register .pdf file association (optional)
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf\UserChoice" \
                     "${APPNAME}" "$INSTDIR\${APPEXE}"
    
SectionEnd

; ============================================================================
; Section Descriptions
; ============================================================================

LangString DESC_SEC_INSTALL ${LANG_ENGLISH} "${APPNAME} application files"
LangString DESC_SEC_STARTMENU ${LANG_ENGLISH} "Create shortcuts in Start Menu"
LangString DESC_SEC_DESKTOP ${LANG_ENGLISH} "Create shortcut on Desktop"
LangString DESC_SEC_FILEASSOC ${LANG_ENGLISH} "Associate with PDF files (opens PDFs with ${APPNAME})"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_INSTALL} $(DESC_SEC_INSTALL)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} $(DESC_SEC_STARTMENU)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} $(DESC_SEC_DESKTOP)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

; ============================================================================
; Callbacks
; ============================================================================

Function .onInit
    ; Check if already installed
    ReadRegStr $R0 HKCU "Software\${APPNAME}" ""
    ${If} $R0 != ""
        MessageBox MB_YESNO "${APPNAME} is already installed. Do you want to replace it?" \
                   IDYES uninst_yes
        Abort
        uninst_yes:
        ExecWait "$INSTDIR\Uninstall.exe /S"
        Sleep 500
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    MessageBox MB_ICONINFORMATION "${APPNAME} ${APPVERSION} has been installed successfully!$\r$\n$\r$\nYou can launch it from the Start Menu or by double-clicking the Desktop shortcut."
FunctionEnd

; ============================================================================
; Uninstaller
; ============================================================================

Section "Uninstall"
    ; Close running instance
    nsExec::ExecToLog 'taskkill /IM ${APPEXE} /F'
    Sleep 500
    
    ; Remove application files
    RMDir /r "$INSTDIR"
    
    ; Remove Start Menu shortcuts
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    
    ; Remove Desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKCU "Software\${APPNAME}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    
    MessageBox MB_ICONINFORMATION "${APPNAME} has been uninstalled successfully!"
    
SectionEnd

Function un.onInit
    MessageBox MB_ICONQUESTION "Are you sure you want to completely remove ${APPNAME}?" IDYES +2
    Abort
FunctionEnd
