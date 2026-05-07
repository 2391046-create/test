"""
XRPL Testnet 이슈어 + DEX 오더북 셋업 스크립트
(AMM 대신 OfferCreate — 더 안정적이고 PathPayment와 완전 호환)

실행: python scripts/setup_issuer.py
출력된 XRPL_ISSUER_ADDRESS, XRPL_ISSUER_SEED를 backend/.env에 저장하세요.
"""
from decimal import Decimal

from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import AccountSet, OfferCreate, Payment, TrustSet
from xrpl.models.transactions.account_set import AccountSetAsfFlag
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops
from xrpl.wallet import generate_faucet_wallet

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

# 테스트용 환율: 1 XRP = ? 통화
XRP_RATES = {
    "USD": Decimal("1.5"),
    "EUR": Decimal("1.3"),
    "KRW": Decimal("1800"),
}

# MM이 보유할 IOU 수량 (충분히 크게)
IOU_SUPPLY = {
    "USD": "2500",
    "EUR": "2500",
    "KRW": "2500000",
}

# XRP→IOU 오더: MM이 팔 IOU 수량
XRP_TO_IOU_OFFER = {
    "USD": "2000",
    "EUR": "2000",
    "KRW": "2000000",
}

# IOU→XRP 오더: MM이 줄 XRP 수량 (소량, 역방향 경로 지원용)
IOU_TO_XRP_OFFER_XRP = {
    "USD": "80",
    "EUR": "80",
    "KRW": "80",
}

# IOU→XRP 오더의 스프레드: 동일 환율로 두 오더를 같은 계정에서 생성하면
# XRPL이 self-crossing offer로 인식해 먼저 생성된 오더를 자동 취소함.
# 5% 스프레드를 적용해 두 오더가 겹치지 않게 방지.
REVERSE_OFFER_SPREAD = Decimal("1.05")


def fund_wallet(client: JsonRpcClient, label: str):
    print(f"  [{label}] testnet faucet에서 지갑 생성 중...")
    w = generate_faucet_wallet(client, debug=False)
    print(f"  [{label}] address={w.address}")
    return w


def main():
    client = JsonRpcClient(TESTNET_URL)
    print("=== LivingFund XRPL Testnet 셋업 시작 ===\n")

    # ── 1) 이슈어 지갑 생성 ──────────────────────────────────────────────
    print("[1/4] 이슈어 지갑 생성")
    issuer = fund_wallet(client, "issuer")

    acct_set = AccountSet(
        account=issuer.address,
        set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,
    )
    submit_and_wait(acct_set, client, issuer)
    print("  Default Ripple 활성화 완료")

    # ── 2) 마켓메이커(MM) 지갑 생성 ─────────────────────────────────────
    print("\n[2/4] 마켓메이커 지갑 생성")
    mm = fund_wallet(client, "MM")

    # ── 3) MM TrustLine 설정 + IOU 발행 ─────────────────────────────────
    print("\n[3/4] TrustLine 설정 및 IOU 발행")
    for currency, supply in IOU_SUPPLY.items():
        trust = TrustSet(
            account=mm.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value="100000000",
            ),
        )
        submit_and_wait(trust, client, mm)

        payment = Payment(
            account=issuer.address,
            destination=mm.address,
            amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value=supply,
            ),
        )
        submit_and_wait(payment, client, issuer)
        print(f"  {currency}: {supply} 발행 완료")

    # ── 4) DEX 양방향 오더 생성 ─────────────────────────────────────────
    print("\n[4/4] DEX 오더 생성 (XRP ↔ USD/EUR/KRW 양방향)")

    for currency in XRP_RATES:
        rate = XRP_RATES[currency]

        # 오더 A — XRP → IOU
        # taker가 XRP를 주면 MM이 IOU를 줌 → PathPayment XRP→IOU 지원
        iou_offer_amt = XRP_TO_IOU_OFFER[currency]
        xrp_pays = Decimal(iou_offer_amt) / rate  # MM이 받을 XRP

        offer_a = OfferCreate(
            account=mm.address,
            taker_gets=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value=iou_offer_amt,
            ),
            taker_pays=xrp_to_drops(xrp_pays),
        )
        resp_a = submit_and_wait(offer_a, client, mm)
        res_a = resp_a.result.get("meta", {}).get("TransactionResult", "?")
        print(f"  XRP→{currency}: {res_a}  (1 XRP = {rate} {currency})")

        # 오더 B — IOU → XRP
        # taker가 IOU를 주면 MM이 XRP를 줌 → PathPayment IOU→XRP, 크로스환전 지원
        xrp_offer_amt = IOU_TO_XRP_OFFER_XRP[currency]
        iou_pays = str((Decimal(xrp_offer_amt) * rate * REVERSE_OFFER_SPREAD).quantize(Decimal("0.000001")))

        offer_b = OfferCreate(
            account=mm.address,
            taker_gets=xrp_to_drops(Decimal(xrp_offer_amt)),
            taker_pays=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value=iou_pays,
            ),
        )
        resp_b = submit_and_wait(offer_b, client, mm)
        res_b = resp_b.result.get("meta", {}).get("TransactionResult", "?")
        print(f"  {currency}→XRP: {res_b}  ({xrp_offer_amt} XRP ↔ {iou_pays} {currency})")

    print("\n=== 셋업 완료 ===")
    print("\n아래 값을 backend/.env에 저장하세요:\n")
    print(f"XRPL_ISSUER_ADDRESS={issuer.address}")
    print(f"XRPL_ISSUER_SEED={issuer.seed}")


if __name__ == "__main__":
    main()
