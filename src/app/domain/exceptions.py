class DomainError(Exception):
    pass


class InvalidStateTransition(DomainError):
    pass


class DocumentNotFound(DomainError):
    pass
