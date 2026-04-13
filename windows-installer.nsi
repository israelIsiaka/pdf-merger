; PDF Merger Windows Installer
; Built with NSIS 3.x

!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

; Allow output path to be overridden: makensis /DOUTDIR=dist installer.nsi
!ifndef OUTDIR
  !define OUTDIR "dist"
!endif

; ============================================================================
; Configuration
; ============================================================================

!define APPNAME    "PDF Merger"
!define APPVERSION "1.0"
!define APPDIR     "PDF Merger"
!define APPEXE     "PDF Merger.exe"
!define PUBLISHER  "PDF Merger Project"
!define HELPURL    "https://github.com/israelIsiaka/pdf-merger"
!define UPDATEURL  "https://github.com/israelIsiaka/pdf-merger/releases"

Name    "${APPNAME} ${APPVERSION}"
OutFile "${OUTDIR}\PDF-Merger-Installer.exe"

; Install to 64-bit Program Files on 64-bit Windows
InstallDir "$PROGRAMFILES64\${APPDIR}"
InstallDirRegKey HKCU "Software\${APPNAME}" ""

; Require administrator rights so we can write to Program Files
RequestExecutionLevel admin

SetCompress   auto
SetOverwrite  on
CRCCheck      on

; ============================================================================
; Modern UI
; ============================================================================

!define MUI_ICON    "Logo.ico"
!define MUI_UNICON  "Logo.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TEXT \
  "This wizard will install ${APPNAME} ${APPVERSION} on your computer.\
   $\r$\n$\r$\nPDF Merger is a free, offline PDF toolkit.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN         "$INSTDIR\${APPEXE}"
!define MUI_FINISHPAGE_RUN_TEXT    "Launch PDF Merger"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; Install
; ============================================================================

Section "Install Application" SEC_INSTALL
    SectionIn RO

    SetOutPath "$INSTDIR"
    File /r "dist\windows\${APPDIR}\*.*"

    ; Registry — uninstall entry visible in Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayName"    "${APPNAME} ${APPVERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "Publisher"      "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "HelpLink"       "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "URLUpdateInfo"  "${UPDATEURL}"
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                       "NoModify" 1
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                       "NoRepair" 1

    WriteRegStr HKCU "Software\${APPNAME}" "" "$INSTDIR"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Start Menu Shortcut" SEC_STARTMENU
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut  "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" \
                    "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
    CreateShortcut  "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" \
                    "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Desktop Shortcut" SEC_DESKTOP
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" \
                   "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
SectionEnd

LangString DESC_SEC_INSTALL   ${LANG_ENGLISH} "${APPNAME} application files"
LangString DESC_SEC_STARTMENU ${LANG_ENGLISH} "Create shortcuts in Start Menu"
LangString DESC_SEC_DESKTOP   ${LANG_ENGLISH} "Create shortcut on Desktop"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_INSTALL}   $(DESC_SEC_INSTALL)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} $(DESC_SEC_STARTMENU)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP}   $(DESC_SEC_DESKTOP)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ============================================================================
; Check and Install Visual C++ Redistributable (prerequisite)
; ============================================================================

Function CheckAndInstallVCRedist
    ; Check if Visual C++ 2022 Redistributable (x64) is already installed
    ReadRegDWord $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{3c635d47-e510-482a-95f0-58a9e8a95d6d}" "DisplayVersion"
    ${If} $0 != ""
        ; Already installed, proceed silently
        return
    ${EndIf}

    ; Not installed, show status and download/install automatically
    IntOp $0 0 + 0  ; Initialize counter
    SetDetailsView show
    DetailPrint ""
    DetailPrint "Checking Visual C++ 2022 Runtime..."
    DetailPrint "Not found. Downloading and installing..."
    DetailPrint ""

    ; Download VC++ Redistributable to temp
    SetOutPath "$TEMP"
    StrCpy $1 "$TEMP\vc_redist_x64.exe"
    DetailPrint "Downloading Visual C++ Redistributable (required library)..."
    DetailPrint "This is a free library from Microsoft and only happens once."
    
    ; Use Windows built-in downloader (more reliable than NSIS methods)
    nsExec::ExecToLog 'powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile(\"https://aka.ms/vs/17/release/vc_redist.x64.exe\", \"$1\") } catch { exit 1 }"'
    Pop $0
    
    ${If} $0 != 0
        ; Download failed, show URL and ask user
        MessageBox MB_OKCANCEL "Could not auto-download Visual C++ Redistributable.$\n$\n\
            Please download it manually:$\n\
            https://aka.ms/vs/17/release/vc_redist.x64.exe$\n$\n\
            Install it, then run this installer again." \
            IDOK OpenURL IDCANCEL AbortVC
        
        OpenURL:
            ExecShell "open" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
            MessageBox MB_OK "Please install Visual C++ Redistributable, then run this installer again."
            Abort
        
        AbortVC:
            Abort
    ${EndIf}

    ; Install silently
    DetailPrint "Installing Visual C++ Redistributable (this may take a minute)..."
    nsExec::ExecToLog '"$1" /q /norestart'
    Pop $0
    
    ${If} $0 != 0
        MessageBox MB_ICONEXCLAMATION "Visual C++ installation returned error code $0.$\n$\nPDF Merger may not work correctly.$\n$\nContinuing anyway..."
    ${Else}
        DetailPrint "Visual C++ Redistributable installed successfully!"
    ${EndIf}
    
    ; Clean up
    Delete "$1"
    DetailPrint ""
    return
FunctionEnd

; ============================================================================
; Uninstaller Section
; ============================================================================

Function .onInit
    ; Check and install Visual C++ Redistributable first
    Call CheckAndInstallVCRedist

    ; Check if already installed
    ReadRegStr $R0 HKCU "Software\${APPNAME}" ""
    ${If} $R0 != ""
        MessageBox MB_YESNO \
          "${APPNAME} is already installed. Replace it?" \
          IDYES do_uninstall
        Abort
        do_uninstall:
        ExecWait '"$R0\Uninstall.exe" /S'
        Sleep 1000
    ${EndIf}
FunctionEnd

; ============================================================================
; Uninstall
; ============================================================================

Section "Uninstall"
    nsExec::ExecToLog 'taskkill /IM "${APPEXE}" /F'
    Sleep 500

    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    Delete   "$DESKTOP\${APPNAME}.lnk"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKCU "Software\${APPNAME}"
SectionEnd
