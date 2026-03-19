"""
Theme manager for platform-specific styling.
Provides native-looking themes for macOS, Windows, and Linux.
"""
from typing import Dict, Literal
from .utils import PlatformInfo, PlatformType

ThemeType = Literal["light", "dark"]


class ThemeManager:
    """Manages themes for different platforms and appearance modes."""
    
    # macOS - Native iOS-inspired theme
    MACOS_LIGHT = {
        "bg": "#F2F2F7",
        "fg": "#000000",
        "button_bg": "#0A84FF",
        "button_fg": "#FFFFFF",
        "button_hover": "#0073E6",
        "secondary_bg": "#FFFFFF",
        "border": "#E5E5EA",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#000000",
        "listbox_select": "#0A84FF",
        "label_main": "#000000",
        "label_secondary": "#666666",
        "success": "#34C759",
        "error": "#FF3B30",
    }
    
    MACOS_DARK = {
        "bg": "#1C1C1E",
        "fg": "#FFFFFF",
        "button_bg": "#147EFB",
        "button_fg": "#FFFFFF",
        "button_hover": "#0073E6",
        "button_active": "#005CC8",
        "secondary_bg": "#2C2C2E",
        "border": "#454545",
        "listbox_bg": "#2C2C2E",
        "listbox_fg": "#FFFFFF",
        "listbox_select": "#147EFB",
        "label_main": "#FFFFFF",
        "label_secondary": "#999999",
        "success": "#34C759",
        "error": "#FF453A",
    }
    
    # Windows - Native Windows 11 Fluent Design
    WINDOWS_LIGHT = {
        "bg": "#F3F3F3",
        "fg": "#000000",
        "button_bg": "#005A9E",
        "button_fg": "#FFFFFF",
        "button_hover": "#004578",
        "secondary_bg": "#FFFFFF",
        "border": "#D0D0D0",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#000000",
        "listbox_select": "#005A9E",
        "label_main": "#000000",
        "label_secondary": "#595959",
        "success": "#107C10",
        "error": "#D83B01",
    }
    
    WINDOWS_DARK = {
        "bg": "#2D2D2D",
        "fg": "#FFFFFF",
        "button_bg": "#0078D4",
        "button_fg": "#FFFFFF",
        "button_hover": "#1084D7",
        "secondary_bg": "#3C3C3C",
        "border": "#454545",
        "listbox_bg": "#3C3C3C",
        "listbox_fg": "#FFFFFF",
        "listbox_select": "#0078D4",
        "label_main": "#FFFFFF",
        "label_secondary": "#B4B4B4",
        "success": "#107C10",
        "error": "#FF8C00",
    }
    
    # Linux/GTK - Native GNOME/GTK theme
    LINUX_LIGHT = {
        "bg": "#F5F5F5",
        "fg": "#2E2E2E",
        "button_bg": "#3584E4",
        "button_fg": "#FFFFFF",
        "button_hover": "#2A5FBB",
        "secondary_bg": "#FFFFFF",
        "border": "#CCCCCC",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#2E2E2E",
        "listbox_select": "#3584E4",
        "label_main": "#2E2E2E",
        "label_secondary": "#666666",
        "success": "#26A269",
        "error": "#E01B24",
    }
    
    LINUX_DARK = {
        "bg": "#242424",
        "fg": "#FFFFFF",
        "button_bg": "#3584E4",
        "button_fg": "#FFFFFF",
        "button_hover": "#5BA3F5",
        "secondary_bg": "#303030",
        "border": "#3D3D3D",
        "listbox_bg": "#303030",
        "listbox_fg": "#FFFFFF",
        "listbox_select": "#3584E4",
        "label_main": "#FFFFFF",
        "label_secondary": "#CCCCCC",
        "success": "#26A269",
        "error": "#FF7B7B",
    }
    
    PLATFORM_THEMES = {
        "macos": {"light": MACOS_LIGHT, "dark": MACOS_DARK},
        "windows": {"light": WINDOWS_LIGHT, "dark": WINDOWS_DARK},
        "linux": {"light": LINUX_LIGHT, "dark": LINUX_DARK},
    }
    
    def __init__(self):
        self.platform: PlatformType = PlatformInfo.get_platform()
        self.is_dark = PlatformInfo.is_dark_mode()
        self.theme_name: ThemeType = "dark" if self.is_dark else "light"
        self.colors: Dict[str, str] = self._get_theme()
    
    def _get_theme(self) -> Dict[str, str]:
        """Get the appropriate theme for the current platform and appearance."""
        return self.PLATFORM_THEMES[self.platform][self.theme_name]
    
    def get_color(self, key: str) -> str:
        """Get a color value from the theme."""
        return self.colors.get(key, "#000000")
    
    def is_platform(self, platform: PlatformType) -> bool:
        """Check if running on a specific platform."""
        return self.platform == platform
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return PlatformInfo.get_platform_name()
