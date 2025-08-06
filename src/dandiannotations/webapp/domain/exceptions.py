"""
Custom exceptions for the DANDI annotations system.
"""


class ResourceError(Exception):
    """Base exception for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource cannot be found."""
    pass


class ResourceValidationError(ResourceError):
    """Raised when resource data validation fails."""
    pass


class ResourceStateError(ResourceError):
    """Raised when a resource operation is invalid for the current state."""
    pass


class DandisetNotFoundError(ResourceError):
    """Raised when a dandiset cannot be found."""
    pass


class RepositoryError(Exception):
    """Base exception for repository-related errors."""
    pass


class RepositoryIOError(RepositoryError):
    """Raised when file I/O operations fail."""
    pass


class RepositoryCorruptionError(RepositoryError):
    """Raised when data corruption is detected."""
    pass


class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass


class ValidationServiceError(ServiceError):
    """Raised when validation service operations fail."""
    pass


class PaginationError(ServiceError):
    """Raised when pagination parameters are invalid."""
    pass
