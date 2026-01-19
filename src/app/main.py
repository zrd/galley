from fastapi import FastAPI
from app.api.documents import router as documents_router
from app.api.debug import router as debug_router
from app.config import settings

app = FastAPI()
app.include_router(documents_router, prefix="/documents", tags=["documents"])

if settings.ENVIRONMENT == "dev":
    app.include_router(debug_router, prefix="/debug", tags=["debug"])
