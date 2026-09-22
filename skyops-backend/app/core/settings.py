from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "SkyOps Flight & Gate Operations"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database — defaults to SQLite for local development/testing, or PostgreSQL if configured
    DATABASE_URL: str = "sqlite:///./skyops.db"
    
    # Supabase / JWT Authentication
    SUPABASE_JWT_SECRET: str = "skyops-jwt-secret-key-for-development"
    SUPABASE_URL: str = "https://example.supabase.co"

    # Integrations
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_TIMEOUT_SECONDS: float = 8.0
    WEATHER_API_KEY: str = ""
    PREDICTOR_SERVICE_URL: str = "http://localhost:8001"

    # Operational buffers (research-informed domain configuration)
    BUFFER_BEFORE_MINUTES: int = 15
    BUFFER_AFTER_MINUTES: int = 15
    MIN_TURNAROUND_MINUTES: int = 45

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
