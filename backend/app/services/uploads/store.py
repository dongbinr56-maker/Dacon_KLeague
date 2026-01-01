import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from app.core.config import get_settings


@dataclass
class UploadItem:
    file_id: str
    path: str
    filename: str
    size_bytes: int

    @property
    def download_url(self) -> str:
        settings = get_settings()
        return f"{settings.api_prefix}/uploads/{self.file_id}"


class UploadStore:
    def __init__(self) -> None:
        self._items: Dict[str, UploadItem] = {}
        self._settings = get_settings()
        self._index_path = os.path.join(self._settings.storage_path, "upload_index.json")
        self._load_index()

    def add(self, item: UploadItem) -> None:
        self._items[item.file_id] = item
        self._save_index()

    def get(self, file_id: str) -> Optional[UploadItem]:
        return self._items.get(file_id)

    def resolve_download_url(self, file_id: str) -> Optional[str]:
        item = self.get(file_id)
        if item:
            return item.download_url
        return None

    def resolve_path(self, file_id: str) -> Optional[str]:
        item = self.get(file_id)
        if item:
            return item.path
        return None

    def list_items(self) -> Dict[str, UploadItem]:
        return self._items

    def _load_index(self) -> None:
        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, PermissionError):
            return
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return

        for file_id, payload in data.items():
            if all(k in payload for k in ("path", "filename", "size_bytes")):
                self._items[file_id] = UploadItem(
                    file_id=file_id,
                    path=payload["path"],
                    filename=payload["filename"],
                    size_bytes=int(payload["size_bytes"]),
                )

    def _save_index(self) -> None:
        os.makedirs(self._settings.storage_path, exist_ok=True)
        payload = {file_id: asdict(item) for file_id, item in self._items.items()}
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


_UPLOAD_STORE: UploadStore | None = None


def get_upload_store() -> UploadStore:
    global _UPLOAD_STORE
    if _UPLOAD_STORE is None:
        _UPLOAD_STORE = UploadStore()
    return _UPLOAD_STORE
