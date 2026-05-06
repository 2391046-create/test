"""
XRPL 블록체인 연동 모듈
지출 내역을 XRPL에 기록
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrpl_json_to_object
from config import settings

logger = logging.getLogger(__name__)


class XRPLRecorder:
    """XRPL 블록체인에 지출 내역을 기록"""
    
    def __init__(self):
        """XRPL 클라이언트 초기화"""
        self.client = JsonRpcClient(settings.XRPL_NETWORK_URL)
        self.wallet = None
        self.account = settings.XRPL_ACCOUNT_ADDRESS
        
        # 지갑 초기화
        if settings.XRPL_WALLET_SEED:
            try:
                self.wallet = Wallet.from_seed(settings.XRPL_WALLET_SEED)
                logger.info(f"XRPL 지갑 로드 성공: {self.wallet.address}")
            except Exception as e:
                logger.error(f"XRPL 지갑 로드 실패: {str(e)}")
    
    def create_expense_memo(
        self,
        merchant: str,
        amount: float,
        currency: str,
        category: str,
        description: Optional[str] = None
    ) -> str:
        """
        지출 정보를 XRPL Memo 필드용 JSON으로 생성
        
        Args:
            merchant: 상호명
            amount: 금액
            currency: 통화
            category: 카테고리
            description: 설명
            
        Returns:
            JSON 문자열
        """
        memo_data = {
            "type": "expense",
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "category": category,
            "description": description or "",
            "timestamp": datetime.utcnow().isoformat(),
            "app": "FinanceCompass"
        }
        
        return json.dumps(memo_data, ensure_ascii=False)
    
    def record_transaction(
        self,
        merchant: str,
        amount: float,
        currency: str,
        category: str,
        description: Optional[str] = None,
        destination_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        지출 내역을 XRPL에 기록
        
        Args:
            merchant: 상호명
            amount: 금액
            currency: 통화
            category: 카테고리
            description: 설명
            destination_address: 수신자 주소 (기본값: 자신의 계정)
            
        Returns:
            트랜잭션 결과
        """
        try:
            if not self.wallet:
                return {
                    "success": False,
                    "error": "XRPL 지갑이 초기화되지 않았습니다",
                    "tx_hash": None
                }
            
            # 메모 생성
            memo_json = self.create_expense_memo(
                merchant=merchant,
                amount=amount,
                currency=currency,
                category=category,
                description=description
            )
            
            # 메모를 16진수로 인코딩
            memo_hex = memo_json.encode('utf-8').hex().upper()
            
            # 트랜잭션 생성
            # 자신의 계정으로 자체 송금 (지출 기록용)
            destination = destination_address or self.wallet.address
            
            # XRP 최소 금액 (drops 단위: 1 XRP = 1,000,000 drops)
            xrp_amount = "1000"  # 0.001 XRP
            
            payment_tx = Payment(
                account=self.wallet.address,
                destination=destination,
                amount=xrp_amount,
                memos=[
                    {
                        "memo": {
                            "memo_data": memo_hex,
                            "memo_type": "4578706F7365",  # "Expose" in hex
                            "memo_format": "4A534F4E"  # "JSON" in hex
                        }
                    }
                ]
            )
            
            # 트랜잭션 제출
            response = submit_and_wait(payment_tx, self.client, self.wallet)
            
            # 결과 처리
            if response.is_successful():
                return {
                    "success": True,
                    "tx_hash": response.result.get("hash"),
                    "ledger_index": response.result.get("ledger_index"),
                    "memo_data": memo_json,
                    "message": f"지출 내역이 XRPL에 기록되었습니다 (TX: {response.result.get('hash')})"
                }
            else:
                return {
                    "success": False,
                    "error": response.result.get("error_message", "알 수 없는 오류"),
                    "tx_hash": None,
                    "memo_data": memo_json
                }
            
        except Exception as e:
            logger.error(f"XRPL 트랜잭션 오류: {str(e)}")
            return {
                "success": False,
                "error": f"XRPL 기록 실패: {str(e)}",
                "tx_hash": None
            }
    
    def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        트랜잭션 상태 조회
        
        Args:
            tx_hash: 트랜잭션 해시
            
        Returns:
            트랜잭션 상태
        """
        try:
            from xrpl.models.requests import Tx
            
            tx_request = Tx(transaction=tx_hash)
            response = self.client.request(tx_request)
            
            if response.is_successful():
                result = response.result
                return {
                    "success": True,
                    "status": "confirmed" if result.get("validated") else "pending",
                    "ledger_index": result.get("ledger_index"),
                    "timestamp": result.get("date"),
                    "hash": result.get("hash"),
                    "account": result.get("Account"),
                    "destination": result.get("Destination"),
                    "amount": result.get("Amount")
                }
            else:
                return {
                    "success": False,
                    "status": "not_found",
                    "error": response.result.get("error_message")
                }
            
        except Exception as e:
            logger.error(f"XRPL 트랜잭션 조회 오류: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    def get_account_transactions(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        계정의 최근 트랜잭션 목록 조회
        
        Args:
            limit: 조회할 트랜잭션 개수
            
        Returns:
            트랜잭션 목록
        """
        try:
            from xrpl.models.requests import AccountTx
            
            request = AccountTx(
                account=self.wallet.address if self.wallet else self.account,
                ledger_index="validated",
                limit=limit
            )
            response = self.client.request(request)
            
            if response.is_successful():
                transactions = []
                for tx_item in response.result.get("transactions", []):
                    tx = tx_item.get("tx", {})
                    transactions.append({
                        "hash": tx.get("hash"),
                        "account": tx.get("Account"),
                        "destination": tx.get("Destination"),
                        "amount": tx.get("Amount"),
                        "memos": tx.get("Memos", []),
                        "date": tx.get("date")
                    })
                
                return {
                    "success": True,
                    "transactions": transactions,
                    "count": len(transactions)
                }
            else:
                return {
                    "success": False,
                    "error": response.result.get("error_message")
                }
            
        except Exception as e:
            logger.error(f"XRPL 계정 트랜잭션 조회 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# 글로벌 XRPL 레코더 인스턴스
xrpl_recorder = XRPLRecorder()
