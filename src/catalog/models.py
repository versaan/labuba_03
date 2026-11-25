from dataclasses import dataclass
from datetime import date

from .errors import InvalidEntityError


@dataclass(frozen=True)
class Book:
    item_id: str
    name: str
    category: str
    year: int
    author: str
    isbn: str

    def __post_init__(self) -> None:
        if type(self.year) is not int:
            raise InvalidEntityError(
                f"year must be an int, not {type(self.year)}",
                "year",
            )
        if self.year > date.today().year:
            raise InvalidEntityError(
                f"year cannot be greater than {date.today().year}",
                "year",
            )

        str_fields = (
            ("item_id", self.item_id),
            ("name", self.name),
            ("category", self.category),
            ("author", self.author),
            ("isbn", self.isbn),
        )
        for field_name, value in str_fields:
            if not isinstance(value, str):
                raise InvalidEntityError(
                    f"{field_name} must be a str, not {type(value)}",
                    field_name,
                )
            if not value.strip():
                raise InvalidEntityError(
                    f"{field_name} must not be empty or whitespace",
                    field_name,
                )
