import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional


class SearchHistoryError(Exception):
    pass


class SearchHistory:
    def __init__(self, filepath: str = "search_history.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except OSError as e:
                raise SearchHistoryError(f"Could not create history file: {e}")

    def _load_raw(self) -> List[Dict]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if not isinstance(data, list):
                    raise SearchHistoryError("History file is corrupted.")
                return data
        except FileNotFoundError:
            self._ensure_file_exists()
            return []
        except json.JSONDecodeError:
            self._backup_corrupted_file()
            return []
        except OSError as e:
            raise SearchHistoryError(f"Could not read history file: {e}")

    def _backup_corrupted_file(self) -> None:
        try:
            os.replace(self.filepath, self.filepath + ".corrupted_backup")
        except OSError:
            pass
        self._ensure_file_exists()

    def _save_raw(self, entries: List[Dict]) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise SearchHistoryError(f"Could not save history file: {e}")

    @staticmethod
    def _clean_drug_name(name: str) -> str:
        if not name or not isinstance(name, str):
            raise SearchHistoryError("Drug name cannot be empty.")

        cleaned = re.sub(r"[^a-zA-Z0-9\s\-]", "", name.strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if not cleaned or not re.search(r"[a-zA-Z]", cleaned):
            raise SearchHistoryError(f"'{name}' doesn't look like a valid medication name.")

        return cleaned

    @staticmethod
    def extract_warning_keywords(text: str) -> List[str]:
        if not text:
            return []

        keyword_patterns = [
            r"overdose", r"allerg(?:y|ic|ies)", r"liver damage",
            r"kidney (?:damage|failure)", r"drowsiness", r"addiction",
            r"withdrawal", r"rash", r"breathing difficult\w*",
            r"heart (?:attack|problem\w*)", r"bleeding", r"seizures?",
            r"pregnan\w*", r"interaction\w*",
        ]
        found = set()
        for pattern in keyword_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            found.update(m.lower() for m in matches)
        return sorted(found)

    def add_search(
        self,
        drug_name: str,
        summary: str = "",
        warnings: Optional[List[str]] = None,
        recall_flag: bool = False,
        raw_data: Optional[Dict] = None,
    ) -> Dict:
        clean_name = self._clean_drug_name(drug_name)
        entries = self._load_raw()

        new_entry = {
            "id": (entries[-1]["id"] + 1) if entries else 1,
            "drug_name": clean_name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "summary": summary.strip() if summary else "",
            "warnings": warnings or [],
            "recall_flag": bool(recall_flag),
            "raw_data": raw_data or {},
        }

        entries.append(new_entry)
        self._save_raw(entries)
        return new_entry

    def get_all(self, newest_first: bool = True) -> List[Dict]:
        entries = self._load_raw()
        return list(reversed(entries)) if newest_first else entries

    def search(self, keyword: str) -> List[Dict]:
        if not keyword or not keyword.strip():
            return self.get_all()

        try:
            pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
        except re.error:
            raise SearchHistoryError("Invalid search keyword.")

        entries = self._load_raw()
        matches = [e for e in entries if pattern.search(e.get("drug_name", ""))]
        return list(reversed(matches))

    def get_recalled_only(self) -> List[Dict]:
        entries = self._load_raw()
        return list(reversed([e for e in entries if e.get("recall_flag")]))

    def delete_entry(self, entry_id: int) -> bool:
        entries = self._load_raw()
        new_entries = [e for e in entries if e.get("id") != entry_id]
        if len(new_entries) == len(entries):
            return False
        self._save_raw(new_entries)
        return True

    def clear_all(self) -> None:
        self._save_raw([])

    def count(self) -> int:
        return len(self._load_raw())
