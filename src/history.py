"""
History manager for PDF Merger.
Tracks past merge and protect operations.
"""
import datetime
import json
import os
from typing import List, Dict

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".pdf_merger_history.json")
MAX_ENTRIES = 100


class HistoryManager:
    """Loads and persists merge/protect operation history."""

    def __init__(self):
        self._entries: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                # Discard any entries that aren't plain dicts (corrupt / hand-edited file)
                return [e for e in data if isinstance(e, dict)]
        except Exception:
            pass
        return []

    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
        except Exception:
            pass

    def add_merge(self, output_path: str, source_count: int, password_protected: bool):
        """Record a merge operation. Stores only the filename, not the full path."""
        self._entries.insert(0, {
            "type": "Merge",
            "output": os.path.basename(output_path),
            "sources": source_count,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": password_protected,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_protect(self, output_path: str):
        """Record a protect operation. Stores only the filename, not the full path."""
        self._entries.insert(0, {
            "type": "Protect",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": True,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_peep(self, preview_path: str, full_path: str, free_pages: int):
        """Record a peep operation. Stores only filenames, not full paths."""
        self._entries.insert(0, {
            "type": "Peep",
            "output": os.path.basename(full_path),
            "preview": os.path.basename(preview_path),
            "sources": 1,
            "free_pages": free_pages,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": True,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_compress(self, output_path: str, level_label: str):
        """Record a compress operation."""
        self._entries.insert(0, {
            "type": f"Compress ({level_label})",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_annotate(self, output_path: str) -> None:
        """Record an annotate/sign operation."""
        self._entries.insert(0, {
            "type": "Annotate",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_split(self, output_dir: str, count: int):
        """Record a split operation."""
        self._entries.insert(0, {
            "type": "Split",
            "output": os.path.basename(output_dir),
            "sources": count,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_pdf_to_word(self, output_path: str):
        """Record a PDF-to-Word conversion."""
        self._entries.insert(0, {
            "type": "PDF to Word",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_word_to_pdf(self, output_path: str):
        """Record a Word-to-PDF conversion."""
        self._entries.insert(0, {
            "type": "Word to PDF",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_pdf_to_images(self, output_dir: str, count: int):
        """Record a PDF-to-Images conversion."""
        self._entries.insert(0, {
            "type": "PDF to Images",
            "output": os.path.basename(output_dir),
            "sources": count,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_images_to_pdf(self, output_path: str, count: int):
        """Record an Images-to-PDF conversion."""
        self._entries.insert(0, {
            "type": "Images to PDF",
            "output": os.path.basename(output_path),
            "sources": count,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def add_watermark(self, output_path: str):
        """Record a watermark operation."""
        self._entries.insert(0, {
            "type": "Watermark",
            "output": os.path.basename(output_path),
            "sources": 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "password_protected": False,
        })
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    def get_entries(self) -> List[Dict]:
        return list(self._entries)

    def clear(self):
        self._entries = []
        self._save()
