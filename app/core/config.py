from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    SECRET_KEY: str | None = os.getenv("SECRET_KEY")
    ALGORITHM: str | None = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


settings = Settings()
