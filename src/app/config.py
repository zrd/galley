from uuid import UUID
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEV_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
    DEV_API_KEY: str = "dev-secret"
    ENVIRONMENT: str = "dev"

settings = Settings()
