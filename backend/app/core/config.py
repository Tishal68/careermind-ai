import os
import secrets
from typing import List
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NexPath - AI Career Operating System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    UPLOAD_DIR: str = "./uploads/resumes"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./careermind.db"
    )

    # JWT Security
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret(cls, value):
        if len(value) < 32 or value in {"nexpath-super-secret-jwt-key-2026-production-ready", "careermind-super-secret-jwt-key-2026-production-ready", "replace-with-a-long-random-value"}:
            raise ValueError("SECRET_KEY must be a private random value of at least 32 characters.")
        return value

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # one hour; configurable

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Ollama AI
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_API_KEY: SecretStr = SecretStr("")
    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "ollama")

    # Fallback can send prompts to another provider; keep it opt-in.
    AI_FALLBACK_ENABLED: bool = False

    # Only configure verified proxy networks; forwarding headers are ignored otherwise.
    TRUSTED_PROXY_CIDRS: List[str] = []

    @field_validator("TRUSTED_PROXY_CIDRS")
    @classmethod
    def validate_proxy_networks(cls, values):
        import ipaddress
        for value in values:
            if ipaddress.ip_network(value).prefixlen == 0:
                raise ValueError("Do not trust the entire internet as a proxy network")
        return values

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @model_validator(mode="after")
    def production_secret(self):
        if self.ENVIRONMENT == "production" and "SECRET_KEY" not in self.model_fields_set:
            raise ValueError("Production requires an explicitly configured private SECRET_KEY.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
