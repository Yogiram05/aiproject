"""
Configuration Management for Healthcare OCR System
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application Settings"""
    
    # Application
    APP_NAME: str = "Healthcare OCR System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    MODELS_DIR: Path = BASE_DIR / "models"
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg", "tiff"]
    
    # OCR Settings
    OCR_ENGINE: str = "paddleocr"
    OCR_LANGUAGE: str = "en,hi"
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    
    # Database
    DATABASE_URL: str = "sqlite:///./healthcare_ocr.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Privacy & Security
    ENABLE_PHI_REDACTION: bool = True
    AUDIT_LOG_ENABLED: bool = True
    ENCRYPTION_KEY: str = "change-this-in-production"
    
    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Processing
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 4
    
    # Claims
    CLAIMS_RULES_FILE: str = "./data/rules/insurance_rules.yaml"
    FRAUD_THRESHOLD: float = 0.75
    
    # Medical Codes
    ICD10_DATA_PATH: str = "./data/medical_codes/icd10_codes.json"
    LOINC_DATA_PATH: str = "./data/medical_codes/loinc_codes.json"
    SNOMED_DATA_PATH: str = "./data/medical_codes/snomed_codes.json"
    DRUG_DATABASE_PATH: str = "./data/medical_codes/drug_database.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Create necessary directories
for directory in [
    settings.UPLOAD_DIR,
    settings.OUTPUT_DIR,
    settings.MODELS_DIR,
    settings.DATA_DIR,
    settings.LOGS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
