"""
기존 이슈어를 유지하면서 DEX 오더북 유동성만 추가하는 스크립트.
이미 setup_issuer.py로 이슈어를 만든 경우 이 스크립트만 실행하세요.

실행: python scripts/add_liquidity.py
"""
import os
import sys
from decimal import Decimal
from pathlib import Path

# backend/.env 로드
env_path = Path(__file__).parent.parent / "backend" / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

TESTNET_URL = os.environ.get("XRPL_TESTNET_URL", "https://s.altnet.rippletest.net:51234")
ISSUER_ADDRESS = os.environ.get("XRPL_ISSUER_ADDRESS", "")
ISSUER_SEED = os.environ.get("XRPL_ISSUER_SEED", "")

if not ISSUER_ADDRESS or not ISSUER_SEED:
    print("❌ .env에 XRPL_ISSUER_ADDRESS / XRPL_ISSUER_SEED가 없습니다.")
    sys.exit(1)

from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import OfferCreate, Payment, TrustSet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet, generate_faucet_wallet

# 1 XRP = ? 통화 (테스트 환율)
XRP_RATES = {
    "USD": Decimal("1.5"),
    "EUR": Decimal("1.3"),
    "KRW": Decimal("1800"),
}

# MM이 보유할 IOU 수량
IOU_SUPPLY = {"USD": "2000", "EUR": "2000", "KRW": "2000000"}

# XRP→IOU 오더에서 MM이 제공할 IOU 수량
XRP_TO_IOU_OFFER = {"USD": "1500", "EUR": "1500", "KRW": "1500000"}

# IOU→XRP 역방향 오더에서 MM이 줄 XRP 수량
IOU_TO_XRP_XRP_AMT = {"USD": "80", "EUR": "80", "KRW": "80"}

# IOU→XRP 오더의 스프레드: 동일 환율로 두 오더를 같은 계정에서 생성하면
# XRPL이 self-crossing offer로 인식해 먼저 생성된 오더를 자동 취소함.
# 5% 스프레드를 적용해 두 오더가 겹치지 않게 방지.
REVERSE_OFFER_SPREAD = Decimal("1.05")


def main():
    client = JsonRpcClient(TESTNET_URL)
    issuer = Wallet.from_seed(ISSUER_SEED)

    print("=== DEX 유동성 추가 시작 ===")
    print(f"이슈어 주소: {ISSUER_ADDRESS}\n")

    # ── 1) 마켓메이커(MM) 지갑 생성 ─────────────────────────────────────
    print("[1/3] 마켓메이커 지갑 생성 중... (faucet, 10~20초)")
    mm = generate_faucet_wallet(client, debug=False)
    print(f"  MM address: {mm.address}")

    # ── 2) MM TrustLine 설정 + IOU 수령 ─────────────────────────────────
    print("\n[2/3] TrustLine 설정 및 IOU 발행")
    for currency, supply in IOU_SUPPLY.items():
        trust = TrustSet(
            account=mm.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=ISSUER_ADDRESS,
                value="100000000",
            ),
        )
        submit_and_wait(trust, client, mm)

        payment = Payment(
            account=issuer.address,
            destination=mm.address,
            amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=ISSUER_ADDRESS,
                value=supply,
            ),
        )
        submit_and_wait(payment, client, issuer)
        print(f"  {currency}: {supply} 발행 완료")

    # ── 3) DEX 양방향 오더 생성 ─────────────────────────────────────────
    print("\n[3/3] DEX 오더 생성 (XRP ↔ USD/EUR/KRW 양방향)")
    for currency, rate in XRP_RATES.items():

        # 오더 A — XRP → IOU (taker가 XRP 주면 MM이 IOU 줌)
        iou_amt = XRP_TO_IOU_OFFER[currency]
        xrp_pays = Decimal(iou_amt) / rate

        resp_a = submit_and_wait(
            OfferCreate(
                account=mm.address,
                taker_gets=IssuedCurrencyAmount(
                    currency=currency, issuer=ISSUER_ADDRESS, value=iou_amt
                ),
                taker_pays=xrp_to_drops(xrp_pays),
            ),
            client,
            mm,
        )
        res_a = resp_a.result.get("meta", {}).get("TransactionResult", "?")
        print(f"  XRP→{currency}: {res_a}  (1 XRP = {rate} {currency})")

        # 오더 B — IOU → XRP (taker가 IOU 주면 MM이 XRP 줌, 크로스환전용)
        xrp_amt = IOU_TO_XRP_XRP_AMT[currency]
        iou_pays = str((Decimal(xrp_amt) * rate * REVERSE_OFFER_SPREAD).quantize(Decimal("0.000001")))

        resp_b = submit_and_wait(
            OfferCreate(
                account=mm.address,
                taker_gets=xrp_to_drops(Decimal(xrp_amt)),
                taker_pays=IssuedCurrencyAmount(
                    currency=currency, issuer=ISSUER_ADDRESS, value=iou_pays
                ),
            ),
            client,
            mm,
        )
        res_b = resp_b.result.get("meta", {}).get("TransactionResult", "?")
        print(f"  {currency}→XRP: {res_b}  ({xrp_amt} XRP ↔ {iou_pays} {currency})")

    print("\n=== 완료! 이제 F03 환전을 다시 테스트하세요 ===")


if __name__ == "__main__":
    main()
