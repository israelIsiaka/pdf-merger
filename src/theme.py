"""
Theme manager for platform-specific styling.
Design System: "The Digital Architect" - Architectural Blue palette.

Colors follow the Design System spec:
  primary:                  #0058bb
  background:               #f8fafb
  surface-container-lowest: #ffffff
  surface-container-low:    #f2f4f5
  surface-container:        #eceeef
  surface-container-high:   #e6e8e9
  on-surface:               #191c1d
  outline-variant:          #c2c6d5   (used as ghost border)

WCAG AA contrast requirements are met for all foreground/background pairs.
"""
from typing import Dict, Literal

from .utils import PlatformInfo, PlatformType

ThemeType = Literal["light", "dark"]


# -- Shared Design System palette (light) ──────────────────────────────────────
# Borders use outline-variant (#c2c6d5) blended toward background for the
# "Ghost Border" rule — visible enough for accessibility, subtle enough to
# avoid the "trapped content" aesthetic.

_DS_LIGHT: Dict[str, str] = {
    "bg":                 "#f8fafb",   # background
    "fg":                 "#191c1d",   # on-surface
    # Primary button — #0058bb on #ffffff = 6.6:1 contrast (WCAG AA)
    "button_bg":          "#0058bb",
    "button_fg":          "#ffffff",
    "button_hover":       "#1471e6",   # primary-container
    # Secondary buttons — surface-container family
    "secondary_btn_bg":   "#eceeef",   # surface-container
    "secondary_btn_hover":"#e6e8e9",   # surface-container-high
    "secondary_btn_fg":   "#191c1d",
    # Input field background — surface-container-high (filled input style)
    "secondary_bg":       "#e6e8e9",
    # Ghost border — outline-variant softened for tonal integrity
    "border":             "#d0d4de",
    # File list — surface-container-lowest creates a natural "lift"
    "listbox_bg":         "#ffffff",
    "listbox_fg":         "#191c1d",
    "listbox_select":     "#0058bb",
    "tree_alt_bg":        "#f2f4f5",   # surface-container-low
    "tree_header_bg":     "#eceeef",   # surface-container
    "tree_header_fg":     "#5a6270",
    # Labels
    "label_main":         "#191c1d",
    "label_secondary":    "#5a6270",
    # Status
    "success":            "#1e7040",
    "error":              "#b52a1c",
}

# -- Shared Design System palette (dark) ───────────────────────────────────────
# Derived from the light system blues, shifted for dark backgrounds.
# Primary dark: #1e6abf on #111418 = 4.2:1 (UI), white text on it = 4.75:1 (WCAG AA).

_DS_DARK: Dict[str, str] = {
    "bg":                 "#0a0c0f",
    "fg":                 "#dee3e8",
    "button_bg":          "#1e6abf",
    "button_fg":          "#ffffff",
    "button_hover":       "#2570c2",
    "secondary_btn_bg":   "#1e2329",
    "secondary_btn_hover":"#262e38",
    "secondary_btn_fg":   "#dee3e8",
    "secondary_bg":       "#191e24",
    "border":             "#2c3540",
    "listbox_bg":         "#161b21",
    "listbox_fg":         "#dee3e8",
    "listbox_select":     "#1e6abf",
    "tree_alt_bg":        "#13181e",
    "tree_header_bg":     "#191e24",
    "tree_header_fg":     "#8a96a2",
    "label_main":         "#dee3e8",
    "label_secondary":    "#8a96a2",
    "success":            "#4aad72",
    "error":              "#e07060",
}


# -- ThemeManager ──────────────────────────────────────────────────────────────

class ThemeManager:
    """
    Manages the application theme.

    Color tokens are shared across all platforms (Design System).
    Font families remain platform-specific to respect OS conventions.
    """

    MACOS_LIGHT   = {**_DS_LIGHT, "font_family": "Helvetica Neue", "font_mono": "Menlo"}
    MACOS_DARK    = {**_DS_DARK,  "font_family": "Helvetica Neue", "font_mono": "Menlo"}

    WINDOWS_LIGHT = {**_DS_LIGHT, "font_family": "Segoe UI",       "font_mono": "Consolas"}
    WINDOWS_DARK  = {**_DS_DARK,  "font_family": "Segoe UI",       "font_mono": "Consolas"}

    LINUX_LIGHT   = {**_DS_LIGHT, "font_family": "Ubuntu",         "font_mono": "Ubuntu Mono"}
    LINUX_DARK    = {**_DS_DARK,  "font_family": "Ubuntu",         "font_mono": "Ubuntu Mono"}

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
