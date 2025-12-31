import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class UploadItem:
    file_id: str
    path: str
    filename: str
    size_bytes: int

    @property
    def download_url(self) -> str:
        return f"/api/uploads/{self.file_id}"


class UploadStore:
    def __init__(self) -> None:
        self._items: Dict[str, UploadItem] = {}

    def add(self, item: UploadItem) -> None:
        self._items[item.file_id] = item

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


upload_store = UploadStore()
