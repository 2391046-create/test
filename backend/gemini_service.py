"""
Gemini AI를 사용한 영수증 및 메뉴판 분석 서비스
"""
import google.generativeai as genai
import base64
import json
import os
from typing import Optional, Dict, Any

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다")

genai.configure(api_key=GEMINI_API_KEY)

# 환율 데이터
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

# 평균 가격 데이터
AVERAGE_PRICES = {
    "USD": {
        "coffee": 5.50, "burger": 12.00, "pizza": 15.00, "sushi": 18.00,
        "salad": 10.00, "pasta": 14.00, "steak": 25.00, "sandwich": 8.00,
        "ramen": 10.00, "chicken": 12.00, "beer": 6.00, "wine": 10.00,
    },
    "JPY": {
        "coffee": 500, "burger": 1200, "pizza": 1500, "sushi": 2000,
        "salad": 1000, "pasta": 1400, "steak": 3000, "sandwich": 800,
        "ramen": 900, "chicken": 1200, "beer": 600, "wine": 1000,
    },
    "GBP": {
        "coffee": 4.50, "burger": 10.00, "pizza": 12.00, "sushi": 15.00,
        "salad": 8.50, "pasta": 11.00, "steak": 20.00, "sandwich": 6.50,
        "ramen": 8.00, "chicken": 10.00, "beer": 5.00, "wine": 8.00,
    },
}


def analyze_receipt(image_base64: str, target_country: str = "USD") -> Dict[str, Any]:
    """
    영수증 이미지 분석
    - 상호명, 품목, 금액, 원화 환산, 더치페이 정산 정보 반환
    """
    try:
        # Gemini 모델 선택
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Base64 이미지 디코딩
        image_data = base64.b64decode(image_base64)
        
        # 프롬프트 작성
        prompt = f"""
당신은 영수증 분석 전문가입니다. 다음 영수증 이미지를 분석하고 JSON 형식으로 다음 정보를 반환하세요:

1. merchant_name: 상호명
2. items: 품목 리스트 (각 항목: name, price, quantity)
3. total_local: 현지 통화 총합계
4. currency: 통화 코드 (USD, JPY, GBP 등)
5. date: 거래 날짜 (YYYY-MM-DD 형식)
6. category: 거래 카테고리 (food, transport, shopping, entertainment, healthcare, education, utility, other)

그리고 다음을 계산하세요:
7. exchange_rate: 원화 환율 (기본값: {EXCHANGE_RATES.get(target_country, 1300)})
8. total_krw: 원화 환산 금액
9. dutch_pay_per_person: 3명이 나눌 경우의 1인당 금액

응답은 반드시 유효한 JSON 형식이어야 합니다.
"""
        
        # Gemini API 호출
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        # 응답 파싱
        response_text = response.text
        
        # JSON 추출
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return {
                "success": False,
                "error": "영수증 분석 실패: 유효한 JSON을 추출할 수 없습니다"
            }
        
        json_str = response_text[json_start:json_end]
        result = json.loads(json_str)
        
        # 환율 및 원화 계산
        exchange_rate = EXCHANGE_RATES.get(target_country, 1300)
        total_local = float(result.get("total_local", 0))
        total_krw = total_local * exchange_rate
        dutch_pay_per_person = total_krw / 3
        
        return {
            "success": True,
            "merchant_name": result.get("merchant_name", "Unknown"),
            "items": result.get("items", []),
            "total_local": total_local,
            "currency": target_country,
            "exchange_rate": exchange_rate,
            "total_krw": round(total_krw, 2),
            "dutch_pay_per_person": round(dutch_pay_per_person, 2),
            "date": result.get("date", ""),
            "category": result.get("category", "other"),
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON 파싱 오류: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"영수증 분석 오류: {str(e)}"
        }


def analyze_price_before_purchase(
    image_or_text: str,
    target_country: str = "USD",
    is_image: bool = True
) -> Dict[str, Any]:
    """
    메뉴판/가격표 분석
    - 메뉴명, 가격, 원화 환산, 평균가 비교 정보 반환
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if is_image:
            # 이미지 분석
            image_data = base64.b64decode(image_or_text)
            prompt = f"""
당신은 메뉴판 분석 전문가입니다. 다음 메뉴판 이미지를 분석하고 JSON 형식으로 다음 정보를 반환하세요:

메뉴 항목들의 리스트:
1. name: 메뉴명
2. price: 가격
3. currency: 통화 코드

응답은 반드시 유효한 JSON 형식이어야 합니다.
예: {{"items": [{{"name": "Coffee", "price": 5.50, "currency": "USD"}}]}}
"""
            response = model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
        else:
            # 텍스트 분석
            prompt = f"""
당신은 메뉴판 분석 전문가입니다. 다음 메뉴판 텍스트를 분석하고 JSON 형식으로 다음 정보를 반환하세요:

메뉴 항목들의 리스트:
1. name: 메뉴명
2. price: 가격
3. currency: 통화 코드

응답은 반드시 유효한 JSON 형식이어야 합니다.
예: {{"items": [{{"name": "Coffee", "price": 5.50, "currency": "USD"}}]}}

메뉴판 텍스트:
{image_or_text}
"""
            response = model.generate_content(prompt)
        
        response_text = response.text
        
        # JSON 추출
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return {
                "success": False,
                "error": "메뉴판 분석 실패: 유효한 JSON을 추출할 수 없습니다"
            }
        
        json_str = response_text[json_start:json_end]
        result = json.loads(json_str)
        
        # 환율 및 평균가 비교
        exchange_rate = EXCHANGE_RATES.get(target_country, 1300)
        avg_prices = AVERAGE_PRICES.get(target_country, {})
        
        items = []
        for item in result.get("items", []):
            name = item.get("name", "").lower()
            price = float(item.get("price", 0))
            price_krw = price * exchange_rate
            
            # 평균가 찾기
            avg_price = None
            for key, value in avg_prices.items():
                if key.lower() in name:
                    avg_price = value
                    break
            
            # 평균가 비교
            if avg_price:
                percentage_diff = ((price - avg_price) / avg_price) * 100
                if percentage_diff < -10:
                    price_comparison = "저렴"
                elif percentage_diff > 10:
                    price_comparison = "비쌈"
                else:
                    price_comparison = "평균"
                
                comparison_message = f"현재 설정된 {target_country}의 {name} 평균가는 약 {avg_price:.2f} {target_country}입니다. 이 메뉴는 평균 대비 약 {abs(percentage_diff):.1f}% {'높게' if percentage_diff > 0 else '낮게'} 책정되어 있습니다."
            else:
                percentage_diff = 0
                price_comparison = "정보없음"
                comparison_message = f"{name}의 평균가 정보가 없습니다."
            
            items.append({
                "name": item.get("name", ""),
                "price_local": price,
                "currency": target_country,
                "price_krw": round(price_krw, 2),
                "exchange_rate": exchange_rate,
                "average_price": avg_price,
                "percentage_diff": round(percentage_diff, 2),
                "price_comparison": price_comparison,
                "comparison_message": comparison_message,
            })
        
        return {
            "success": True,
            "items": items,
            "currency": target_country,
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON 파싱 오류: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"메뉴판 분석 오류: {str(e)}"
        }
