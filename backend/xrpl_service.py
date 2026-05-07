from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.memos import Memo, MemoData
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

XRPL_NETWORK_URL = os.getenv("XRPL_NETWORK_URL", "https://s.altnet.rippletest.net:51234")
XRPL_WALLET_SEED = os.getenv("XRPL_WALLET_SEED")
XRPL_ACCOUNT_ADDRESS = os.getenv("XRPL_ACCOUNT_ADDRESS")

client = JsonRpcClient(XRPL_NETWORK_URL)

def record_transaction_with_memo(wallet_seed: Optional[str] = None, expense_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    XRPL 테스트넷에 거래 기록 저장
    Memo 필드에 지출 내역을 JSON 문자열로 저장
    성공 시 Tx Hash 반환
    """
    try:
        if not wallet_seed:
            wallet_seed = XRPL_WALLET_SEED
        if not wallet_seed:
            return {
                "success": False,
                "error": "Wallet seed not provided",
                "tx_hash": None,
            }
        
        wallet = Wallet.from_seed(wallet_seed)
        
        if not expense_data:
            expense_data = {}
        
        memo_data = {
            "type": "expense",
            "merchant": expense_data.get("merchant", "Unknown"),
            "amount": expense_data.get("amount", 0.0),
            "currency": expense_data.get("currency", "KRW"),
            "category": expense_data.get("category", "other"),
            "description": expense_data.get("description", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "app": "FinanceCompass",
        }
        
        if "dutch_pay" in expense_data:
            memo_data["dutch_pay"] = expense_data["dutch_pay"]
        
        memo_json = json.dumps(memo_data, ensure_ascii=False)
        memo_hex = memo_json.encode('utf-8').hex().upper()
        
        memo = Memo(
            memo_data=MemoData(data=memo_hex)
        )
        
        payment = Payment(
            account=wallet.address,
            destination=wallet.address,
            amount="1",
            memos=[memo],
            sequence=None,
            fee="12",
        )
        
        response = submit_and_wait(payment, client, wallet)
        
        if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
            return {
                "success": True,
                "tx_hash": response.result.get("hash"),
                "ledger_index": response.result.get("ledger_index"),
                "timestamp": datetime.utcnow().isoformat(),
                "memo_data": memo_data,
                "account": wallet.address,
            }
        else:
            return {
                "success": False,
                "error": response.result.get("meta", {}).get("TransactionResult", "Unknown error"),
                "tx_hash": None,
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tx_hash": None,
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
        
        memo_data = None
        if "Memos" in result and len(result["Memos"]) > 0:
            memo_hex = result["Memos"][0]["Memo"]["MemoData"]
            try:
                memo_data = json.loads(bytes.fromhex(memo_hex).decode('utf-8'))
            except:
                memo_data = {"raw": memo_hex}
        
        return {
            "success": True,
            "tx_hash": tx_hash,
            "account": result.get("Account"),
            "destination": result.get("Destination"),
            "amount": result.get("Amount"),
            "fee": result.get("Fee"),
            "ledger_index": result.get("ledger_index"),
            "timestamp": result.get("date"),
            "status": "confirmed" if result.get("meta", {}).get("TransactionResult") == "tesSUCCESS" else "failed",
            "memo_data": memo_data,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tx_hash": tx_hash,
        }

def get_account_balance(account_address: Optional[str] = None) -> Dict[str, Any]:
    """
    XRPL 계정 잔액 조회
    """
    try:
        if not account_address:
            account_address = XRPL_ACCOUNT_ADDRESS
        if not account_address:
            return {
                "success": False,
                "error": "Account address not provided",
            }
        
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
            "flags": result.get("Flags"),
            "sequence": result.get("Sequence"),
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
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
            "error": str(e),
        }
