class DomainError(Exception):
    """Base exception for domain errors."""

    pass


class InvalidStateTransition(DomainError):
    """Raised when an invalid state transition is attempted."""

    pass


class EntityNotFound(DomainError):
    """Base exception for entity not found errors."""

    pass


class AuthorNotFound(EntityNotFound):
    """Raised when an author is not found."""

    pass


class ManuscriptNotFound(EntityNotFound):
    """Raised when a manuscript is not found."""

    pass


class SampleNotFound(EntityNotFound):
    """Raised when a sample is not found."""

    pass


class EbookNotFound(EntityNotFound):
    """Raised when an ebook is not found."""

    pass


class GenreNotFound(EntityNotFound):
    pass


class TagNotFound(EntityNotFound):
    pass


class AuthenticationError(DomainError):
    """Raised for authentication failures."""

    pass


class AuthorizationError(DomainError):
    """Raised when user lacks permission for an action."""

    pass
