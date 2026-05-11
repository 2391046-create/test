"""
앱 설정 - .env 파일에서 자동 로드
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# backend 폴더의 .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Settings(BaseSettings):
    # Gemini API
    GEMINI_API_KEY: str = ""

    # ngrok
    NGROK_TOKEN: str = ""

    # XRPL
    XRPL_NETWORK_URL: str = "https://s.altnet.rippletest.net:51234"

    # SQLite DB (PostgreSQL 불필요)
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance_compass.db"

    # 환율 API (없어도 무료 fallback 사용)
    EXCHANGE_RATE_API_KEY: str = ""

    # 서버 포트
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
