import pytest

from catalog.errors import CatalogError
from catalog.errors import DuplicateIdError
from catalog.errors import EntityNotFoundError
from catalog.models import Book
from catalog.repository import BookCatalog
from catalog.repository import ReadOnlyCatalogView
from catalog.repository import UndoableBookCatalog


def make_book(
    item_id: str,
    name: str = "Title",
    category: str = "General",
    year: int = 2020,
    author: str = "Author",
    isbn: str = "978-0000000000",
    edition: int = 1,
) -> Book:
    return Book(
        item_id=item_id,
        name=name,
        category=category,
        year=year,
        author=author,
        isbn=isbn,
        edition=edition,
    )


def test_add_get_remove_len_contains() -> None:
    catalog = BookCatalog()
    b1 = make_book("1", "Python Crash Course", "Programming")
    b2 = make_book("2", "Fluent Python", "Programming")

    catalog.add(b1)
    catalog.add(b2)

    assert len(catalog) == 2
    assert "1" in catalog
    assert "999" not in catalog
    assert catalog.get("1") == b1

    catalog.remove("1")
    assert len(catalog) == 1
    assert "1" not in catalog
    with pytest.raises(EntityNotFoundError) as exc_info:
        catalog.get("1")
    assert exc_info.value.item_id == "1"


def test_duplicate_id_raises() -> None:
    catalog = BookCatalog([make_book("dup-1", "First")])

    with pytest.raises(DuplicateIdError) as exc_info:
        catalog.add(make_book("dup-1", "Second"))

    assert exc_info.value.item_id == "dup-1"
    assert len(catalog) == 1
    assert catalog.get("dup-1").name == "First"


def test_remove_missing_id_raises() -> None:
    catalog = BookCatalog()

    with pytest.raises(EntityNotFoundError) as exc_info:
        catalog.remove("missing-id")

    assert exc_info.value.item_id == "missing-id"


def test_find_by_category_and_name_case_insensitive_and_not_internal_list() -> None:
    b1 = make_book("1", "Clean Code", "Craft")
    b2 = make_book("2", "The Clean Coder", "Craft")
    b3 = make_book("3", "Refactoring", "Design")
    catalog = BookCatalog([b1, b2, b3])

    by_cat = catalog.find_by_category("Craft")
    assert by_cat == [b1, b2]
    by_cat.clear()
    assert catalog.find_by_category("Craft") == [b1, b2]

    by_name = catalog.find_by_name("cLeAn")
    assert by_name == [b1, b2]
    by_name.clear()
    assert len(catalog) == 3


def test_iteration_order_is_deterministic_after_removal() -> None:
    b1 = make_book("1", "First")
    b2 = make_book("2", "Second")
    b3 = make_book("3", "Third")
    catalog = BookCatalog([b1, b2, b3])

    catalog.remove("2")
    assert list(catalog) == [b1, b3]


def test_read_only_view_allows_reads_and_blocks_mutations() -> None:
    b1 = make_book("1", "Domain-Driven Design", "Architecture")
    catalog = BookCatalog([b1])
    view = ReadOnlyCatalogView(catalog)

    assert len(view) == 1
    assert "1" in view
    assert view.get("1") == b1
    assert view.find_by_category("Architecture") == [b1]
    assert view.find_by_name("domain") == [b1]
    assert list(view) == [b1]

    with pytest.raises(AttributeError):
        view.add = None  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        del view._catalog  # type: ignore[attr-defined]


def test_undoable_catalog_add_and_remove_and_failed_operations() -> None:
    b1 = make_book("1", "One")
    b2 = make_book("2", "Two")
    catalog = UndoableBookCatalog([b1])

    with pytest.raises(CatalogError):
        catalog.undo()

    # Failed add should not push to undo stack
    with pytest.raises(DuplicateIdError):
        catalog.add(b1)

    catalog.add(b2)
    assert len(catalog) == 2
    catalog.undo()
    assert len(catalog) == 1
    assert "2" not in catalog

    catalog.remove("1")
    assert len(catalog) == 0
    catalog.undo()
    assert len(catalog) == 1
    assert catalog.get("1") == b1
