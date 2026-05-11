"""
XRPL 블록체인 서비스 - 거래 기록, 지갑 관리
"""
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional

from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.requests import AccountInfo
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.core import keypairs

from app.config import settings

# XRPL 클라이언트
_client = JsonRpcClient(settings.XRPL_NETWORK_URL)


def get_client():
    return _client


def validate_wallet(wallet_seed: str) -> Dict[str, Any]:
    """지갑 seed 검증 및 주소 추출"""
    try:
        wallet = Wallet.from_seed(wallet_seed)
        return {
            "success": True,
            "address": wallet.address,
            "public_key": wallet.public_key,
        }
    except Exception as e:
        return {"success": False, "error": f"지갑 검증 실패: {str(e)}"}


def get_account_balance(address: str) -> Dict[str, Any]:
    """XRPL 계정 잔액 조회"""
    try:
        req = AccountInfo(account=address, ledger_index="validated")
        response = _client.request(req)

        if response.is_successful():
            balance_drops = int(response.result["account_data"]["Balance"])
            balance_xrp = balance_drops / 1_000_000
            return {
                "success": True,
                "address": address,
                "balance_xrp": balance_xrp,
                "balance_drops": balance_drops,
            }
        else:
            return {"success": False, "error": "계정을 찾을 수 없습니다 (아직 활성화되지 않은 계정일 수 있습니다)"}
    except Exception as e:
        return {"success": False, "error": f"잔액 조회 실패: {str(e)}"}


def record_transaction_on_xrpl(wallet_seed: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    거래 내역을 XRPL에 Memo로 기록
    - wallet_seed: XRPL 지갑 seed
    - expense_data: 기록할 거래 데이터
    """
    try:
        wallet = Wallet.from_seed(wallet_seed)

        # Memo 데이터 (최대 1KB 권장)
        memo_payload = {
            "app": "FinanceCompass",
            "type": "expense",
            "merchant": expense_data.get("merchant_name", "")[:50],
            "amount": expense_data.get("amount_local", 0),
            "currency": expense_data.get("currency", "USD"),
            "category": expense_data.get("category", "other"),
            "date": expense_data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "id": expense_data.get("transaction_id", ""),
        }

        memo_json = json.dumps(memo_payload, ensure_ascii=False)
        memo_hex = memo_json.encode("utf-8").hex().upper()

        # Payment 트랜잭션 (자신에게 1 drop = 0.000001 XRP)
        payment = Payment(
            account=wallet.address,
            destination=wallet.address,
            amount="1",
            memos=[{
                "Memo": {
                    "MemoData": memo_hex,
                    "MemoType": "46696e616e6365436f6d70617373",  # "FinanceCompass" hex
                }
            }],
        )

        response = submit_and_wait(payment, _client, wallet)
        result = response.result

        if result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
            return {
                "success": True,
                "tx_hash": result.get("hash", ""),
                "account": wallet.address,
                "ledger_index": result.get("ledger_index"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            tx_result = result.get("meta", {}).get("TransactionResult", "Unknown")
            return {"success": False, "error": f"XRPL 트랜잭션 실패: {tx_result}"}

    except Exception as e:
        return {"success": False, "error": f"XRPL 기록 오류: {str(e)}"}


def get_transaction_info(tx_hash: str) -> Dict[str, Any]:
    """XRPL 트랜잭션 조회"""
    try:
        from xrpl.models.requests import Tx
        req = Tx(transaction=tx_hash)
        response = _client.request(req)

        if response.is_successful():
            result = response.result
            # Memo 디코딩
            memo_data = None
            memos = result.get("Memos", [])
            if memos:
                try:
                    raw = memos[0]["Memo"]["MemoData"]
                    memo_data = json.loads(bytes.fromhex(raw).decode("utf-8"))
                except:
                    pass

            return {
                "success": True,
                "tx_hash": tx_hash,
                "account": result.get("Account"),
                "status": "confirmed",
                "memo": memo_data,
                "ledger_index": result.get("ledger_index"),
            }
        else:
            return {"success": False, "error": "트랜잭션을 찾을 수 없습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}
