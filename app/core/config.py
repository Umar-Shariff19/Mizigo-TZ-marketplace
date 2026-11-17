from dotenv import load_dotenv
import os
import sys

load_dotenv()

INSECURE_DEFAULT_SECRETS = {
    "supersecretkey123456789",
    "secret",
    "changeme",
    "password",
    "test-secret-key",
}


class Settings:
    """Application configuration loaded from environment variables."""

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://mizigo:mizigo@localhost:5432/mizigo")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123456789")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    @property
    def UPLOAD_DIR(self) -> str:
        return os.getenv("UPLOAD_DIR", "uploads")

    @property
    def PRODUCT_UPLOAD_DIR(self) -> str:
        return os.path.join(self.UPLOAD_DIR, "products")

    # Configurable CORS origins as comma-separated values
    _cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
    CORS_ORIGINS: list[str] = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate critical configuration, enforcing strong safeguards in production."""
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY in INSECURE_DEFAULT_SECRETS or len(self.SECRET_KEY) < 32:
                raise RuntimeError(
                    "Production configuration error: SECRET_KEY must be a cryptographically strong, "
                    "non-default secret at least 32 characters long."
                )
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise RuntimeError(
                    "Production configuration error: DATABASE_URL must be specified and point to a production database."
                )


settings = Settings()


