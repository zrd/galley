from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Environment
    ENVIRONMENT: str = "dev"

    # Dev mode settings
    DEV_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
    DEV_API_KEY: str = "dev-secret"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/self_publishing"

    # JWT Auth
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""


settings = Settings()
