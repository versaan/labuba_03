import json

from pathlib import Path

import pytest

from catalog.errors import CorruptedFileError
from catalog.errors import UnsupportedVersionError
from catalog.models import Book
from catalog.repository import BookCatalog
from catalog.storage import load_catalog
from catalog.storage import save_catalog


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    file_path = tmp_path / "catalog.json"
    books = [
        Book("b-1", "Structure and Interpretation", "CS", 1996, "Abelson & Sussman", "978-0262510875", 2),
        Book("b-2", "Designing Data-Intensive Applications", "Systems", 2017, "Martin Kleppmann", "978-1449373320", 1),
    ]

    save_catalog(file_path, books)
    loaded = load_catalog(file_path)

    assert loaded == books


def test_migrate_v1_to_v2_adds_default_edition(tmp_path: Path) -> None:
    file_path = tmp_path / "v1_catalog.json"
    v1_payload = {
        "format_version": 1,
        "items": [
            {
                "item_id": "b-1",
                "name": "Legacy Book",
                "category": "Archive",
                "year": 2001,
                "author": "Author Name",
                "isbn": "978-1234567890",
            }
        ],
    }
    file_path.write_text(json.dumps(v1_payload), encoding="utf-8")

    migrated = load_catalog(file_path)

    assert len(migrated) == 1
    assert migrated[0].edition == 1
    assert migrated[0].name == "Legacy Book"


def test_corrupted_json_raises_and_does_not_mutate_existing_catalog(tmp_path: Path) -> None:
    file_path = tmp_path / "broken.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    original_book = Book("keep-1", "Existing Book", "Core", 2020, "Author", "978-0000000001", 1)
    catalog = BookCatalog([original_book])

    with pytest.raises(CorruptedFileError):
        rebuilt = BookCatalog(load_catalog(file_path))
        catalog = rebuilt

    assert len(catalog) == 1
    assert catalog.get("keep-1") == original_book


def test_unsupported_version_raises_and_preserves_catalog(tmp_path: Path) -> None:
    file_path = tmp_path / "future_version.json"
    file_path.write_text(json.dumps({"format_version": 99, "items": []}), encoding="utf-8")

    original_book = Book("keep-1", "Existing Book", "Core", 2020, "Author", "978-0000000001", 1)
    catalog = BookCatalog([original_book])

    with pytest.raises(UnsupportedVersionError) as exc_info:
        BookCatalog(load_catalog(file_path))

    assert exc_info.value.version == 99
    assert len(catalog) == 1
    assert catalog.get("keep-1") == original_book
