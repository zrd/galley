"""
Global error handlers for the API.

Converts domain exceptions to appropriate HTTP responses.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    EntityNotFound,
    InvalidStateTransition,
)
from app.services import ConversionError, GenerationError
from app.storage import UnsafeStorageKey


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers with the FastAPI app."""

    @app.exception_handler(EntityNotFound)
    async def entity_not_found_handler(request: Request, exc: EntityNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidStateTransition)
    async def invalid_state_handler(request: Request, exc: InvalidStateTransition) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationError)
    async def authz_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConversionError)
    async def conversion_error_handler(request: Request, exc: ConversionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Document conversion failed."},
        )

    @app.exception_handler(GenerationError)
    async def generation_error_handler(request: Request, exc: GenerationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Ebook generation failed."},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UnsafeStorageKey)
    async def unsafe_storage_handler(request: Request, exc: UnsafeStorageKey) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )
