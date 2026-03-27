"""
Platform detection and configuration module.
Detects the operating system and provides platform-specific settings.
"""
import os
import platform
import subprocess
import sys
from typing import Literal

PlatformType = Literal["macos", "windows", "linux"]


class PlatformInfo:
    """Detects and provides information about the current platform."""

    @staticmethod
    def get_platform() -> PlatformType:
        """Detect the current platform."""
        system = platform.system()
        if system == "Darwin":
            return "macos"
        elif system == "Windows":
            return "windows"
        else:
            return "linux"

    @staticmethod
    def is_dark_mode() -> bool:
        """Detect if the system is in dark mode.

        Returns False on any failure so the app always starts cleanly.
        """
        current_platform = PlatformInfo.get_platform()

        if current_platform == "macos":
            try:
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                return "Dark" in result.stdout
            except Exception:
                return False

        elif current_platform == "windows":
            try:
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0  # 0 = dark, 1 = light
            except Exception:
                return False

        else:  # Linux — try GNOME, then KDE, then GTK_THEME env
            # 1. GNOME / GTK (most common)
            try:
                result = subprocess.run(
                    [
                        "gsettings", "get",
                        "org.gnome.desktop.interface",
                        "gtk-application-prefer-dark-theme",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    return "true" in result.stdout.lower()
            except Exception:
                pass

            # 2. GNOME color-scheme (GNOME 42+)
            try:
                result = subprocess.run(
                    [
                        "gsettings", "get",
                        "org.gnome.desktop.interface",
                        "color-scheme",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    return "dark" in result.stdout.lower()
            except Exception:
                pass

            # 3. KDE Plasma
            try:
                result = subprocess.run(
                    ["kreadconfig5", "--group", "General",
                     "--key", "ColorScheme"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    return "dark" in result.stdout.lower()
            except Exception:
                pass

            # 4. GTK_THEME environment variable fallback
            gtk_theme = os.environ.get("GTK_THEME", "")
            if gtk_theme:
                return "dark" in gtk_theme.lower()

            return False

    @staticmethod
    def get_platform_name() -> str:
        """Get human-readable platform name."""
        platform_map = {
            "macos":   "macOS",
            "windows": "Windows",
            "linux":   "Linux",
        }
        return platform_map.get(PlatformInfo.get_platform(), "Unknown")
