from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Leadership Development Platform"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database - Neon PostgreSQL
    DATABASE_URL: Optional[str] = None
    
    # PostgreSQL specific settings (for development)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "leadership"
    POSTGRES_PASSWORD: str = "lead123"
    POSTGRES_DB: str = "leader_db"
    POSTGRES_PORT: str = "5432"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values) -> str:
        # If DATABASE_URL is provided (production), use it directly
        if isinstance(v, str) and v.strip():
            return v
        
        # Build PostgreSQL URL from components (development)
        return f"postgresql://{values.data.get('POSTGRES_USER', 'postgres')}:{values.data.get('POSTGRES_PASSWORD', 'password')}@{values.data.get('POSTGRES_SERVER', 'localhost')}:{values.data.get('POSTGRES_PORT', '5432')}/{values.data.get('POSTGRES_DB', 'fastapi_db')}"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Allowed hosts for trusted host middleware
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Email settings (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Redis settings (optional)
    REDIS_URL: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


settings = Settings()
