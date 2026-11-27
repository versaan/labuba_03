from datetime import date

import pytest

from catalog.errors import InvalidEntityError
from catalog.models import Book


def test_create_valid_book_and_strip_whitespace() -> None:
    book = Book(
        item_id="  b-101  ",
        name="  Clean Architecture  ",
        category="  Software  ",
        year=2017,
        author="  Robert C. Martin  ",
        isbn="  978-0134494166  ",
        edition=2,
    )

    assert book.item_id == "b-101"
    assert book.name == "Clean Architecture"
    assert book.category == "Software"
    assert book.year == 2017
    assert book.author == "Robert C. Martin"
    assert book.isbn == "978-0134494166"
    assert book.edition == 2


def test_book_is_frozen() -> None:
    book = Book("b-1", "Dune", "Sci-Fi", 1965, "Frank Herbert", "978-0441172719")

    with pytest.raises(AttributeError):
        book.name = "New Name"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "expected_field"),
    [
        (
            {
                "item_id": "   ",
                "name": "Dune",
                "category": "Sci-Fi",
                "year": 1965,
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
            },
            "item_id",
        ),
        (
            {
                "item_id": "b-1",
                "name": "",
                "category": "Sci-Fi",
                "year": 1965,
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
            },
            "name",
        ),
        (
            {
                "item_id": "b-1",
                "name": "Dune",
                "category": "  ",
                "year": 1965,
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
            },
            "category",
        ),
        (
            {
                "item_id": "b-1",
                "name": "Dune",
                "category": "Sci-Fi",
                "year": date.today().year + 1,
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
            },
            "year",
        ),
        (
            {
                "item_id": "b-1",
                "name": "Dune",
                "category": "Sci-Fi",
                "year": "1965",
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
            },
            "year",
        ),
        (
            {
                "item_id": "b-1",
                "name": "Dune",
                "category": "Sci-Fi",
                "year": 1965,
                "author": "Frank Herbert",
                "isbn": "978-0441172719",
                "edition": 0,
            },
            "edition",
        ),
    ],
)
def test_invalid_book_raises_invalid_entity_error(kwargs: dict, expected_field: str) -> None:
    with pytest.raises(InvalidEntityError) as exc_info:
        Book(**kwargs)

    assert exc_info.value.field == expected_field
