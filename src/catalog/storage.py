"""JSON persistence and format migration for the catalog package."""

import json

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .errors import CorruptedFileError
from .errors import InvalidEntityError
from .errors import UnsupportedVersionError
from .models import Book

FORMAT_VERSION = 2
SUPPORTED_VERSIONS = {1, 2}
EXPECTED_BOOK_KEYS = {
    "item_id",
    "name",
    "category",
    "year",
    "author",
    "isbn",
    "edition",
}
V1_BOOK_KEYS = {
    "item_id",
    "name",
    "category",
    "year",
    "author",
    "isbn",
}


def _book_to_dict(book: Book) -> dict[str, Any]:
    return asdict(book)


def _book_from_dict(data: Any, file_path: Path | None = None) -> Book:
    if not isinstance(data, dict):
        raise CorruptedFileError("Book entry must be a dict", file_path)
    if set(data.keys()) != EXPECTED_BOOK_KEYS:
        raise CorruptedFileError("Book entry has missing or unexpected keys", file_path)
    try:
        return Book(**data)
    except InvalidEntityError as exc:
        raise CorruptedFileError(f"Invalid book data in file: {exc}", file_path) from exc


def _migrate_v1_to_v2(raw_data: dict[str, Any], file_path: Path | None = None) -> dict[str, Any]:
    if set(raw_data.keys()) != {"format_version", "items"}:
        raise CorruptedFileError("v1 payload must contain 'format_version' and 'items'", file_path)
    if not isinstance(raw_data["items"], list):
        raise CorruptedFileError("v1 'items' must be a list", file_path)

    migrated_items: list[dict[str, Any]] = []
    for entry in raw_data["items"]:
        if not isinstance(entry, dict):
            raise CorruptedFileError("v1 item entry must be a dict", file_path)
        if set(entry.keys()) != V1_BOOK_KEYS:
            raise CorruptedFileError("v1 item entry has missing or unexpected keys", file_path)
        item = deepcopy(entry)
        item["edition"] = 1
        migrated_items.append(item)

    return {
        "format_version": 2,
        "items": migrated_items,
    }


def _normalize_payload(raw_data: Any, file_path: Path | None = None) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise CorruptedFileError("Catalog root must be a JSON object", file_path)
    if "format_version" not in raw_data:
        raise CorruptedFileError("Catalog root must contain 'format_version'", file_path)

    version = raw_data["format_version"]
    if type(version) is not int:
        raise CorruptedFileError("format_version must be an int", file_path)
    if version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version, supported_version=FORMAT_VERSION)

    if version == 1:
        return _migrate_v1_to_v2(raw_data, file_path)

    if set(raw_data.keys()) != {"format_version", "items"}:
        raise CorruptedFileError("Catalog root must contain 'format_version' and 'items'", file_path)
    if not isinstance(raw_data["items"], list):
        raise CorruptedFileError("'items' must be a list", file_path)

    return raw_data


def save_catalog(path: Path | str, books: Iterable[Book]) -> None:
    target = Path(path)
    payload = {
        "format_version": FORMAT_VERSION,
        "items": [_book_to_dict(book) for book in books],
    }
    try:
        with target.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise CorruptedFileError(f"Failed to write catalog file: {exc}", target) from exc


def load_catalog(path: Path | str) -> list[Book]:
    target = Path(path)
    try:
        with target.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise CorruptedFileError(f"Failed to read catalog file: {exc}", target) from exc

    normalized = _normalize_payload(raw_data, target)
    return [_book_from_dict(item, target) for item in normalized["items"]]
