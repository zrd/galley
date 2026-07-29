"""
Debug endpoints - only available in dev environment.
"""

from fastapi import APIRouter

from app.security.auth import CurrentAuthorId

router = APIRouter()


@router.get("/whoami")
def whoami(author_id: CurrentAuthorId) -> dict[str, str]:
    """Return the current authenticated author's ID."""
    return {"author_id": str(author_id)}
