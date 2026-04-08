"""Project-wide custom exception types for JBT data service."""


class DataServiceError(Exception):
    """Base class for all JBT data service exceptions."""


class DataError(DataServiceError):
    """Raised when data acquisition or parsing fails."""


class StorageError(DataServiceError):
    """Raised when data storage operations fail."""


class ConfigError(DataServiceError):
    """Raised when configuration loading or validation fails."""
