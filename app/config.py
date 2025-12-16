"""Application configuration settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_title: str = "UVA AI Course Assistant"
    debug: bool = False
    
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_embedding_model: str = "models/gemini-embedding-001"  # Best: up to 3072 dims, multilingual
    
    # Vector Database
    chroma_persist_dir: str = "./data/chroma"
    
    # SIS API
    sis_api_base_url: str = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    templates_dir: Path = base_dir / "templates"
    static_dir: Path = base_dir / "static"
    data_dir: Path = base_dir / "data"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars like old OPENAI_API_KEY


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

