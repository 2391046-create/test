"""
Gemini AI 서비스 - 영수증/메뉴판/은행알림 분석
"""
import asyncio
import base64
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

import google.generativeai as genai
from app.config import settings

# Gemini 초기화
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel("gemini-1.5-flash")
else:
    _model = None
    print("⚠️ GEMINI_API_KEY 없음 - AI 기능 비활성화")

# 카테고리 키워드 매핑
CATEGORY_KEYWORDS = {
    "food": ["restaurant", "cafe", "coffee", "pizza", "burger", "sushi", "ramen", "food",
             "meal", "lunch", "dinner", "breakfast", "bakery", "bar", "pub", "starbucks",
             "mcdonalds", "kfc", "subway", "식당", "카페", "음식", "식사"],
    "transport": ["taxi", "uber", "lyft", "bus", "train", "metro", "subway", "parking",
                  "gas", "fuel", "airline", "flight", "grab", "transport", "교통", "택시"],
    "shopping": ["mall", "store", "shop", "market", "supermarket", "amazon", "ebay",
                 "walmart", "target", "shopping", "마트", "쇼핑"],
    "entertainment": ["movie", "cinema", "theater", "concert", "game", "netflix", "spotify",
                      "entertainment", "museum", "park", "sports", "영화"],
    "utilities": ["electricity", "water", "internet", "phone", "utility", "bill", "통신", "공과금"],
    "health": ["hospital", "clinic", "pharmacy", "doctor", "medical", "dental", "약국", "병원"],
    "education": ["school", "university", "book", "education", "course", "tuition", "학원"],
    "accommodation": ["hotel", "hostel", "airbnb", "resort", "motel", "호텔", "숙박"],
}

# 현지 평균 물가 데이터 (메뉴 비교용)
AVERAGE_PRICES = {
    "USD": {
        "coffee": 5.50, "latte": 6.00, "americano": 4.50, "burger": 12.00,
        "pizza": 15.00, "sushi": 18.00, "salad": 10.00, "pasta": 14.00,
        "steak": 28.00, "sandwich": 9.00, "ramen": 12.00, "chicken": 13.00,
        "beer": 7.00, "cocktail": 12.00, "breakfast": 12.00,
    },
    "JPY": {
        "coffee": 550, "latte": 650, "americano": 480, "burger": 1200,
        "pizza": 1600, "sushi": 2200, "salad": 1000, "pasta": 1400,
        "steak": 3500, "sandwich": 850, "ramen": 950, "chicken": 1300,
        "beer": 650, "cocktail": 1200, "breakfast": 1000,
    },
    "GBP": {
        "coffee": 4.50, "latte": 5.20, "americano": 3.80, "burger": 10.00,
        "pizza": 12.00, "sushi": 16.00, "salad": 8.50, "pasta": 12.00,
        "steak": 22.00, "sandwich": 7.00, "ramen": 9.00, "chicken": 11.00,
        "beer": 5.50, "cocktail": 10.00, "breakfast": 10.00,
    },
    "EUR": {
        "coffee": 3.50, "latte": 4.50, "americano": 3.00, "burger": 10.00,
        "pizza": 12.00, "sushi": 15.00, "salad": 8.00, "pasta": 11.00,
        "steak": 20.00, "sandwich": 7.00, "ramen": 10.00, "chicken": 10.00,
        "beer": 5.00, "cocktail": 9.00, "breakfast": 9.00,
    },
    "CNY": {
        "coffee": 35, "latte": 42, "americano": 28, "burger": 45,
        "pizza": 60, "sushi": 80, "salad": 35, "pasta": 55,
        "steak": 120, "sandwich": 30, "ramen": 38, "chicken": 45,
        "beer": 20, "cocktail": 50, "breakfast": 25,
    },
    "THB": {
        "coffee": 120, "latte": 150, "americano": 90, "burger": 200,
        "pizza": 280, "sushi": 350, "salad": 180, "pasta": 250,
        "steak": 500, "sandwich": 150, "ramen": 180, "chicken": 200,
        "beer": 80, "cocktail": 200, "breakfast": 150,
    },
    "SGD": {
        "coffee": 6.00, "latte": 7.00, "americano": 5.00, "burger": 12.00,
        "pizza": 16.00, "sushi": 20.00, "salad": 10.00, "pasta": 14.00,
        "steak": 28.00, "sandwich": 9.00, "ramen": 12.00, "chicken": 12.00,
        "beer": 8.00, "cocktail": 15.00, "breakfast": 11.00,
    },
    "AUD": {
        "coffee": 5.00, "latte": 6.00, "americano": 4.50, "burger": 14.00,
        "pizza": 16.00, "sushi": 20.00, "salad": 12.00, "pasta": 16.00,
        "steak": 30.00, "sandwich": 10.00, "ramen": 14.00, "chicken": 15.00,
        "beer": 8.00, "cocktail": 15.00, "breakfast": 14.00,
    },
}


def _extract_json(text: str) -> Optional[Dict]:
    """응답 텍스트에서 JSON 추출"""
    # 코드 블록 제거
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # JSON 객체 찾기
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return None


def _classify_category(merchant_name: str, items: List[Dict]) -> tuple:
    """카테고리 자동 분류"""
    text = (merchant_name + " " + " ".join([item.get("name", "") for item in items])).lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    if not scores:
        return "other", 50.0

    best = max(scores, key=scores.get)
    confidence = min(100.0, scores[best] * 25.0)
    return best, confidence


async def analyze_receipt_image(image_base64: str, currency: str = "USD") -> Dict[str, Any]:
    """
    영수증 이미지 분석 (실제 Gemini AI 호출)
    """
    if not _model:
        return {"success": False, "error": "GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."}

    try:
        prompt = f"""You are a receipt analysis expert.
Analyze this receipt image and return ONLY a JSON object (no other text):

{{
    "merchant_name": "store name",
    "items": [
        {{"name": "item name", "quantity": 1, "price": 0.00}}
    ],
    "total": 0.00,
    "currency": "{currency}",
    "date": "YYYY-MM-DD",
    "description": "brief description"
}}

Rules:
- Detect the actual currency from the receipt (look for symbols: $, £, €, ¥, ₩, etc.)
- Extract ALL line items
- Use null for missing data
- Return ONLY valid JSON"""

        # 이미지 데이터 준비 (base64 → bytes)
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            image_bytes = image_base64.encode() if isinstance(image_base64, str) else image_base64

        response = await asyncio.to_thread(
            lambda: _model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
        )

        data = _extract_json(response.text)
        if not data:
            return {"success": False, "error": "영수증 파싱 실패 - 이미지를 다시 시도해주세요"}

        merchant = data.get("merchant_name", "Unknown")
        items = data.get("items", [])
        total = float(data.get("total", 0) or 0)
        detected_currency = (data.get("currency") or currency).upper()

        category, confidence = _classify_category(merchant, items)

        return {
            "success": True,
            "merchant_name": merchant,
            "items": items,
            "total_local": total,
            "currency": detected_currency,
            "category": category,
            "category_confidence": confidence,
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "description": data.get("description", ""),
        }

    except Exception as e:
        return {"success": False, "error": f"분석 오류: {str(e)}"}


async def analyze_bank_notification(notification_text: str, currency: str = "USD") -> Dict[str, Any]:
    """
    은행 알림 텍스트 분석 (실제 Gemini AI 호출)
    """
    if not _model:
        return {"success": False, "error": "GEMINI_API_KEY가 설정되지 않았습니다."}

    try:
        prompt = f"""Extract transaction information from this bank notification:
"{notification_text}"

Return ONLY a JSON object:
{{
    "merchant_name": "store or service name",
    "amount": 0.00,
    "currency": "currency code (USD/KRW/JPY etc)",
    "date": "YYYY-MM-DD",
    "description": "what was purchased"
}}

- Detect currency from symbols (₩=KRW, $=USD, £=GBP, €=EUR, ¥=JPY)
- Return ONLY valid JSON"""

        response = await asyncio.to_thread(
            lambda: _model.generate_content(prompt)
        )

        data = _extract_json(response.text)
        if not data:
            return {"success": False, "error": "알림 파싱 실패"}

        merchant = data.get("merchant_name", "Unknown")
        amount = float(data.get("amount", 0) or 0)
        detected_currency = (data.get("currency") or currency).upper()
        category, confidence = _classify_category(merchant, [])

        return {
            "success": True,
            "merchant_name": merchant,
            "amount_local": amount,
            "currency": detected_currency,
            "category": category,
            "category_confidence": confidence,
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "description": data.get("description", ""),
            "source": "bank_notification",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def analyze_menu_image(
    image_base64: Optional[str] = None,
    text: Optional[str] = None,
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    메뉴판 이미지/텍스트 분석 + 현지 평균 물가 비교
    """
    if not _model:
        return {"success": False, "error": "GEMINI_API_KEY가 설정되지 않았습니다."}

    try:
        prompt = """Extract ALL menu items and their prices from this menu.
Return ONLY a JSON object:
{
    "items": [
        {"name": "item name", "price": 0.00}
    ],
    "currency": "detected currency code"
}
Return ONLY valid JSON."""

        if image_base64:
            try:
                image_bytes = base64.b64decode(image_base64)
            except Exception:
                image_bytes = image_base64.encode() if isinstance(image_base64, str) else image_base64

            response = await asyncio.to_thread(
                lambda: _model.generate_content([
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_bytes}
                ])
            )
        else:
            response = await asyncio.to_thread(
                lambda: _model.generate_content(f"{prompt}\n\nMenu text:\n{text}")
            )

        data = _extract_json(response.text)
        if not data:
            return {"success": False, "error": "메뉴판 파싱 실패"}

        detected_currency = (data.get("currency") or currency).upper()
        avg_prices = AVERAGE_PRICES.get(detected_currency, AVERAGE_PRICES.get("USD", {}))

        analyzed_items = []
        for item in data.get("items", []):
            name = item.get("name", "")
            price = float(item.get("price", 0) or 0)
            name_lower = name.lower()

            # 평균가 찾기 (키워드 매칭)
            avg_price = None
            matched_keyword = None
            for kw, avg in avg_prices.items():
                if kw in name_lower:
                    avg_price = avg
                    matched_keyword = kw
                    break

            if avg_price and avg_price > 0:
                diff_pct = ((price - avg_price) / avg_price) * 100
                if diff_pct < -10:
                    comparison = "저렴"
                    emoji = "🟢"
                elif diff_pct > 10:
                    comparison = "비쌈"
                    emoji = "🔴"
                else:
                    comparison = "평균"
                    emoji = "🟡"

                message = (
                    f"{detected_currency} 기준 {name}의 현지 평균 단가는 "
                    f"{avg_price:.2f} {detected_currency}입니다. "
                    f"이 메뉴는 평균 대비 {abs(diff_pct):.1f}% "
                    f"{'비쌉니다' if diff_pct > 0 else '저렴합니다'}. {emoji}"
                )
            else:
                diff_pct = 0
                comparison = "정보없음"
                message = f"{name}의 현지 평균가 데이터가 없습니다."

            analyzed_items.append({
                "name": name,
                "price": price,
                "currency": detected_currency,
                "average_price": avg_price,
                "percentage_diff": round(diff_pct, 1),
                "price_comparison": comparison,
                "message": message,
            })

        return {
            "success": True,
            "currency": detected_currency,
            "items": analyzed_items,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
