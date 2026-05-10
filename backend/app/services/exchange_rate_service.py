"""
실시간 환율 조회 서비스
"""
import asyncio
import aiohttp
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

# 환율 캐시
_exchange_rate_cache: Dict[str, tuple[Dict[str, float], datetime]] = {}
CACHE_DURATION = timedelta(minutes=30)  # 30분 캐시


async def get_exchange_rates(base_currency: str = "USD") -> Dict[str, float]:
    """
    실시간 환율 조회 (캐시 활용)
    
    Args:
        base_currency: 기준 통화
    
    Returns:
        {"USD": 1.0, "JPY": 110.5, "KRW": 1200, ...}
    """
    # 캐시 확인
    if base_currency in _exchange_rate_cache:
        rates, cached_time = _exchange_rate_cache[base_currency]
        if datetime.now() - cached_time < CACHE_DURATION:
            return rates
    
    try:
        # API 호출 (여러 소스 시도)
        rates = await _fetch_from_exchangerate_api(base_currency)
        
        if not rates:
            rates = await _fetch_from_fixer_api(base_currency)
        
        if not rates:
            rates = _get_fallback_rates(base_currency)
        
        # 캐시 저장
        _exchange_rate_cache[base_currency] = (rates, datetime.now())
        
        return rates
        
    except Exception as e:
        print(f"환율 조회 오류: {e}")
        return _get_fallback_rates(base_currency)


async def _fetch_from_exchangerate_api(base_currency: str) -> Optional[Dict[str, float]]:
    """exchangerate-api.com에서 환율 조회"""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("rates", {})
    except Exception as e:
        print(f"exchangerate-api 오류: {e}")
    
    return None


async def _fetch_from_fixer_api(base_currency: str) -> Optional[Dict[str, float]]:
    """fixer.io에서 환율 조회 (무료 버전)"""
    try:
        url = f"https://api.fixer.io/latest?base={base_currency}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("rates", {})
    except Exception as e:
        print(f"fixer.io 오류: {e}")
    
    return None


def _get_fallback_rates(base_currency: str) -> Dict[str, float]:
    """
    기본 환율 (API 실패 시 사용)
    """
    fallback_rates = {
        "USD": {
            "USD": 1.0,
            "JPY": 110.5,
            "GBP": 0.73,
            "EUR": 0.85,
            "CNY": 6.45,
            "THB": 33.5,
            "SGD": 1.35,
            "AUD": 1.35,
            "CAD": 1.25,
            "HKD": 7.78,
            "KRW": 1200,
        },
        "KRW": {
            "USD": 1 / 1200,
            "JPY": 110.5 / 1200,
            "GBP": 0.73 / 1200,
            "EUR": 0.85 / 1200,
            "CNY": 6.45 / 1200,
            "THB": 33.5 / 1200,
            "SGD": 1.35 / 1200,
            "AUD": 1.35 / 1200,
            "CAD": 1.25 / 1200,
            "HKD": 7.78 / 1200,
            "KRW": 1.0,
        },
        "JPY": {
            "USD": 1 / 110.5,
            "JPY": 1.0,
            "GBP": 0.73 / 110.5,
            "EUR": 0.85 / 110.5,
            "CNY": 6.45 / 110.5,
            "THB": 33.5 / 110.5,
            "SGD": 1.35 / 110.5,
            "AUD": 1.35 / 110.5,
            "CAD": 1.25 / 110.5,
            "HKD": 7.78 / 110.5,
            "KRW": 1200 / 110.5,
        },
    }
    
    return fallback_rates.get(base_currency, fallback_rates["USD"])


async def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """
    통화 변환
    
    Args:
        amount: 금액
        from_currency: 원본 통화
        to_currency: 대상 통화
    
    Returns:
        변환된 금액
    """
    if from_currency == to_currency:
        return amount
    
    rates = await get_exchange_rates(from_currency)
    
    if to_currency not in rates:
        # 기본값 사용
        rates = _get_fallback_rates(from_currency)
    
    rate = Decimal(str(rates.get(to_currency, 1.0)))
    return amount * rate


def clear_cache():
    """환율 캐시 초기화"""
    global _exchange_rate_cache
    _exchange_rate_cache.clear()
