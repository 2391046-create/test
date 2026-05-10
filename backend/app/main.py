from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import users, wallets, transactions, menu_scanner, user_settings, wallets_extended


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="LivingFund API",
    description="유학생 생활비 금융 서비스 — XRPL 기반",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(wallets_extended.router)
app.include_router(transactions.router)
app.include_router(menu_scanner.router)
app.include_router(user_settings.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
