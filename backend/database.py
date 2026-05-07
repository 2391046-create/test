"""
데이터베이스 연결 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from models import Base

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    데이터베이스 세션 생성
    FastAPI 의존성으로 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    데이터베이스 초기화
    모든 테이블 생성
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    데이터베이스 초기화 (개발용)
    모든 테이블 삭제
    """
    Base.metadata.drop_all(bind=engine)
