"""
Finance Compass Backend - FastAPI 메인 서버
다국 영수증 인식, XRPL 블록체인, 거래 관리, 지갑 관리
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import uvicorn

# 서비스 임포트
from gemini_service import analyze_receipt, analyze_price_before_purchase
from xrpl_service import (
    record_transaction_with_memo,
    get_transaction_info,
    get_account_balance,
    validate_wallet
)

# ============ FastAPI 앱 설정 ============
app = FastAPI(
    title="Finance Compass Backend",
    description="유학생 재정 관리 및 XRPL 블록체인 연동 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Pydantic 스키마 ============

class ScanReceiptRequest(BaseModel):
    """영수증 스캔 요청"""
    image_base64: str
    target_country: str = "USD"


class AnalyzePriceRequest(BaseModel):
    """메뉴판 가격 분석 요청"""
    image_base64: Optional[str] = None
    text: Optional[str] = None
    target_country: str = "USD"


class RecordXRPLRequest(BaseModel):
    """XRPL 기록 요청"""
    expense_data: Dict[str, Any]
    wallet_seed: str


class TransactionInfoRequest(BaseModel):
    """트랜잭션 정보 조회 요청"""
    tx_hash: str


class WalletValidationRequest(BaseModel):
    """지갑 검증 요청"""
    wallet_seed: str


class CreateTransactionRequest(BaseModel):
    """거래 생성 요청"""
    user_id: str
    merchant_name: str
    amount: float
    currency: str
    category: str
    date: str
    description: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    wallet_seed: Optional[str] = None
    record_to_xrpl: bool = False


class UpdateTransactionRequest(BaseModel):
    """거래 수정 요청"""
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None


class CreateWalletRequest(BaseModel):
    """지갑 생성 요청"""
    user_id: str
    wallet_seed: str
    wallet_name: Optional[str] = None


class UserSettingsRequest(BaseModel):
    """사용자 설정 요청"""
    user_id: str
    default_currency: str
    preferred_country: str
    monthly_budget: Optional[float] = None


# ============ 인메모리 저장소 (임시) ============
# 실제 운영에서는 데이터베이스 사용
transactions_db: Dict[str, Dict[str, Any]] = {}
wallets_db: Dict[str, Dict[str, Any]] = {}
users_db: Dict[str, Dict[str, Any]] = {}
transaction_counter = 0


# ============ 헬스 체크 ============
@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Finance Compass Backend"
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Finance Compass Backend API",
        "version": "1.0.0",
        "endpoints": {
            "scanner": {
                "scan_receipt": "POST /scan-receipt",
                "analyze_price": "POST /analyze-price"
            },
            "transactions": {
                "create": "POST /transactions",
                "get": "GET /transactions/{transaction_id}",
                "list": "GET /transactions",
                "update": "PUT /transactions/{transaction_id}",
                "delete": "DELETE /transactions/{transaction_id}",
                "record_xrpl": "POST /transactions/{transaction_id}/record-xrpl"
            },
            "wallets": {
                "create": "POST /wallets",
                "list": "GET /wallets",
                "validate": "POST /wallets/validate",
                "balance": "GET /wallets/{wallet_id}/balance"
            },
            "settings": {
                "update": "PUT /users/{user_id}/settings",
                "get": "GET /users/{user_id}/settings"
            },
            "xrpl": {
                "transaction_info": "POST /xrpl/transaction-info",
                "account_balance": "GET /xrpl/account-balance",
                "validate_wallet": "POST /xrpl/validate-wallet"
            }
        }
    }


# ============ 영수증/메뉴판 스캐너 엔드포인트 ============

@app.post("/scan-receipt")
async def scan_receipt(request: ScanReceiptRequest):
    """
    영수증 스캔 및 분석
    - 영수증 이미지를 Gemini AI로 분석
    - 상호명, 품목, 금액, 원화 환산, 더치페이 정산 정보 반환
    """
    try:
        result = analyze_receipt(request.image_base64, request.target_country)
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
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
        
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 거래 관리 엔드포인트 ============

@app.post("/transactions")
async def create_transaction(request: CreateTransactionRequest):
    """거래 생성"""
    global transaction_counter
    try:
        transaction_counter += 1
        transaction_id = f"txn_{transaction_counter}"
        
        transaction = {
            "id": transaction_id,
            "user_id": request.user_id,
            "merchant_name": request.merchant_name,
            "amount": request.amount,
            "currency": request.currency,
            "category": request.category,
            "date": request.date,
            "description": request.description,
            "items": request.items or [],
            "created_at": datetime.utcnow().isoformat(),
            "xrpl_tx_hash": None
        }
        
        transactions_db[transaction_id] = transaction
        
        # XRPL에 기록할 경우
        if request.record_to_xrpl and request.wallet_seed:
            xrpl_result = record_transaction_with_memo(
                request.wallet_seed,
                {
                    "merchant_name": request.merchant_name,
                    "total_local": request.amount,
                    "currency": request.currency,
                    "category": request.category,
                    "date": request.date,
                    "items": request.items or []
                }
            )
            
            if xrpl_result.get("success"):
                transaction["xrpl_tx_hash"] = xrpl_result.get("tx_hash")
                transactions_db[transaction_id] = transaction
        
        return {
            "success": True,
            "data": transaction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions")
async def list_transactions(user_id: str = Query(...), skip: int = 0, limit: int = 100):
    """거래 목록 조회"""
    try:
        user_transactions = [
            txn for txn in transactions_db.values()
            if txn.get("user_id") == user_id
        ]
        return {
            "success": True,
            "data": user_transactions[skip:skip+limit],
            "total": len(user_transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """거래 상세 조회"""
    try:
        if transaction_id not in transactions_db:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        return {
            "success": True,
            "data": transactions_db[transaction_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, request: UpdateTransactionRequest):
    """거래 수정"""
    try:
        if transaction_id not in transactions_db:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        transaction = transactions_db[transaction_id]
        
        if request.category:
            transaction["category"] = request.category
        if request.description:
            transaction["description"] = request.description
        if request.amount:
            transaction["amount"] = request.amount
        
        transaction["updated_at"] = datetime.utcnow().isoformat()
        transactions_db[transaction_id] = transaction
        
        return {
            "success": True,
            "data": transaction
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """거래 삭제"""
    try:
        if transaction_id not in transactions_db:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        del transactions_db[transaction_id]
        
        return {
            "success": True,
            "message": "거래가 삭제되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/{transaction_id}/record-xrpl")
async def record_transaction_xrpl(transaction_id: str, wallet_seed: str = Query(...)):
    """거래를 XRPL에 기록"""
    try:
        if transaction_id not in transactions_db:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        transaction = transactions_db[transaction_id]
        
        xrpl_result = record_transaction_with_memo(
            wallet_seed,
            {
                "merchant_name": transaction.get("merchant_name"),
                "total_local": transaction.get("amount"),
                "currency": transaction.get("currency"),
                "category": transaction.get("category"),
                "date": transaction.get("date"),
                "items": transaction.get("items", [])
            }
        )
        
        if xrpl_result.get("success"):
            transaction["xrpl_tx_hash"] = xrpl_result.get("tx_hash")
            transactions_db[transaction_id] = transaction
            
            return {
                "success": True,
                "data": {
                    "transaction_id": transaction_id,
                    "tx_hash": xrpl_result.get("tx_hash")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=xrpl_result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 지갑 관리 엔드포인트 ============

@app.post("/wallets")
async def create_wallet(request: CreateWalletRequest):
    """지갑 생성"""
    try:
        # 지갑 검증
        validation = validate_wallet(request.wallet_seed)
        if not validation.get("success"):
            raise HTTPException(status_code=400, detail=validation.get("error"))
        
        wallet_id = f"wallet_{request.user_id}_{len(wallets_db)}"
        
        wallet = {
            "id": wallet_id,
            "user_id": request.user_id,
            "address": validation.get("address"),
            "public_key": validation.get("public_key"),
            "name": request.wallet_name or f"Wallet {len(wallets_db)+1}",
            "created_at": datetime.utcnow().isoformat()
        }
        
        wallets_db[wallet_id] = wallet
        
        return {
            "success": True,
            "data": wallet
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallets")
async def list_wallets(user_id: str = Query(...)):
    """사용자의 지갑 목록 조회"""
    try:
        user_wallets = [
            w for w in wallets_db.values()
            if w.get("user_id") == user_id
        ]
        return {
            "success": True,
            "data": user_wallets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallets/{wallet_id}/balance")
async def get_wallet_balance(wallet_id: str):
    """지갑 잔액 조회"""
    try:
        if wallet_id not in wallets_db:
            raise HTTPException(status_code=404, detail="지갑을 찾을 수 없습니다")
        
        wallet = wallets_db[wallet_id]
        balance_result = get_account_balance(wallet.get("address"))
        
        if balance_result.get("success"):
            return {
                "success": True,
                "data": {
                    "wallet_id": wallet_id,
                    "address": wallet.get("address"),
                    "balances": balance_result.get("balances")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=balance_result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wallets/validate")
async def validate_wallet_endpoint(request: WalletValidationRequest):
    """지갑 검증"""
    try:
        result = validate_wallet(request.wallet_seed)
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 사용자 설정 엔드포인트 ============

@app.put("/users/{user_id}/settings")
async def update_user_settings(user_id: str, request: UserSettingsRequest):
    """사용자 설정 업데이트"""
    try:
        if user_id not in users_db:
            users_db[user_id] = {}
        
        users_db[user_id].update({
            "user_id": user_id,
            "default_currency": request.default_currency,
            "preferred_country": request.preferred_country,
            "monthly_budget": request.monthly_budget,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "data": users_db[user_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/settings")
async def get_user_settings(user_id: str):
    """사용자 설정 조회"""
    try:
        if user_id not in users_db:
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "default_currency": "USD",
                    "preferred_country": "USA",
                    "monthly_budget": None
                }
            }
        
        return {
            "success": True,
            "data": users_db[user_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ XRPL 엔드포인트 ============

@app.post("/xrpl/transaction-info")
async def xrpl_transaction_info(request: TransactionInfoRequest):
    """XRPL 트랜잭션 정보 조회"""
    try:
        result = get_transaction_info(request.tx_hash)
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/xrpl/account-balance")
async def xrpl_account_balance(account_address: str = Query(...)):
    """XRPL 계정 잔액 조회"""
    try:
        result = get_account_balance(account_address)
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/xrpl/validate-wallet")
async def xrpl_validate_wallet(request: WalletValidationRequest):
    """XRPL 지갑 검증"""
    try:
        result = validate_wallet(request.wallet_seed)
        if result.get("success"):
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 서버 실행 ============
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
