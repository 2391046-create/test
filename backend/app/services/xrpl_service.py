"""XRPL operations: wallet creation, payment, path payment"""
import asyncio
import binascii
from decimal import Decimal
from typing import Optional

from cryptography.fernet import Fernet
from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, RipplePathFind
from xrpl.models.transactions.offer_create import OfferCreate, OfferCreateFlag
from xrpl.models.transactions.payment import Payment, PaymentFlag
from xrpl.models.transactions.transaction import Memo
from xrpl.models.transactions.trust_set import TrustSet
from xrpl.transaction import submit_and_wait
from xrpl.utils import drops_to_xrp, xrp_to_drops
from xrpl.wallet import Wallet, generate_faucet_wallet

from app.config import settings


def _get_client() -> JsonRpcClient:
    return JsonRpcClient(settings.XRPL_TESTNET_URL)


def _get_fernet() -> Fernet:
    return Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_seed(seed: str) -> str:
    return _get_fernet().encrypt(seed.encode()).decode()


def decrypt_seed(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ── Sync XRPL helpers (wrapped with asyncio.to_thread) ──────────────────────

def _create_wallet_sync() -> dict:
    """Create new XRPL testnet wallet via faucet and fund with XRP"""
    client = _get_client()
    wallet = generate_faucet_wallet(client, debug=False)
    return {
        "address": wallet.address,
        "seed": wallet.seed,
        "public_key": wallet.public_key,
    }


def _set_trust_lines_sync(seed: str, currencies: list[str], issuer: str) -> list[str]:
    """Set IOU trust lines so the wallet can hold foreign currencies"""
    client = _get_client()
    wallet = Wallet.from_seed(seed)
    hashes = []
    for currency in currencies:
        tx = TrustSet(
            account=wallet.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer,
                value="10000000",
            ),
        )
        response = submit_and_wait(tx, client, wallet)
        hashes.append(response.result.get("hash", ""))
    return hashes


def _get_balances_sync(address: str) -> list[dict]:
    """Return XRP balance + all non-zero IOU balances from XRPL"""
    client = _get_client()
    balances = []

    try:
        info = client.request(AccountInfo(account=address, ledger_index="validated"))
        xrp_bal = drops_to_xrp(info.result["account_data"]["Balance"])
        balances.append({"currency": "XRP", "amount": str(xrp_bal), "issuer": None})
    except Exception:
        pass

    try:
        lines = client.request(AccountLines(account=address, ledger_index="validated"))
        for line in lines.result.get("lines", []):
            if Decimal(line["balance"]) != 0:
                balances.append({
                    "currency": line["currency"],
                    "amount": line["balance"],
                    "issuer": line["account"],
                })
    except Exception:
        pass

    return balances


def _send_payment_sync(
    sender_seed: str,
    recipient_address: str,
    amount: str,
    currency: str = "XRP",
    issuer: Optional[str] = None,
    memo_text: Optional[str] = None,
) -> dict:
    """F02: Submit a Payment transaction on XRPL"""
    client = _get_client()
    sender_wallet = Wallet.from_seed(sender_seed)

    if currency.upper() == "XRP":
        tx_amount = xrp_to_drops(Decimal(amount))
    else:
        if not issuer:
            raise ValueError("issuer is required for non-XRP payments")
        tx_amount = IssuedCurrencyAmount(
            currency=currency.upper(),
            issuer=issuer,
            value=amount,
        )

    kwargs: dict = {
        "account": sender_wallet.address,
        "destination": recipient_address,
        "amount": tx_amount,
    }

    if memo_text:
        hex_data = binascii.hexlify(memo_text.encode()).decode().upper()
        kwargs["memos"] = [Memo(memo_data=hex_data)]

    payment = Payment(**kwargs)
    response = submit_and_wait(payment, client, sender_wallet)

    tx_result = response.result.get("meta", {}).get("TransactionResult", "")
    return {
        "tx_hash": response.result.get("hash", ""),
        "status": "success" if tx_result == "tesSUCCESS" else "failed",
        "meta": response.result.get("meta", {}),
    }


def _get_best_rate_sync(from_currency: str, to_currency: str, issuer: str) -> Optional[Decimal]:
    """DEX 오더북에서 최우선 환율 조회 (to_currency per 1 from_currency)"""
    client = _get_client()
    fc, tc = from_currency.upper(), to_currency.upper()

    taker_gets = {"currency": "XRP"} if tc == "XRP" else {"currency": tc, "issuer": issuer}
    taker_pays = {"currency": "XRP"} if fc == "XRP" else {"currency": fc, "issuer": issuer}

    response = client.request(BookOffers(taker_gets=taker_gets, taker_pays=taker_pays, limit=5))
    offers = response.result.get("offers", [])
    if not offers:
        return None

    best = offers[0]
    gets = best["TakerGets"]
    pays = best["TakerPays"]

    gets_val = drops_to_xrp(gets) if isinstance(gets, str) else Decimal(str(gets["value"]))
    pays_val = drops_to_xrp(pays) if isinstance(pays, str) else Decimal(str(pays["value"]))

    if pays_val == 0:
        return None
    return gets_val / pays_val


def _parse_offer_balance_changes(meta: dict, account: str, to_currency: str) -> dict:
    """OfferCreate 메타데이터에서 실제 환전 금액 파싱"""
    xrp_delta = Decimal("0")
    iou_delta = Decimal("0")

    for wrapper in meta.get("AffectedNodes", []):
        node_type = next(iter(wrapper))
        node = wrapper[node_type]
        entry_type = node.get("LedgerEntryType", "")

        if entry_type == "AccountRoot":
            fields = node.get("FinalFields", node.get("NewFields", {}))
            prev = node.get("PreviousFields", {})
            if fields.get("Account") == account and "Balance" in prev:
                delta = Decimal(fields["Balance"]) - Decimal(prev["Balance"])
                xrp_delta += delta

        elif entry_type == "RippleState":
            final = node.get("FinalFields", node.get("NewFields", {}))
            prev = node.get("PreviousFields", {})
            if "Balance" not in prev:
                continue
            bal = final.get("Balance", {})
            if bal.get("currency", "") != to_currency.upper():
                continue
            low = final.get("LowLimit", {}).get("issuer", "")
            high = final.get("HighLimit", {}).get("issuer", "")
            if account not in (low, high):
                continue
            delta = Decimal(final["Balance"]["value"]) - Decimal(prev["Balance"]["value"])
            # RippleState balance sign: positive = LowLimit account holds it
            iou_delta += delta if account == low else -delta

    return {
        "xrp_delta": str(xrp_delta),
        "iou_delta": str(abs(iou_delta)),
    }


def _path_payment_sync(
    sender_seed: str,
    from_currency: str,
    from_max: str,
    to_currency: str,
    to_amount: Optional[str],
    issuer: str,
    slippage_pct: float = 1.0,
) -> dict:
    """F03: DEX 환전 — OfferCreate(TF_IMMEDIATE_OR_CANCEL)로 구현

    PathPayment self-payment은 XRPL 노드에 따라 tecPATH_PARTIAL이 발생하므로
    OfferCreate를 사용해 DEX에서 즉시 체결되도록 처리합니다.

    to_amount가 None이면 BookOffers로 현재 환율을 조회한 후
    from_max * rate * (1 - slippage_pct/100) 으로 자동 계산합니다.
    tecKILLED는 이 비율이 시장 환율과 맞지 않을 때 발생합니다.
    """
    # ── to_amount 자동 계산 ────────────────────────────────────────────────
    if not to_amount:
        rate = _get_best_rate_sync(from_currency, to_currency, issuer)
        if rate is None:
            raise ValueError(
                f"DEX에 {from_currency}→{to_currency} 오더가 없습니다. "
                "scripts/add_liquidity.py를 실행하여 유동성을 추가하세요."
            )
        slippage_factor = Decimal(str(1 - slippage_pct / 100))
        to_amount = str(
            (Decimal(from_max) * rate * slippage_factor).quantize(Decimal("0.000001"))
        )

    client = _get_client()
    sender_wallet = Wallet.from_seed(sender_seed)

    fc = from_currency.upper()
    tc = to_currency.upper()

    # taker_gets: 우리가 줄 통화 (from_max 한도)
    if fc == "XRP":
        taker_gets = xrp_to_drops(Decimal(from_max))
    else:
        taker_gets = IssuedCurrencyAmount(currency=fc, issuer=issuer, value=from_max)

    # taker_pays: 우리가 받을 통화 (to_amount 목표)
    if tc == "XRP":
        taker_pays = xrp_to_drops(Decimal(to_amount))
    else:
        taker_pays = IssuedCurrencyAmount(currency=tc, issuer=issuer, value=to_amount)

    # TF_IMMEDIATE_OR_CANCEL: DEX에 있는 오더와 즉시 체결, 남은 건 취소
    offer = OfferCreate(
        account=sender_wallet.address,
        taker_gets=taker_gets,
        taker_pays=taker_pays,
        flags=OfferCreateFlag.TF_IMMEDIATE_OR_CANCEL,
    )
    response = submit_and_wait(offer, client, sender_wallet)

    tx_result = response.result.get("meta", {}).get("TransactionResult", "")
    if tx_result != "tesSUCCESS":
        raise ValueError(f"XRPL 거래 실패: {tx_result}")

    meta = response.result.get("meta", {})
    changes = _parse_offer_balance_changes(meta, sender_wallet.address, tc)

    exchanged = changes["iou_delta"] if tc != "XRP" else str(
        abs(drops_to_xrp(str(int(Decimal(changes["xrp_delta"])))))
    )
    # 실제 소비된 XRP (음수 delta = 소비)
    spent_xrp = str(abs(drops_to_xrp(str(abs(int(Decimal(changes["xrp_delta"])))))))

    if Decimal(exchanged) == 0:
        raise ValueError(
            f"DEX 체결 실패: 환전된 금액이 0입니다. "
            f"add_liquidity.py 재실행 후 다시 시도하세요."
        )

    rate = None
    try:
        if fc == "XRP" and tc != "XRP" and Decimal(spent_xrp) > 0:
            # IOU per 1 XRP (e.g. 1 XRP = 1.5 USD → rate = "1.5")
            rate = str(Decimal(exchanged) / Decimal(spent_xrp))
        elif fc != "XRP" and tc == "XRP" and Decimal(exchanged) > 0:
            # XRP per 1 IOU
            rate = str(Decimal(spent_xrp) / Decimal(from_max))
    except Exception:
        pass

    return {
        "tx_hash": response.result.get("hash", ""),
        "status": "success",
        "exchanged_amount": exchanged if exchanged != "0" else to_amount,
        "spent_amount": spent_xrp if fc == "XRP" else from_max,
        "rate": rate,
        "meta": {},
    }


# ── Public async API ─────────────────────────────────────────────────────────

async def create_xrpl_wallet() -> dict:
    return await asyncio.to_thread(_create_wallet_sync)


async def set_trust_lines(seed: str, currencies: list[str], issuer: str) -> list[str]:
    return await asyncio.to_thread(_set_trust_lines_sync, seed, currencies, issuer)


async def get_account_balances(address: str) -> list[dict]:
    return await asyncio.to_thread(_get_balances_sync, address)


async def send_payment(
    sender_seed: str,
    recipient_address: str,
    amount: str,
    currency: str = "XRP",
    issuer: Optional[str] = None,
    memo_text: Optional[str] = None,
) -> dict:
    return await asyncio.to_thread(
        _send_payment_sync,
        sender_seed, recipient_address, amount, currency, issuer, memo_text,
    )


async def path_payment(
    sender_seed: str,
    from_currency: str,
    from_max: str,
    to_currency: str,
    to_amount: Optional[str],
    issuer: str,
    slippage_pct: float = 1.0,
) -> dict:
    return await asyncio.to_thread(
        _path_payment_sync,
        sender_seed, from_currency, from_max, to_currency, to_amount, issuer, slippage_pct,
    )


def _record_transaction_with_memo_sync(seed: str, expense_data: dict) -> dict:
    """지출 내역을 XRPL 자체 송금 트랜잭션의 Memo에 기록"""
    import json
    try:
        client = _get_client()
        wallet = Wallet.from_seed(seed)

        # 지출 데이터를 JSON으로 변환
        memo_json = json.dumps(expense_data, ensure_ascii=False)
        hex_data = binascii.hexlify(memo_json.encode("utf-8")).decode().upper()

        # 자체 송금 (1 drop XRP)
        payment = Payment(
            account=wallet.address,
            destination=wallet.address,
            amount=xrp_to_drops(Decimal("0.000001")),
            memos=[Memo(memo_data=hex_data)],
        )

        response = submit_and_wait(payment, client, wallet)
        tx_result = response.result.get("meta", {}).get("TransactionResult", "")

        return {
            "success": tx_result == "tesSUCCESS",
            "tx_hash": response.result.get("hash", ""),
            "status": "success" if tx_result == "tesSUCCESS" else "failed",
            "memo_data": expense_data,
            "ledger_index": response.result.get("ledger_index"),
            "account": wallet.address,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def record_transaction_with_memo(seed: str, expense_data: dict) -> dict:
    """지출 내역을 XRPL Memo에 기록 (async)"""
    return await asyncio.to_thread(_record_transaction_with_memo_sync, seed, expense_data)
