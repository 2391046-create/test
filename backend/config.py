"""
환경 설정 관리 모듈
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finance_compass"
    )
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # XRPL
    XRPL_NETWORK_URL: str = os.getenv(
        "XRPL_NETWORK_URL",
        "https://s.altnet.rippletest.net:51234"
    )
    XRPL_WALLET_SEED: str = os.getenv("XRPL_WALLET_SEED", "")
    XRPL_ACCOUNT_ADDRESS: str = os.getenv("XRPL_ACCOUNT_ADDRESS", "")
    
    # 서버
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:8000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
