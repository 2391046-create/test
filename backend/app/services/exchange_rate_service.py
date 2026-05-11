"""
실시간 환율 서비스 - 무료 API 여러 개를 순서대로 시도
"""
import asyncio
import aiohttp
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

# 캐시 (30분)
_cache: Dict[str, tuple] = {}
CACHE_DURATION = timedelta(minutes=30)

# 기본 환율 (API 모두 실패 시 사용)
FALLBACK_TO_KRW = {
    "USD": 1350.0,
    "JPY": 9.2,
    "GBP": 1710.0,
    "EUR": 1460.0,
    "CNY": 186.0,
    "THB": 38.0,
    "SGD": 1005.0,
    "AUD": 878.0,
    "CAD": 990.0,
    "HKD": 173.0,
    "KRW": 1.0,
}


async def get_rate_to_krw(currency: str) -> float:
    """특정 통화 → KRW 환율 반환"""
    currency = currency.upper()
    if currency == "KRW":
        return 1.0

    rates = await get_all_rates_to_krw()
    return rates.get(currency, FALLBACK_TO_KRW.get(currency, 1350.0))


async def get_all_rates_to_krw() -> Dict[str, float]:
    """모든 통화 → KRW 환율 반환 (캐시 활용)"""
    cache_key = "all_to_krw"

    if cache_key in _cache:
        rates, cached_at = _cache[cache_key]
        if datetime.now() - cached_at < CACHE_DURATION:
            return rates

    rates = await _fetch_rates()
    _cache[cache_key] = (rates, datetime.now())
    return rates


async def _fetch_rates() -> Dict[str, float]:
    """무료 환율 API 순서대로 시도"""
    # 1순위: exchangerate-api.com (완전 무료, 키 불필요)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.exchangerate-api.com/v4/latest/KRW",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw = data.get("rates", {})
                    # KRW 기준이므로, 1/rate = 해당 통화 → KRW
                    result = {}
                    for cur, rate in raw.items():
                        if rate > 0:
                            result[cur] = 1.0 / rate
                    result["KRW"] = 1.0
                    print(f"✅ 환율 업데이트 성공 (exchangerate-api.com): USD={result.get('USD', 'N/A')}")
                    return result
    except Exception as e:
        print(f"exchangerate-api 실패: {e}")

    # 2순위: open.er-api.com (완전 무료)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://open.er-api.com/v6/latest/KRW",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw = data.get("rates", {})
                    result = {}
                    for cur, rate in raw.items():
                        if rate > 0:
                            result[cur] = 1.0 / rate
                    result["KRW"] = 1.0
                    print(f"✅ 환율 업데이트 성공 (open.er-api.com)")
                    return result
    except Exception as e:
        print(f"open.er-api 실패: {e}")

    print("⚠️ 모든 환율 API 실패 - 기본값 사용")
    return FALLBACK_TO_KRW.copy()


async def convert_to_krw(amount: float, currency: str) -> float:
    """금액을 KRW로 변환"""
    rate = await get_rate_to_krw(currency)
    return round(amount * rate, 2)


def get_fallback_rate(currency: str) -> float:
    """즉시(동기) fallback 환율 반환"""
    return FALLBACK_TO_KRW.get(currency.upper(), 1350.0)
