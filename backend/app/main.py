"""
Finance Compass Backend - 메인 FastAPI 앱
SQLite 기반, .env에 GEMINI_API_KEY + NGROK_TOKEN만 넣으면 바로 실행
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import transactions, menu_scanner, wallets, users, exchange_rates


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Finance Compass Backend 시작 중...")
    await create_tables()
    print("✅ 준비 완료!")
    yield
    print("👋 서버 종료")


app = FastAPI(
    title="Finance Compass API",
    description="유학생 재정 관리 - 영수증 인식, XRPL, 환율, 예산 관리",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(transactions.router)
app.include_router(menu_scanner.router)
app.include_router(wallets.router)
app.include_router(users.router)
app.include_router(exchange_rates.router)


@app.get("/")
async def root():
    return {
        "service": "Finance Compass Backend",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "영수증 인식": "POST /api/transactions/analyze-receipt",
            "은행알림 인식": "POST /api/transactions/analyze-bank-notification",
            "거래 생성": "POST /api/transactions/create",
            "거래 목록": "GET /api/transactions/list?user_id=xxx",
            "거래 수정": "PUT /api/transactions/{id}",
            "PDF 보고서": "POST /api/transactions/generate-report",
            "XRPL 기록": "POST /api/transactions/{id}/record-xrpl?wallet_seed=xxx",
            "메뉴판 분석": "POST /api/menu/analyze",
            "지갑 연결": "POST /api/wallets/connect",
            "지갑 목록": "GET /api/wallets/list?user_id=xxx",
            "지갑 잔액": "GET /api/wallets/{id}/balance",
            "환율 조회": "GET /api/rates/",
            "특정환율": "GET /api/rates/USD",
            "사용자 생성": "POST /api/users/create",
            "설정 변경": "PUT /api/users/{id}/settings",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
