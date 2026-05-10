"""
Gemini AI 기반 영수증 및 메뉴판 분석 서비스
"""
import asyncio
import base64
import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

import google.generativeai as genai
from app.config import settings

# Gemini 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# 환율 데이터 (실시간 업데이트는 별도 서비스에서 처리)
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
    "KRW": 1,
}

# 카테고리 매핑
CATEGORY_KEYWORDS = {
    "food": ["restaurant", "cafe", "coffee", "pizza", "burger", "sushi", "ramen", "food", "meal", "lunch", "dinner", "breakfast", "bakery", "bar", "pub"],
    "transport": ["taxi", "uber", "bus", "train", "metro", "parking", "gas", "fuel", "car", "transport", "airline", "flight"],
    "shopping": ["mall", "store", "shop", "market", "supermarket", "clothes", "fashion", "amazon", "ebay", "shopping"],
    "entertainment": ["movie", "cinema", "theater", "concert", "game", "entertainment", "museum", "park", "sports"],
    "utilities": ["electricity", "water", "gas", "internet", "phone", "utility", "bill"],
    "health": ["hospital", "clinic", "pharmacy", "doctor", "medical", "health", "dental", "medicine"],
    "education": ["school", "university", "book", "education", "course", "training", "tuition"],
    "accommodation": ["hotel", "hostel", "airbnb", "accommodation", "resort", "motel"],
}

# 평균 가격 데이터
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


async def analyze_receipt_image(image_base64: str, currency: str = "USD") -> Dict[str, Any]:
    """
    영수증 이미지를 분석하여 거래 정보 추출
    
    Args:
        image_base64: Base64 인코딩된 이미지
        currency: 통화 코드
    
    Returns:
        {
            "success": bool,
            "merchant_name": str,
            "items": [{"name": str, "quantity": int, "price": float}],
            "total_local": float,
            "currency": str,
            "exchange_rate": float,
            "total_krw": float,
            "category": str,
            "category_confidence": float,
            "date": str,
            "error": str (if success=False)
        }
    """
    try:
        # 이미지 데이터 준비
        image_data = {
            "mime_type": "image/jpeg",
            "data": image_base64,
        }
        
        # Gemini 프롬프트
        prompt = f"""
        Analyze this receipt image and extract the following information in JSON format:
        
        {{
            "merchant_name": "store/restaurant name",
            "items": [
                {{"name": "item name", "quantity": 1, "price": 0.00}},
                ...
            ],
            "total": 0.00,
            "currency": "{currency}",
            "date": "YYYY-MM-DD HH:MM:SS",
            "description": "brief description"
        }}
        
        If you cannot extract some information, use null or 0.
        Return ONLY valid JSON, no other text.
        """
        
        # Gemini 호출
        response = await asyncio.to_thread(
            lambda: model.generate_content([prompt, image_data])
        )
        
        # 응답 파싱
        response_text = response.text.strip()
        
        # JSON 추출
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return {
                "success": False,
                "error": "Failed to parse receipt"
            }
        
        receipt_data = json.loads(json_match.group())
        
        # 기본값 설정
        merchant_name = receipt_data.get("merchant_name", "Unknown")
        items = receipt_data.get("items", [])
        total_local = float(receipt_data.get("total", 0))
        currency_code = receipt_data.get("currency", currency).upper()
        
        # 환율 적용
        exchange_rate = EXCHANGE_RATES.get(currency_code, 1300)
        total_krw = Decimal(str(total_local * exchange_rate))
        
        # 카테고리 자동 분류
        category, confidence = _classify_category(merchant_name, items)
        
        # 날짜 파싱
        date_str = receipt_data.get("date", datetime.now().isoformat())
        
        return {
            "success": True,
            "merchant_name": merchant_name,
            "items": items,
            "total_local": total_local,
            "currency": currency_code,
            "exchange_rate": float(exchange_rate),
            "total_krw": float(total_krw),
            "category": category,
            "category_confidence": confidence,
            "date": date_str,
            "description": receipt_data.get("description", ""),
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_bank_notification(notification_text: str, currency: str = "USD") -> Dict[str, Any]:
    """
    은행 알림 텍스트를 분석하여 거래 정보 추출
    
    Args:
        notification_text: 은행 알림 텍스트
        currency: 통화 코드
    
    Returns:
        {
            "success": bool,
            "merchant_name": str,
            "amount": float,
            "currency": str,
            "category": str,
            "date": str,
            "error": str (if success=False)
        }
    """
    try:
        prompt = f"""
        Extract transaction information from this bank notification text:
        "{notification_text}"
        
        Return JSON format:
        {{
            "merchant_name": "store/service name",
            "amount": 0.00,
            "currency": "{currency}",
            "date": "YYYY-MM-DD HH:MM:SS",
            "description": "transaction description"
        }}
        
        Return ONLY valid JSON, no other text.
        """
        
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        
        response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if not json_match:
            return {
                "success": False,
                "error": "Failed to parse notification"
            }
        
        tx_data = json.loads(json_match.group())
        
        merchant_name = tx_data.get("merchant_name", "Unknown")
        amount = float(tx_data.get("amount", 0))
        currency_code = tx_data.get("currency", currency).upper()
        
        # 환율 적용
        exchange_rate = EXCHANGE_RATES.get(currency_code, 1300)
        amount_krw = Decimal(str(amount * exchange_rate))
        
        # 카테고리 분류
        category, confidence = _classify_category(merchant_name, [])
        
        return {
            "success": True,
            "merchant_name": merchant_name,
            "amount_local": amount,
            "currency": currency_code,
            "exchange_rate": float(exchange_rate),
            "amount_krw": float(amount_krw),
            "category": category,
            "category_confidence": confidence,
            "date": tx_data.get("date", datetime.now().isoformat()),
            "description": tx_data.get("description", ""),
            "source": "bank_notification",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_menu_price(image_base64: Optional[str] = None, text: Optional[str] = None, currency: str = "USD") -> Dict[str, Any]:
    """
    메뉴판 가격을 분석하여 평균가와 비교
    
    Args:
        image_base64: Base64 인코딩된 메뉴판 이미지
        text: 메뉴판 텍스트
        currency: 통화 코드
    
    Returns:
        {
            "success": bool,
            "items": [
                {
                    "name": str,
                    "price": float,
                    "currency": str,
                    "average_price": float,
                    "price_comparison": str,  # "저렴", "평균", "비쌈"
                    "percentage_diff": float,  # 평균 대비 차이 %
                }
            ],
            "error": str (if success=False)
        }
    """
    try:
        if image_base64:
            image_data = {
                "mime_type": "image/jpeg",
                "data": image_base64,
            }
            prompt = f"""
            Extract menu items and prices from this menu image:
            
            Return JSON format:
            {{
                "items": [
                    {{"name": "item name", "price": 0.00}},
                    ...
                ]
            }}
            
            Return ONLY valid JSON, no other text.
            """
            
            response = await asyncio.to_thread(
                lambda: model.generate_content([prompt, image_data])
            )
        else:
            prompt = f"""
            Extract menu items and prices from this menu text:
            "{text}"
            
            Return JSON format:
            {{
                "items": [
                    {{"name": "item name", "price": 0.00}},
                    ...
                ]
            }}
            
            Return ONLY valid JSON, no other text.
            """
            
            response = await asyncio.to_thread(
                lambda: model.generate_content(prompt)
            )
        
        response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if not json_match:
            return {
                "success": False,
                "error": "Failed to parse menu"
            }
        
        menu_data = json.loads(json_match.group())
        items = menu_data.get("items", [])
        currency_code = currency.upper()
        
        # 평균가 비교
        average_prices = AVERAGE_PRICES.get(currency_code, {})
        
        analyzed_items = []
        for item in items:
            item_name = item.get("name", "").lower()
            price = float(item.get("price", 0))
            
            # 평균가 찾기
            average_price = None
            for keyword, avg_price in average_prices.items():
                if keyword in item_name:
                    average_price = avg_price
                    break
            
            if average_price:
                percentage_diff = ((price - average_price) / average_price) * 100
                if percentage_diff < -10:
                    comparison = "저렴"
                elif percentage_diff > 10:
                    comparison = "비쌈"
                else:
                    comparison = "평균"
            else:
                percentage_diff = 0
                comparison = "평균"
            
            analyzed_items.append({
                "name": item.get("name"),
                "price": price,
                "currency": currency_code,
                "average_price": average_price or price,
                "price_comparison": comparison,
                "percentage_diff": round(percentage_diff, 2),
            })
        
        return {
            "success": True,
            "items": analyzed_items,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _classify_category(merchant_name: str, items: List[Dict]) -> tuple[str, float]:
    """
    상호명과 품목을 기반으로 카테고리 자동 분류
    
    Returns:
        (category, confidence_percentage)
    """
    text = (merchant_name + " " + " ".join([item.get("name", "") for item in items])).lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return "other", 50.0
    
    # 최고 점수 카테고리
    best_category = max(scores, key=scores.get)
    confidence = min(100, (scores[best_category] / len(CATEGORY_KEYWORDS[best_category])) * 100)
    
    return best_category, confidence
