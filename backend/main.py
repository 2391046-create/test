from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import base64
import os
from datetime import datetime

from gemini_service import analyze_receipt, analyze_price_before_purchase
from xrpl_service import record_transaction_with_memo, get_transaction_info, get_account_balance, validate_wallet

app = FastAPI(
    title="Finance Compass Backend",
    description="유학생 재정 관리 및 XRPL 블록체인 연동 API",
    version="1.0.0"
)

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8081",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanReceiptRequest(BaseModel):
    image_base64: str
    target_country: str = "USD"

class AnalyzePriceRequest(BaseModel):
    image_base64: Optional[str] = None
    text: Optional[str] = None
    target_country: str = "USD"

class RecordXRPLRequest(BaseModel):
    expense_data: dict
    wallet_seed: Optional[str] = None

class TransactionInfoRequest(BaseModel):
    tx_hash: str

class WalletValidationRequest(BaseModel):
    wallet_seed: str

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Finance Compass Backend"
    }

@app.post("/scan-receipt")
async def scan_receipt(request: ScanReceiptRequest):
    """
    영수증 스캔 및 분석
    - 영수증 이미지를 Gemini AI로 분석
    - 상호명, 품목, 금액, 원화 환산, 더치페이 정산 정보 반환
    """
    try:
        result = analyze_receipt(request.image_base64, request.target_country)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-price")
async def analyze_price(request: AnalyzePriceRequest):
    """
    메뉴판/가격표 분석
    - 메뉴판 이미지 또는 텍스트를 분석
    - 메뉴명, 가격, 원화 환산, 평균가 비교 정보 반환
    """
    try:
        if request.image_base64:
            result = analyze_price_before_purchase(
                request.image_base64,
                request.target_country,
                is_image=True
            )
        elif request.text:
            result = analyze_price_before_purchase(
                request.text,
                request.target_country,
                is_image=False
            )
        else:
            raise ValueError("image_base64 또는 text 중 하나를 제공해야 합니다")
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record-xrpl")
async def record_xrpl(request: RecordXRPLRequest):
    """
    XRPL 블록체인에 거래 기록
    - 지출 내역을 XRPL Memo 필드에 JSON으로 저장
    - 트랜잭션 해시 반환
    """
    try:
        result = record_transaction_with_memo(
            request.wallet_seed,
            request.expense_data
        )
        
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xrpl/transaction-info")
async def xrpl_transaction_info(request: TransactionInfoRequest):
    """
    XRPL 트랜잭션 정보 조회
    """
    try:
        result = get_transaction_info(request.tx_hash)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/xrpl/account-balance")
async def xrpl_account_balance(account_address: Optional[str] = None):
    """
    XRPL 계정 잔액 조회
    """
    try:
        result = get_account_balance(account_address)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xrpl/validate-wallet")
async def xrpl_validate_wallet(request: WalletValidationRequest):
    """
    XRPL 지갑 유효성 검증
    """
    try:
        result = validate_wallet(request.wallet_seed)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Finance Compass Backend API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "scan_receipt": "/scan-receipt (POST)",
            "analyze_price": "/analyze-price (POST)",
            "record_xrpl": "/record-xrpl (POST)",
            "xrpl_transaction_info": "/xrpl/transaction-info (POST)",
            "xrpl_account_balance": "/xrpl/account-balance (GET)",
            "xrpl_validate_wallet": "/xrpl/validate-wallet (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
