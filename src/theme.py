"""
Theme manager for platform-specific styling.
Follows each platform's Human Interface Guidelines.
"""
from typing import Dict, Literal

from .utils import PlatformInfo, PlatformType

ThemeType = Literal["light", "dark"]


class ThemeManager:
    """Manages themes for different platforms and appearance modes."""

    # ── macOS — Apple HIG ─────────────────────────────────────────────────────
    MACOS_LIGHT = {
        "bg":                 "#F5F5F7",
        "fg":                 "#1D1D1F",
        # Primary (accent) button — blue, white text passes WCAG AA (5.3:1)
        "button_bg":          "#0556D3",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#044BAD",
        # Secondary (gray) button — used for all non-primary actions
        "secondary_btn_bg":   "#E5E5EA",
        "secondary_btn_hover":"#D1D1D6",
        "secondary_btn_fg":   "#1D1D1F",
        # General
        "secondary_bg":       "#FFFFFF",
        "border":             "#D2D2D7",
        # File list (treeview)
        "listbox_bg":         "#FFFFFF",
        "listbox_fg":         "#1D1D1F",
        "listbox_select":     "#0556D3",
        "tree_alt_bg":        "#F0F0F5",
        "tree_header_bg":     "#F0F0F5",
        "tree_header_fg":     "#6E6E73",
        # Labels
        "label_main":         "#1D1D1F",
        "label_secondary":    "#6E6E73",
        # Status
        "success":            "#34C759",
        "error":              "#FF3B30",
        # Fonts
        "font_family":        "Helvetica Neue",
        "font_mono":          "Menlo",
    }

    MACOS_DARK = {
        "bg":                 "#1C1C1E",
        "fg":                 "#FFFFFF",
        "button_bg":          "#0A84FF",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#409CFF",
        "secondary_btn_bg":   "#3A3A3C",
        "secondary_btn_hover":"#48484A",
        "secondary_btn_fg":   "#FFFFFF",
        "secondary_bg":       "#2C2C2E",
        "border":             "#38383A",
        "listbox_bg":         "#2C2C2E",
        "listbox_fg":         "#FFFFFF",
        "listbox_select":     "#0A84FF",
        "tree_alt_bg":        "#232325",
        "tree_header_bg":     "#2C2C2E",
        "tree_header_fg":     "#8E8E93",
        "label_main":         "#FFFFFF",
        "label_secondary":    "#8E8E93",
        "success":            "#30D158",
        "error":              "#FF453A",
        "font_family":        "Helvetica Neue",
        "font_mono":          "Menlo",
    }

    # ── Windows — Fluent Design (Windows 11) ─────────────────────────────────
    WINDOWS_LIGHT = {
        "bg":                 "#F3F3F3",
        "fg":                 "#1B1B1B",
        "button_bg":          "#0067C0",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#005098",
        "secondary_btn_bg":   "#E0E0E0",
        "secondary_btn_hover":"#CCCCCC",
        "secondary_btn_fg":   "#1B1B1B",
        "secondary_bg":       "#FFFFFF",
        "border":             "#C4C4C4",
        "listbox_bg":         "#FFFFFF",
        "listbox_fg":         "#1B1B1B",
        "listbox_select":     "#0067C0",
        "tree_alt_bg":        "#EBEBEB",
        "tree_header_bg":     "#F0F0F0",
        "tree_header_fg":     "#6B6B6B",
        "label_main":         "#1B1B1B",
        "label_secondary":    "#6B6B6B",
        "success":            "#107C10",
        "error":              "#C42B1C",
        "font_family":        "Segoe UI",
        "font_mono":          "Consolas",
    }

    WINDOWS_DARK = {
        "bg":                 "#202020",
        "fg":                 "#FFFFFF",
        "button_bg":          "#0078D4",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#1484D8",
        "secondary_btn_bg":   "#3C3C3C",
        "secondary_btn_hover":"#4A4A4A",
        "secondary_btn_fg":   "#FFFFFF",
        "secondary_bg":       "#2D2D2D",
        "border":             "#3B3B3B",
        "listbox_bg":         "#2D2D2D",
        "listbox_fg":         "#FFFFFF",
        "listbox_select":     "#0078D4",
        "tree_alt_bg":        "#252525",
        "tree_header_bg":     "#2D2D2D",
        "tree_header_fg":     "#ADADAD",
        "label_main":         "#FFFFFF",
        "label_secondary":    "#ADADAD",
        "success":            "#6CCB5F",
        "error":              "#FC9C9C",
        "font_family":        "Segoe UI",
        "font_mono":          "Consolas",
    }

    # ── Linux — GNOME HIG ─────────────────────────────────────────────────────
    LINUX_LIGHT = {
        "bg":                 "#FAFAFA",
        "fg":                 "#2E2E2E",
        "button_bg":          "#1C71D8",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#1558A6",
        "secondary_btn_bg":   "#E0E0E0",
        "secondary_btn_hover":"#D0D0D0",
        "secondary_btn_fg":   "#2E2E2E",
        "secondary_bg":       "#FFFFFF",
        "border":             "#C0BFBC",
        "listbox_bg":         "#FFFFFF",
        "listbox_fg":         "#2E2E2E",
        "listbox_select":     "#1C71D8",
        "tree_alt_bg":        "#F0F0F0",
        "tree_header_bg":     "#F0F0F0",
        "tree_header_fg":     "#5E5C64",
        "label_main":         "#2E2E2E",
        "label_secondary":    "#5E5C64",
        "success":            "#2EC27E",
        "error":              "#E01B24",
        "font_family":        "Ubuntu",
        "font_mono":          "Ubuntu Mono",
    }

    LINUX_DARK = {
        "bg":                 "#242424",
        "fg":                 "#FFFFFF",
        "button_bg":          "#3584E4",
        "button_fg":          "#FFFFFF",
        "button_hover":       "#62A0EA",
        "secondary_btn_bg":   "#383838",
        "secondary_btn_hover":"#454545",
        "secondary_btn_fg":   "#FFFFFF",
        "secondary_bg":       "#303030",
        "border":             "#3D3D3D",
        "listbox_bg":         "#303030",
        "listbox_fg":         "#FFFFFF",
        "listbox_select":     "#3584E4",
        "tree_alt_bg":        "#1E1E1E",
        "tree_header_bg":     "#303030",
        "tree_header_fg":     "#C0BFC5",
        "label_main":         "#FFFFFF",
        "label_secondary":    "#C0BFC5",
        "success":            "#57E389",
        "error":              "#FF7B7B",
        "font_family":        "Ubuntu",
        "font_mono":          "Ubuntu Mono",
    }

    PLATFORM_THEMES = {
        "macos":   {"light": MACOS_LIGHT,   "dark": MACOS_DARK},
        "windows": {"light": WINDOWS_LIGHT, "dark": WINDOWS_DARK},
        "linux":   {"light": LINUX_LIGHT,   "dark": LINUX_DARK},
    }

    def __init__(self):
        self.platform: PlatformType = PlatformInfo.get_platform()
        self.is_dark = PlatformInfo.is_dark_mode()
        self.theme_name: ThemeType = "dark" if self.is_dark else "light"
        self.colors: Dict[str, str] = self._get_theme()

    def _get_theme(self) -> Dict[str, str]:
        return self.PLATFORM_THEMES[self.platform][self.theme_name]

    def get_color(self, key: str) -> str:
        return self.colors.get(key, "#000000")

    def get_font(self, key: str = "font_family") -> str:
        return self.colors.get(key, "Helvetica")

    def is_platform(self, platform: PlatformType) -> bool:
        return self.platform == platform

    def get_platform_name(self) -> str:
        return PlatformInfo.get_platform_name()
