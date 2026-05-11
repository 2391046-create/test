"""
환율 라우터 - 실시간 환율 조회
"""
from fastapi import APIRouter
from app.services.exchange_rate_service import get_all_rates_to_krw, get_rate_to_krw

router = APIRouter(prefix="/api/rates", tags=["exchange rates"])


@router.get("/")
async def get_rates():
    """
    모든 통화의 KRW 환율 실시간 조회
    (30분 캐시, API 실패 시 최근값 사용)
    """
    rates = await get_all_rates_to_krw()
    # KRW 기준으로 정리
    return {
        "success": True,
        "base": "KRW",
        "rates": rates,
        "note": "각 통화 1단위 = X KRW"
    }


@router.get("/{currency}")
async def get_rate(currency: str):
    """특정 통화 → KRW 환율"""
    rate = await get_rate_to_krw(currency.upper())
    return {
        "success": True,
        "currency": currency.upper(),
        "rate_to_krw": rate,
        "note": f"1 {currency.upper()} = {rate} KRW"
    }
