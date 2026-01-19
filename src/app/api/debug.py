from fastapi import APIRouter, Depends
from uuid import UUID
from app.security.auth import get_current_user_id

router = APIRouter()

@router.get("/whoami")
def whoami(user_id: UUID = Depends(get_current_user_id)):
    return {"user_id": user_id}
