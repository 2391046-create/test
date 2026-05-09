"""Gemini 1.5 Flash를 사용한 영수증/메뉴판 분석"""
import asyncio
import base64
import json
import os
from typing import Dict, Any, Optional

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

EXCHANGE_RATES = {
    "USD": 1300,
    "JPY": 9.5,
    "GBP": 1650,
    "EUR": 1400,
    "CNY": 180,
    "THB": 37,
    "SGD": 970,
    "AUD": 850,
    "CAD": 950,
    "HKD": 166,
}

AVERAGE_PRICES = {
    "USD": {
        "coffee": 5.50,
        "burger": 12.00,
        "pizza": 15.00,
        "sushi": 18.00,
        "salad": 10.00,
        "pasta": 14.00,
        "steak": 25.00,
        "sandwich": 8.00,
        "ramen": 10.00,
        "chicken": 12.00,
    },
    "JPY": {
        "coffee": 500,
        "burger": 1200,
        "pizza": 1500,
        "sushi": 2000,
        "salad": 1000,
        "pasta": 1400,
        "steak": 3000,
        "sandwich": 800,
        "ramen": 900,
        "chicken": 1200,
    },
    "GBP": {
        "coffee": 4.50,
        "burger": 10.00,
        "pizza": 12.00,
        "sushi": 15.00,
        "salad": 8.50,
        "pasta": 11.00,
        "steak": 20.00,
        "sandwich": 6.50,
        "ramen": 8.00,
        "chicken": 10.00,
    },
}


def get_exchange_rate(currency: str) -> float:
    """통화별 환율 조회 (KRW 기준)"""
    return EXCHANGE_RATES.get(currency, 1300)


def get_average_price(currency: str, item_name: str) -> Optional[float]:
    """메뉴별 평균가 조회"""
    if currency not in AVERAGE_PRICES:
        return None
    item_key = item_name.lower().strip()
    for key, price in AVERAGE_PRICES[currency].items():
        if key in item_key:
            return price
    return None


async def analyze_receipt(image_data: bytes, target_country: str) -> Dict[str, Any]:
    """
    영수증 이미지 분석 (Gemini 1.5 Flash)
    
    Returns:
        {
            "merchant_name": str,
            "items": [{"name": str, "quantity": int, "price": float}],
            "total_local": float,
            "currency": str,
            "exchange_rate": float,
            "total_krw": int,
            "dutch_pay": {
                "num_people": int,
                "per_person_local": float,
                "per_person_krw": int
            }
        }
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return {"error": "GEMINI_API_KEY not configured"}

        # 이미지를 base64로 인코딩
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
당신은 영수증 분석 전문가입니다. 제공된 영수증 이미지를 분석하고 다음 정보를 추출하여 JSON 형식으로 반환하세요:

1. 상호명 (merchant_name)
2. 구매 항목 목록 (items): 각 항목의 이름, 수량, 가격
3. 총 금액 (total_local)
4. 통화 (currency): 자동 감지
5. 날짜 (date)
6. 시간 (time)

추가 계산:
- 환율: 1 {target_country} = ₩{get_exchange_rate(target_country)}
- 원화 환산 금액 (total_krw)
- 더치페이 정산 (2명 기준):
  - 1인당 현지통화 (per_person_local)
  - 1인당 원화 (per_person_krw)

응답은 반드시 다음 JSON 형식이어야 합니다:
{{
    "merchant_name": "상호명",
    "items": [
        {{"name": "항목명", "quantity": 1, "price": 10.50}}
    ],
    "total_local": 21.00,
    "currency": "USD",
    "exchange_rate": {get_exchange_rate(target_country)},
    "total_krw": 27300,
    "date": "2026-05-07",
    "time": "14:30",
    "dutch_pay": {{
        "num_people": 2,
        "per_person_local": 10.50,
        "per_person_krw": 13650
    }}
}}

JSON만 반환하세요. 다른 텍스트는 포함하지 마세요.
"""

        response = await asyncio.to_thread(
            model.generate_content,
            [{"mime_type": "image/jpeg", "data": image_b64}, prompt],
        )

        response_text = response.text.strip()

        # JSON 추출
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # 데이터 검증 및 정규화
        if "total_local" not in result:
            result["total_local"] = 0
        if "items" not in result:
            result["items"] = []

        result["total_local"] = float(result.get("total_local", 0))
        result["exchange_rate"] = get_exchange_rate(result.get("currency", target_country))
        result["total_krw"] = int(result["total_local"] * result["exchange_rate"])
        result["currency"] = result.get("currency", target_country)

        # 더치페이 계산
        num_people = result.get("dutch_pay", {}).get("num_people", 2)
        per_person_local = result["total_local"] / num_people
        per_person_krw = result["total_krw"] // num_people

        result["dutch_pay"] = {
            "num_people": num_people,
            "per_person_local": round(per_person_local, 2),
            "per_person_krw": per_person_krw,
        }

        return result

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Receipt analysis failed: {str(e)}"}


async def analyze_price_before_purchase(
    data: Any, target_country: str, is_image: bool = False
) -> Dict[str, Any]:
    """
    메뉴판/가격표 분석 (Gemini 1.5 Flash)
    
    Args:
        data: 이미지 바이트 또는 텍스트 문자열
        target_country: 국가 코드 (USD, JPY, GBP 등)
        is_image: True면 이미지, False면 텍스트
    
    Returns:
        {
            "restaurant_name": str,
            "items": [{"name": str, "price_local": float, "price_krw": int, "comparison": str}],
            "currency": str,
            "exchange_rate": float
        }
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return {"error": "GEMINI_API_KEY not configured"}

        model = genai.GenerativeModel("gemini-1.5-flash")

        if is_image:
            image_b64 = base64.standard_b64encode(data).decode("utf-8")
            prompt = f"""
당신은 메뉴판/가격표 분석 전문가입니다. 제공된 이미지에서 다음 정보를 추출하세요:

1. 레스토랑/가게 이름 (restaurant_name)
2. 메뉴 항목 목록: 각 항목의 이름과 가격
3. 통화 (currency): 자동 감지

각 메뉴에 대해 평균가와 비교하여 "현재 설정된 [국가]의 [메뉴] 평균가는 약 [얼마]입니다. 이 메뉴는 평균 대비 약 [얼마] 높게/낮게 책정되어 있습니다"라는 멘트를 생성하세요.

환율: 1 {target_country} = ₩{get_exchange_rate(target_country)}

응답은 반드시 다음 JSON 형식이어야 합니다:
{{
    "restaurant_name": "가게명",
    "items": [
        {{
            "name": "메뉴명",
            "price_local": 12.50,
            "price_krw": 16250,
            "comparison": "현재 설정된 USD의 burger 평균가는 약 12.00입니다. 이 메뉴는 평균 대비 약 4% 높게 책정되어 있습니다"
        }}
    ],
    "currency": "USD",
    "exchange_rate": {get_exchange_rate(target_country)}
}}

JSON만 반환하세요.
"""
            response = await asyncio.to_thread(
                model.generate_content,
                [{"mime_type": "image/jpeg", "data": image_b64}, prompt],
            )
        else:
            prompt = f"""
당신은 메뉴판/가격표 분석 전문가입니다. 제공된 텍스트에서 메뉴와 가격을 추출하세요:

입력 텍스트:
{data}

다음 정보를 추출하세요:
1. 레스토랑/가게 이름 (restaurant_name)
2. 메뉴 항목 목록: 각 항목의 이름과 가격
3. 통화 (currency): 자동 감지

각 메뉴에 대해 평균가와 비교하여 "현재 설정된 [국가]의 [메뉴] 평균가는 약 [얼마]입니다. 이 메뉴는 평균 대비 약 [얼마] 높게/낮게 책정되어 있습니다"라는 멘트를 생성하세요.

환율: 1 {target_country} = ₩{get_exchange_rate(target_country)}

응답은 반드시 다음 JSON 형식이어야 합니다:
{{
    "restaurant_name": "가게명",
    "items": [
        {{
            "name": "메뉴명",
            "price_local": 12.50,
            "price_krw": 16250,
            "comparison": "현재 설정된 USD의 burger 평균가는 약 12.00입니다. 이 메뉴는 평균 대비 약 4% 높게 책정되어 있습니다"
        }}
    ],
    "currency": "USD",
    "exchange_rate": {get_exchange_rate(target_country)}
}}

JSON만 반환하세요.
"""
            response = await asyncio.to_thread(model.generate_content, prompt)

        response_text = response.text.strip()

        # JSON 추출
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # 데이터 정규화
        if "items" not in result:
            result["items"] = []

        result["exchange_rate"] = get_exchange_rate(result.get("currency", target_country))
        result["currency"] = result.get("currency", target_country)

        # 각 항목의 원화 환산 계산
        for item in result["items"]:
            if "price_local" in item:
                item["price_krw"] = int(item["price_local"] * result["exchange_rate"])

        return result

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Price analysis failed: {str(e)}"}
