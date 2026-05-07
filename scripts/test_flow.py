"""
LivingFund API 전체 플로우 테스트
실행: python scripts/test_flow.py

전제조건:
  - docker-compose up -d (PostgreSQL)
  - uvicorn app.main:app --reload (backend)
  - python scripts/add_liquidity.py (DEX 유동성)
"""
import os
import sys
import time
import json
from pathlib import Path

import requests

# ── 설정 ─────────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"

env_path = Path(__file__).parent.parent / "backend" / ".env"
env = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()

ISSUER_SEED = env.get("XRPL_ISSUER_SEED", "")

# ── 출력 헬퍼 ─────────────────────────────────────────────────────────────────

def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def ok(msg: str):
    print(f"  [OK] {msg}")

def fail(msg: str, detail: str = ""):
    print(f"  [FAIL] {msg}")
    if detail:
        print(f"         {detail}")

def info(msg: str):
    print(f"  [..] {msg}")

def pretty(data: dict):
    print(json.dumps(data, indent=4, ensure_ascii=False, default=str))

# ── API 호출 헬퍼 ─────────────────────────────────────────────────────────────

def post(path: str, body: dict) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}{path}", json=body, timeout=60)
        if r.ok:
            return r.json()
        fail(f"POST {path} → {r.status_code}", r.json().get("detail", r.text))
        return None
    except requests.exceptions.ConnectionError:
        fail(f"POST {path}", "서버에 연결할 수 없습니다. uvicorn 실행 여부를 확인하세요.")
        sys.exit(1)

def get(path: str) -> dict | None:
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=60)
        if r.ok:
            return r.json()
        fail(f"GET {path} → {r.status_code}", r.json().get("detail", r.text))
        return None
    except requests.exceptions.ConnectionError:
        fail(f"GET {path}", "서버에 연결할 수 없습니다.")
        sys.exit(1)

# ── 테스트 스텝 ───────────────────────────────────────────────────────────────

def step_health():
    section("0. 서버 헬스 체크")
    r = get("/health")
    if r and r.get("status") == "ok":
        ok("서버 정상 응답")
        return True
    fail("헬스 체크 실패")
    return False

def step_create_user() -> dict | None:
    section("1. 학생 유저 생성")
    ts = int(time.time())
    body = {"name": f"테스트학생_{ts}", "email": f"student_{ts}@test.com", "phone": "010-0000-0000"}
    info(f"email: {body['email']}")
    data = post("/api/users/", body)
    if data:
        ok(f"유저 생성 완료  id={data['id']}")
        pretty(data)
    return data

def step_create_wallet(user_id: str) -> dict | None:
    section("2. XRPL 지갑 생성 (faucet + TrustLine)")
    info("faucet 요청 중... 15~30초 소요")
    t0 = time.time()
    data = post("/api/wallets/", {"user_id": user_id, "currencies": ["USD", "EUR", "KRW"]})
    if data:
        ok(f"지갑 생성 완료  ({time.time()-t0:.1f}s)")
        ok(f"address : {data['xrpl_address']}")
        ok(f"wallet_id: {data['id']}")
        ok(f"잔액:")
        for b in data.get("balances", []):
            print(f"           {b['currency']}: {b['amount']}")
    return data

def step_charge(wallet_id: str, wallet_address: str) -> dict | None:
    section("3. 생활비 충전 (이슈어 → 학생, 10 XRP)")
    if not ISSUER_SEED:
        fail("XRPL_ISSUER_SEED가 .env에 없습니다.")
        return None
    body = {
        "recipient_wallet_id": wallet_id,
        "sender_seed": ISSUER_SEED,
        "amount": "10",
        "currency": "XRP",
    }
    info("Payment 트랜잭션 제출 중...")
    data = post("/api/transactions/charge", body)
    if data:
        ok(f"충전 완료  tx_hash={data['xrpl_tx_hash'][:16]}...")
        ok(f"status   : {data['status']}")
        ok(f"amount   : {data['amount']} {data['currency']}")
    return data

def step_exchange(wallet_id: str) -> dict | None:
    section("4. 환전 (XRP → USD, from_max=1 XRP)")
    body = {
        "wallet_id": wallet_id,
        "from_currency": "XRP",
        "to_currency": "USD",
        "from_max": "1",
        "to_amount": None,
        "slippage_pct": 1,
    }
    info("OfferCreate 제출 중...")
    data = post("/api/transactions/exchange", body)
    if data:
        ok(f"환전 완료")
        ok(f"tx_hash        : {data['transaction']['xrpl_tx_hash'][:16]}...")
        ok(f"exchanged_amount: {data['exchanged_amount']} USD")
        ok(f"rate           : {data.get('rate')} USD/XRP")
    return data

def step_balances(wallet_id: str):
    section("5. 최신 잔액 조회 (XRPL 동기화)")
    data = get(f"/api/wallets/{wallet_id}")
    if data:
        ok("잔액 조회 완료")
        for b in data.get("balances", []):
            issuer = f"  (issuer: {b['issuer'][:8]}...)" if b.get("issuer") else ""
            print(f"    {b['currency']:>4}: {b['amount']}{issuer}")
    return data

def step_transactions(wallet_id: str):
    section("6. 트랜잭션 내역 조회")
    data = get(f"/api/transactions/wallet/{wallet_id}")
    if data is not None:
        ok(f"총 {len(data)}건")
        for tx in data:
            print(f"    [{tx['tx_type']:>11}] {tx['currency']} {tx['amount']}  status={tx['status']}  {tx['xrpl_tx_hash'][:12]}...")
    return data

# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    print("\nLivingFund API 전체 플로우 테스트")
    print(f"BASE_URL: {BASE_URL}")

    if not step_health():
        sys.exit(1)

    user = step_create_user()
    if not user:
        sys.exit(1)

    wallet = step_create_wallet(user["id"])
    if not wallet:
        sys.exit(1)

    wallet_id = wallet["id"]
    wallet_address = wallet["xrpl_address"]

    charge = step_charge(wallet_id, wallet_address)
    if not charge:
        print("\n  충전 실패 — 환전 테스트를 건너뜁니다.")
    else:
        time.sleep(2)  # 원장 반영 대기
        step_exchange(wallet_id)

    step_balances(wallet_id)
    step_transactions(wallet_id)

    section("테스트 완료")
    print(f"  wallet_id  : {wallet_id}")
    print(f"  xrpl_address: {wallet_address}")
    print()


if __name__ == "__main__":
    main()
