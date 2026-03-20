"""
PDF Merger - A professional PDF merging application with platform-native styling.
"""
__version__ = "1.0.0"
__author__ = "PDF Merger Contributors"

from .app import PDFMergerApp, main
from .merger import PDFMerger
from .history import HistoryManager
from .theme import ThemeManager
from .utils import PlatformInfo

__all__ = ["PDFMergerApp", "main", "PDFMerger", "HistoryManager", "ThemeManager", "PlatformInfo"]
