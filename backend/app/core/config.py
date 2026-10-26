import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "FleetOps AI"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./fleetops.db"
    
    # ChromaDB RAG Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    EMBEDDING_PROVIDER: str = "default"  # "default" (lightweight local), "chroma", "openai"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # LLM Settings (Optional - offline deterministic fallback enabled when not configured)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Langfuse Observability (Optional - graceful degradation when not configured)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Demo Operator Auth
    DEMO_OPERATOR_ROLE: str = "demo_operator"
    SUPERVISOR_ROLE: str = "supervisor"
    VIEWER_ROLE: str = "viewer"
    
    # Safety Thresholds
    BATTERY_DISPATCH_MIN_PCT: float = 30.0
    BATTERY_RTH_MIN_PCT: float = 20.0
    TELEMETRY_MAX_AGE_SECONDS: int = 60
    
    # Geofence Polygon for Flight Zone Alpha (Longitude, Latitude)
    # Default operational zone: bounding box between lat [37.770, 37.780], lon [-122.420, -122.410]
    GEOFENCE_MIN_LAT: float = 37.7700
    GEOFENCE_MAX_LAT: float = 37.7800
    GEOFENCE_MIN_LON: float = -122.4200
    GEOFENCE_MAX_LON: float = -122.4100
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
