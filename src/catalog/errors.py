"""Exception hierarchy for the catalog package."""

from pathlib import Path


class CatalogError(Exception):
    """Base exception for all catalog errors."""


class InvalidEntityError(CatalogError):
    """Raised when an entity violates domain invariants or has invalid fields."""

    def __init__(
        self,
        message: str = "Invalid entity",
        field: str | None = None,
    ) -> None:
        self.field = field
        detail = f"Invalid field '{field}': {message}" if field else message
        super().__init__(detail)


class DuplicateIdError(CatalogError):
    """Raised when attempting to add an entity with an existing ID."""

    def __init__(
        self,
        item_id: str,
        message: str = "Duplicate item ID",
    ) -> None:
        self.item_id = item_id
        super().__init__(f"{message}: '{item_id}'.")


class EntityNotFoundError(CatalogError):
    """Raised when an entity with the requested ID is not found."""

    def __init__(
        self,
        item_id: str,
        message: str = "Entity not found",
    ) -> None:
        self.item_id = item_id
        super().__init__(f"{message}: '{item_id}'.")


class UnsupportedVersionError(CatalogError):
    """Raised when a catalog file specifies an unsupported format version."""

    def __init__(
        self,
        version: object,
        supported_version: int = 1,
        message: str = "Unsupported format version",
    ) -> None:
        self.version = version
        self.supported_version = supported_version
        super().__init__(f"{message}: {version!r}. Supported version: {supported_version}.")


class CorruptedFileError(CatalogError):
    """Raised when a catalog file cannot be read, parsed, or has broken structure."""

    def __init__(
        self,
        message: str = "Corrupted catalog file",
        file_path: str | Path | None = None,
    ) -> None:
        self.file_path = str(file_path) if file_path is not None else None
        detail = f"[file: {self.file_path}] {message}" if self.file_path else message
        super().__init__(detail)
