"""In-memory catalog repository, category index, read-only view, and undo support."""

from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass

from .errors import CatalogError
from .errors import DuplicateIdError
from .errors import EntityNotFoundError
from .models import Book


class BookCatalog:
    """In-memory catalog of Book items indexed by unique item_id.

    Iteration order matches insertion order; removing an item preserves the
    relative order of remaining items. Also maintains a synchronized non-unique
    index by category.
    """

    def __init__(self, books: Iterable[Book] = ()) -> None:
        self._items: dict[str, Book] = {}
        self._category_index: dict[str, set[str]] = {}
        for book in books:
            self.add(book)

    def add(self, item: Book) -> None:
        if item.item_id in self._items:
            raise DuplicateIdError(item.item_id)
        self._items[item.item_id] = item
        self._category_index.setdefault(item.category, set()).add(item.item_id)

    def get(self, item_id: str) -> Book:
        try:
            return self._items[item_id]
        except KeyError as exc:
            raise EntityNotFoundError(item_id) from exc

    def remove(self, item_id: str) -> None:
        book = self.get(item_id)
        del self._items[item_id]

        ids_in_category = self._category_index.get(book.category)
        if ids_in_category is not None:
            ids_in_category.discard(item_id)
            if not ids_in_category:
                del self._category_index[book.category]

    def find_by_category(self, category: str) -> list[Book]:
        item_ids = self._category_index.get(category)
        if not item_ids:
            return []
        return [self._items[item_id] for item_id in self._items if item_id in item_ids]

    def find_by_name(self, query: str) -> list[Book]:
        normalized = query.lower()
        return [book for book in self._items.values() if normalized in book.name.lower()]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Book]:
        return iter(self._items.values())

    def __contains__(self, item_id: object) -> bool:
        return isinstance(item_id, str) and item_id in self._items


class ReadOnlyCatalogView:
    """Read-only wrapper over BookCatalog that blocks mutating operations."""

    __slots__ = ("_catalog",)
    _catalog: BookCatalog

    def __init__(self, catalog: BookCatalog) -> None:
        object.__setattr__(self, "_catalog", catalog)

    def get(self, item_id: str) -> Book:
        return self._catalog.get(item_id)

    def find_by_category(self, category: str) -> list[Book]:
        return self._catalog.find_by_category(category)

    def find_by_name(self, query: str) -> list[Book]:
        return self._catalog.find_by_name(query)

    def __len__(self) -> int:
        return len(self._catalog)

    def __iter__(self) -> Iterator[Book]:
        return iter(self._catalog)

    def __contains__(self, item_id: object) -> bool:
        return item_id in self._catalog

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ReadOnlyCatalogView is read-only")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("ReadOnlyCatalogView is read-only")


@dataclass(frozen=True)
class _UndoAction:
    kind: str  # "add" -> undo removes book; "remove" -> undo restores book
    book: Book


class UndoableBookCatalog(BookCatalog):
    """BookCatalog supporting undo for the last successful mutation."""

    def __init__(self, books: Iterable[Book] = ()) -> None:
        self._undo_stack: list[_UndoAction] = []
        super().__init__(books)
        self._undo_stack.clear()

    def add(self, item: Book) -> None:
        super().add(item)
        self._undo_stack.append(_UndoAction(kind="add", book=item))

    def remove(self, item_id: str) -> None:
        book = self.get(item_id)
        super().remove(item_id)
        self._undo_stack.append(_UndoAction(kind="remove", book=book))

    def undo(self) -> None:
        if not self._undo_stack:
            raise CatalogError("Nothing to undo")

        action = self._undo_stack.pop()
        if action.kind == "add":
            super().remove(action.book.item_id)
        elif action.kind == "remove":
            super().add(action.book)
