from .auth import router as auth_router
from .authors import router as authors_router
from .debug import router as debug_router
from .ebooks import router as ebooks_router
from .genres import router as genres_router
from .health import router as health_router
from .manuscripts import router as manuscripts_router
from .samples import router as samples_router

__all__ = [
    "auth_router",
    "authors_router",
    "debug_router",
    "ebooks_router",
    "genres_router",
    "health_router",
    "manuscripts_router",
    "samples_router",
]
