"""
Platform detection and configuration module.
Detects the operating system and provides platform-specific settings.
"""
import sys
import platform
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
        """Detect if system is in dark mode."""
        current_platform = PlatformInfo.get_platform()
        
        if current_platform == "macos":
            try:
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                return "Dark" in result.stdout
            except:
                return False
        
        elif current_platform == "windows":
            try:
                import winreg
                registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
                value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                winreg.CloseKey(registry_key)
                return value == 0  # 0 = dark, 1 = light
            except:
                return False
        
        else:  # Linux
            try:
                import subprocess
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-application-prefer-dark-theme"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                return "true" in result.stdout.lower()
            except:
                return False
    
    @staticmethod
    def get_platform_name() -> str:
        """Get human-readable platform name."""
        platform_map = {
            "macos": "macOS",
            "windows": "Windows",
            "linux": "Linux"
        }
        return platform_map.get(PlatformInfo.get_platform(), "Unknown")
