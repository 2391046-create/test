"""
FastAPI 메인 애플리케이션
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from config import settings
from database import get_db, init_db
from models import User, Transaction, Budget
from schemas import (
    ClassifyRequest, ClassifyResponse,
    RecordRequest, RecordResponse,
    TransactionResponse, TransactionListResponse,
    BudgetCreate, BudgetResponse, BudgetStatusResponse,
    UserCreate, UserResponse,
    ErrorResponse
)
from gemini_service import GeminiClassifier
from xrpl_service import xrpl_recorder

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Finance Compass Backend",
    description="유학생 재정 관리 및 XRPL 블록체인 연동 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 라이프사이클 이벤트 ============

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("Finance Compass Backend 시작")
    init_db()
    logger.info("데이터베이스 초기화 완료")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("Finance Compass Backend 종료")


# ============ 헬스 체크 ============

@app.get("/health", tags=["Health"])
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ============ 분류 API ============

@app.post(
    "/classify",
    response_model=ClassifyResponse,
    tags=["Classification"],
    summary="결제 내역 분류",
    description="결제 알림 텍스트 또는 영수증 이미지를 분석하여 자동 분류"
)
async def classify_expense(request: ClassifyRequest):
    """
    결제 내역 분류 API
    
    - **text**: 결제 알림 텍스트 (선택)
    - **image_url**: 영수증 이미지 URL (선택)
    - **image_base64**: 영수증 이미지 Base64 (선택)
    """
    try:
        if request.text:
            # 텍스트 분류
            result = GeminiClassifier.classify_text(request.text)
            return result
        
        elif request.image_base64:
            # Base64 이미지 분류
            result = GeminiClassifier.classify_image(request.image_base64)
            return result
        
        elif request.image_url:
            # URL 이미지 분류
            result = GeminiClassifier.classify_image_from_url(request.image_url)
            return result
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="text, image_url, 또는 image_base64 중 하나를 제공해야 합니다"
            )
    
    except Exception as e:
        logger.error(f"분류 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분류 실패: {str(e)}"
        )


# ============ 거래 기록 API ============

@app.post(
    "/record",
    response_model=RecordResponse,
    tags=["Transactions"],
    summary="거래 기록",
    description="분류된 지출 내역을 데이터베이스 및 XRPL에 기록"
)
async def record_transaction(
    request: RecordRequest,
    db: Session = Depends(get_db)
):
    """
    거래 기록 API
    
    - **merchant**: 상호명
    - **amount**: 금액
    - **currency**: 통화 (기본값: KRW)
    - **category**: 카테고리
    - **transaction_date**: 거래 날짜
    - **description**: 설명 (선택)
    - **record_on_blockchain**: XRPL에 기록할지 여부 (기본값: True)
    """
    try:
        # 기본 사용자 ID (실제로는 인증에서 가져와야 함)
        user_id = 1
        
        # 거래 기록 생성
        transaction = Transaction(
            user_id=user_id,
            merchant=request.merchant,
            amount=request.amount,
            currency=request.currency,
            category=request.category,
            description=request.description,
            transaction_date=request.transaction_date,
            confidence=0.95
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        xrpl_tx_hash = None
        xrpl_memo = None
        is_recorded_on_blockchain = False
        
        # XRPL에 기록
        if request.record_on_blockchain:
            xrpl_result = xrpl_recorder.record_transaction(
                merchant=request.merchant,
                amount=request.amount,
                currency=request.currency,
                category=request.category,
                description=request.description
            )
            
            if xrpl_result.get("success"):
                xrpl_tx_hash = xrpl_result.get("tx_hash")
                xrpl_memo = xrpl_result.get("memo_data")
                is_recorded_on_blockchain = True
                
                # 트랜잭션 업데이트
                transaction.xrpl_tx_hash = xrpl_tx_hash
                transaction.xrpl_memo = xrpl_memo
                transaction.is_recorded_on_blockchain = True
                db.commit()
        
        return RecordResponse(
            transaction_id=transaction.id,
            merchant=transaction.merchant,
            amount=transaction.amount,
            category=transaction.category,
            xrpl_tx_hash=xrpl_tx_hash,
            xrpl_memo=xrpl_memo,
            is_recorded_on_blockchain=is_recorded_on_blockchain,
            message=f"거래가 기록되었습니다 (ID: {transaction.id})"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"거래 기록 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"거래 기록 실패: {str(e)}"
        )


# ============ 거래 조회 API ============

@app.get(
    "/transactions",
    response_model=TransactionListResponse,
    tags=["Transactions"],
    summary="거래 목록 조회",
    description="사용자의 거래 내역 목록 조회"
)
async def get_transactions(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    db: Session = Depends(get_db)
):
    """
    거래 목록 조회 API
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수
    - **category**: 카테고리 필터 (선택)
    """
    try:
        # 기본 사용자 ID
        user_id = 1
        
        query = db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if category:
            query = query.filter(Transaction.category == category)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return TransactionListResponse(
            total=total,
            items=[TransactionResponse.from_orm(item) for item in items]
        )
    
    except Exception as e:
        logger.error(f"거래 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"거래 조회 실패: {str(e)}"
        )


# ============ 예산 API ============

@app.post(
    "/budgets",
    response_model=BudgetResponse,
    tags=["Budgets"],
    summary="예산 설정",
    description="월별 카테고리 예산 설정"
)
async def create_budget(
    request: BudgetCreate,
    db: Session = Depends(get_db)
):
    """
    예산 설정 API
    
    - **category**: 카테고리
    - **amount**: 예산 금액
    - **currency**: 통화 (기본값: KRW)
    - **month_year**: 월 (YYYY-MM 형식)
    """
    try:
        # 기본 사용자 ID
        user_id = 1
        
        budget = Budget(
            user_id=user_id,
            category=request.category,
            amount=request.amount,
            currency=request.currency,
            month_year=request.month_year
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
        return BudgetResponse.from_orm(budget)
    
    except Exception as e:
        db.rollback()
        logger.error(f"예산 설정 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예산 설정 실패: {str(e)}"
        )


@app.get(
    "/budgets/{month_year}",
    response_model=list[BudgetStatusResponse],
    tags=["Budgets"],
    summary="예산 상태 조회",
    description="월별 예산 상태 및 지출 현황 조회"
)
async def get_budget_status(
    month_year: str,
    db: Session = Depends(get_db)
):
    """
    예산 상태 조회 API
    
    - **month_year**: 월 (YYYY-MM 형식)
    """
    try:
        # 기본 사용자 ID
        user_id = 1
        
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month_year == month_year
        ).all()
        
        status_list = []
        for budget in budgets:
            # 해당 월의 거래 합계 계산
            spent = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.category == budget.category,
                Transaction.transaction_date >= f"{month_year}-01",
                Transaction.transaction_date < f"{int(month_year.split('-')[0])}-{int(month_year.split('-')[1])+1:02d}-01"
            ).with_entities(
                db.func.sum(Transaction.amount)
            ).scalar() or 0.0
            
            remaining = budget.amount - spent
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            
            if percentage > 100:
                status_str = "exceeded"
            elif percentage >= 80:
                status_str = "warning"
            else:
                status_str = "under"
            
            status_list.append(BudgetStatusResponse(
                category=budget.category,
                budget_amount=budget.amount,
                spent_amount=spent,
                remaining_amount=max(remaining, 0),
                percentage_used=percentage,
                status=status_str
            ))
        
        return status_list
    
    except Exception as e:
        logger.error(f"예산 상태 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예산 상태 조회 실패: {str(e)}"
        )


# ============ XRPL API ============

@app.get(
    "/xrpl/transactions/{tx_hash}",
    tags=["XRPL"],
    summary="XRPL 트랜잭션 조회",
    description="XRPL 블록체인에 기록된 트랜잭션 조회"
)
async def get_xrpl_transaction(tx_hash: str):
    """
    XRPL 트랜잭션 조회 API
    
    - **tx_hash**: 트랜잭션 해시
    """
    try:
        result = xrpl_recorder.get_transaction_status(tx_hash)
        return result
    
    except Exception as e:
        logger.error(f"XRPL 트랜잭션 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"XRPL 조회 실패: {str(e)}"
        )


@app.get(
    "/xrpl/account/transactions",
    tags=["XRPL"],
    summary="XRPL 계정 트랜잭션 목록",
    description="XRPL 계정의 최근 트랜잭션 목록 조회"
)
async def get_xrpl_account_transactions(limit: int = 10):
    """
    XRPL 계정 트랜잭션 목록 조회 API
    
    - **limit**: 조회할 트랜잭션 개수
    """
    try:
        result = xrpl_recorder.get_account_transactions(limit=limit)
        return result
    
    except Exception as e:
        logger.error(f"XRPL 계정 트랜잭션 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"XRPL 조회 실패: {str(e)}"
        )


# ============ 에러 핸들러 ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 핸들러"""
    logger.error(f"예상치 못한 오류: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "서버 오류가 발생했습니다"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
