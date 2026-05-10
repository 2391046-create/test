"""
XRPL 블록체인 연동 서비스
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.memos import Memo, MemoData
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

# XRPL 설정
XRPL_NETWORK_URL = os.getenv("XRPL_NETWORK_URL", "https://s.altnet.rippletest.net:51234")
client = JsonRpcClient(XRPL_NETWORK_URL)


def record_transaction_with_memo(
    wallet_seed: str,
    expense_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    XRPL에 거래 기록 (Memo 필드에 JSON 저장)
    """
    try:
        # 지갑 생성
        wallet = Wallet.from_seed(wallet_seed)
        
        # Memo 데이터 생성
        memo_data = {
            "type": "expense",
            "merchant": expense_data.get("merchant_name", ""),
            "amount": expense_data.get("total_local", 0),
            "currency": expense_data.get("currency", "USD"),
            "category": expense_data.get("category", "other"),
            "date": expense_data.get("date", ""),
            "items": expense_data.get("items", []),
            "dutch_pay": expense_data.get("dutch_pay_per_person", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        memo_json = json.dumps(memo_data, ensure_ascii=False)
        memo_hex = memo_json.encode('utf-8').hex().upper()
        
        # Memo 객체 생성
        memo = Memo(
            memo_data=MemoData(data=memo_hex)
        )
        
        # Payment 트랜잭션 생성 (자신에게 전송하여 Memo 기록)
        payment = Payment(
            account=wallet.address,
            destination=wallet.address,
            amount="1",
            memos=[memo],
            fee="12",
        )
        
        # 트랜잭션 제출
        response = submit_and_wait(payment, client, wallet)
        
        if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
            return {
                "success": True,
                "tx_hash": response.result.get("hash", ""),
                "account": wallet.address,
                "memo": memo_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "success": False,
                "error": response.result.get("meta", {}).get("TransactionResult", "Unknown error")
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"XRPL 기록 오류: {str(e)}"
        }


def get_transaction_info(tx_hash: str) -> Dict[str, Any]:
    """
    XRPL 트랜잭션 정보 조회
    """
    try:
        response = client.request({
            "method": "tx",
            "transaction": tx_hash,
        })
        
        result = response.result
        
        # Memo 데이터 추출
        memo_data = None
        if "Memos" in result and len(result["Memos"]) > 0:
            try:
                memo_hex = result["Memos"][0]["Memo"]["MemoData"]
                memo_text = bytes.fromhex(memo_hex).decode('utf-8')
                memo_data = json.loads(memo_text)
            except:
                memo_data = None
        
        return {
            "success": True,
            "tx_hash": tx_hash,
            "account": result.get("Account", ""),
            "destination": result.get("Destination", ""),
            "amount": result.get("Amount", ""),
            "fee": result.get("Fee", ""),
            "ledger_index": result.get("ledger_index", ""),
            "status": "confirmed" if result.get("meta", {}).get("TransactionResult") == "tesSUCCESS" else "failed",
            "memo": memo_data,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"트랜잭션 조회 오류: {str(e)}"
        }


def get_account_balance(account_address: str) -> Dict[str, Any]:
    """
    XRPL 계정 잔액 조회
    """
    try:
        response = client.request({
            "method": "account_info",
            "account": account_address,
        })
        
        result = response.result["account_data"]
        
        balance_drops = result.get("Balance", 0)
        balance_xrp = int(balance_drops) / 1_000_000
        
        return {
            "success": True,
            "account": account_address,
            "balance_xrp": balance_xrp,
            "balance_drops": balance_drops,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"잔액 조회 오류: {str(e)}"
        }


def validate_wallet(wallet_seed: str) -> Dict[str, Any]:
    """
    XRPL 지갑 유효성 검증
    """
    try:
        wallet = Wallet.from_seed(wallet_seed)
        return {
            "success": True,
            "address": wallet.address,
            "public_key": wallet.public_key,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"지갑 검증 오류: {str(e)}"
        }
