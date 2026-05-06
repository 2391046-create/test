"""
Pydantic 스키마 정의
API 요청/응답 데이터 검증
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 거래 관련 스키마 ============

class TransactionCreate(BaseModel):
    """거래 생성 요청"""
    merchant: str = Field(..., description="상호명")
    amount: float = Field(..., gt=0, description="금액")
    currency: str = Field(default="KRW", description="통화")
    category: str = Field(..., description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    transaction_date: datetime = Field(..., description="거래 날짜")
    raw_text: Optional[str] = Field(None, description="원본 텍스트")
    confidence: float = Field(default=0.0, description="신뢰도")


class TransactionResponse(BaseModel):
    """거래 응답"""
    id: int
    user_id: int
    merchant: str
    amount: float
    currency: str
    category: str
    description: Optional[str]
    transaction_date: datetime
    created_at: datetime
    xrpl_tx_hash: Optional[str]
    is_recorded_on_blockchain: bool
    confidence: float
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """거래 목록 응답"""
    total: int
    items: List[TransactionResponse]


# ============ 분류 관련 스키마 ============

class ClassifyRequest(BaseModel):
    """분류 요청"""
    text: Optional[str] = Field(None, description="결제 알림 텍스트")
    image_url: Optional[str] = Field(None, description="영수증 이미지 URL")
    image_base64: Optional[str] = Field(None, description="영수증 이미지 (Base64)")


class ClassifyResponse(BaseModel):
    """분류 응답"""
    merchant: str = Field(..., description="상호명")
    amount: float = Field(..., description="금액")
    currency: str = Field(..., description="통화")
    category: str = Field(..., description="카테고리")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    description: Optional[str] = Field(None, description="설명")
    raw_analysis: Optional[str] = Field(None, description="AI 분석 결과")


# ============ 기록 관련 스키마 ============

class RecordRequest(BaseModel):
    """거래 기록 요청"""
    merchant: str = Field(..., description="상호명")
    amount: float = Field(..., gt=0, description="금액")
    currency: str = Field(default="KRW", description="통화")
    category: str = Field(..., description="카테고리")
    transaction_date: datetime = Field(..., description="거래 날짜")
    description: Optional[str] = Field(None, description="설명")
    record_on_blockchain: bool = Field(default=True, description="XRPL에 기록할지 여부")


class RecordResponse(BaseModel):
    """거래 기록 응답"""
    transaction_id: int
    merchant: str
    amount: float
    category: str
    xrpl_tx_hash: Optional[str] = None
    xrpl_memo: Optional[str] = None
    is_recorded_on_blockchain: bool
    message: str


# ============ 예산 관련 스키마 ============

class BudgetCreate(BaseModel):
    """예산 생성 요청"""
    category: str = Field(..., description="카테고리")
    amount: float = Field(..., gt=0, description="예산 금액")
    currency: str = Field(default="KRW", description="통화")
    month_year: str = Field(..., description="월 (YYYY-MM 형식)")


class BudgetResponse(BaseModel):
    """예산 응답"""
    id: int
    category: str
    amount: float
    currency: str
    month_year: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    """예산 상태 응답"""
    category: str
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    percentage_used: float
    status: str  # "under", "warning", "exceeded"


# ============ XRPL 관련 스키마 ============

class XRPLRecordResponse(BaseModel):
    """XRPL 기록 응답"""
    tx_hash: str
    account: str
    destination: str
    amount: str
    memo_data: str
    status: str
    ledger_index: Optional[int]
    created_at: datetime
    confirmed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ 사용자 관련 스키마 ============

class UserCreate(BaseModel):
    """사용자 생성 요청"""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., description="이메일")
    password: str = Field(..., min_length=8, description="비밀번호")


class UserResponse(BaseModel):
    """사용자 응답"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ 통합 응답 스키마 ============

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool
    message: str
    data: Optional[dict] = None
