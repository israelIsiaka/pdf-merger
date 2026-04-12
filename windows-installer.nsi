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
; Detect existing install
; ============================================================================

Function .onInit
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
