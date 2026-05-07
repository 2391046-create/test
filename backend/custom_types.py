"""
타입 정의 (TypeScript와 호환)
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClassifyResult:
    """분류 결과"""
    merchant: str
    amount: float
    currency: str
    category: str
    confidence: float
    description: Optional[str] = None
    raw_analysis: Optional[str] = None


@dataclass
class TransactionRecord:
    """거래 기록"""
    id: int
    merchant: str
    amount: float
    currency: str
    category: str
    transaction_date: datetime
    xrpl_tx_hash: Optional[str] = None
    is_recorded_on_blockchain: bool = False
    confidence: float = 0.0


@dataclass
class BudgetInfo:
    """예산 정보"""
    category: str
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    percentage_used: float
    status: str  # "under", "warning", "exceeded"


@dataclass
class XRPLTransaction:
    """XRPL 트랜잭션"""
    tx_hash: str
    account: str
    destination: str
    amount: str
    memo_data: Dict[str, Any]
    status: str  # "pending", "confirmed", "failed"
    ledger_index: Optional[int] = None
    timestamp: Optional[datetime] = None


# API 응답 타입
class APIResponse:
    """API 응답 기본 클래스"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(error: str, status_code: int = 400) -> Dict[str, Any]:
        return {
            "success": False,
            "error": error,
            "status_code": status_code
        }
