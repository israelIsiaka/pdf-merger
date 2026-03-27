"""
Saved annotation profiles for PDF text overlays.
Profiles are persisted in ~/.pdf_merger_annotation_profiles.json.
"""
import json
import os
from typing import Dict, List

PROFILES_FILE = os.path.join(
    os.path.expanduser("~"), ".pdf_merger_annotation_profiles.json"
)


class AnnotationProfilesManager:
    """Loads and persists named annotation profiles."""

    def __init__(self):
        self._profiles: List[Dict] = self._load()

    # -- Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> List[Dict]:
        try:
            with open(PROFILES_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                # Discard entries that aren't dicts or are missing the required 'name' key
                return [e for e in data if isinstance(e, dict) and "name" in e]
        except Exception:
            pass
        return []

    def _save(self) -> None:
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._profiles, f, indent=2)
        except Exception:
            pass

    # -- Public API ────────────────────────────────────────────────────────────

    def get_profiles(self) -> List[Dict]:
        return list(self._profiles)

    def profile_names(self) -> List[str]:
        return [p.get("name", "") for p in self._profiles]

    def get(self, name: str) -> Dict:
        for p in self._profiles:
            if p.get("name") == name:
                return dict(p)
        return {}

    def save_profile(self, name: str, fields: Dict) -> None:
        """Add a new profile or overwrite an existing one by name."""
        for p in self._profiles:
            if p.get("name") == name:
                p.clear()
                p.update({"name": name, **fields})
                self._save()
                return
        self._profiles.append({"name": name, **fields})
        self._save()

    def delete(self, name: str) -> None:
        self._profiles = [p for p in self._profiles if p.get("name") != name]
        self._save()
