import google.generativeai as genai
import base64
import json
import re
from typing import Optional, Dict, Any, List
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    return EXCHANGE_RATES.get(currency, 1300)

def get_average_price(currency: str, item_name: str) -> Optional[float]:
    if currency not in AVERAGE_PRICES:
        return None
    
    item_lower = item_name.lower()
    prices = AVERAGE_PRICES[currency]
    
    for key, price in prices.items():
        if key in item_lower or item_lower in key:
            return price
    
    return None

def extract_json_from_text(text: str) -> Dict[str, Any]:
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {}

def analyze_receipt(image_data: str, target_country: str = "USD") -> Dict[str, Any]:
    """
    영수증 이미지 분석 - OCR 기능
    상호명, 품목리스트, 현지통화 총합계, 원화 환산 금액, 더치페이 정산 추천 금액 포함
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Please analyze this receipt image and extract the following information in JSON format:
        
        {{
            "merchant_name": "Name of the store/restaurant",
            "items": [
                {{"name": "item name", "quantity": 1, "price": 0.00}},
            ],
            "subtotal": 0.00,
            "tax": 0.00,
            "total": 0.00,
            "currency": "{target_country}",
            "date": "YYYY-MM-DD",
            "time": "HH:MM"
        }}
        
        Return ONLY valid JSON, no additional text.
        """
        
        response = model.generate_content([
            {
                "mime_type": "image/jpeg",
                "data": image_data,
            },
            prompt
        ])
        
        receipt_data = extract_json_from_text(response.text)
        
        if not receipt_data:
            receipt_data = {
                "merchant_name": "Unknown",
                "items": [],
                "subtotal": 0.0,
                "tax": 0.0,
                "total": 0.0,
                "currency": target_country,
            }
        
        total_local = receipt_data.get("total", 0.0)
        exchange_rate = get_exchange_rate(target_country)
        total_krw = total_local * exchange_rate
        
        items = receipt_data.get("items", [])
        num_people = len([item for item in items if item]) if items else 1
        if num_people == 0:
            num_people = 1
        
        dutch_pay_per_person = total_krw / num_people
        
        result = {
            "merchant_name": receipt_data.get("merchant_name", "Unknown"),
            "items": items,
            "subtotal_local": receipt_data.get("subtotal", 0.0),
            "tax_local": receipt_data.get("tax", 0.0),
            "total_local": total_local,
            "currency": target_country,
            "total_krw": round(total_krw, 2),
            "exchange_rate": exchange_rate,
            "dutch_pay": {
                "num_people": num_people,
                "per_person_krw": round(dutch_pay_per_person, 2),
                "per_person_local": round(total_local / num_people, 2),
            },
            "date": receipt_data.get("date"),
            "time": receipt_data.get("time"),
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "merchant_name": "Error",
            "total_krw": 0.0,
            "currency": target_country,
        }

def analyze_price_before_purchase(image_data_or_text: str, target_country: str = "USD", is_image: bool = False) -> Dict[str, Any]:
    """
    메뉴판/가격표 분석 - 결제 전 가격 비교
    메뉴명, 현지 가격, 원화 환산 금액, 평균가 비교 멘트 포함
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if is_image:
            prompt = f"""
            Analyze this menu/price list image and extract items with prices in JSON format:
            
            {{
                "menu_items": [
                    {{"name": "item name", "price": 0.00, "description": "brief description"}},
                ],
                "currency": "{target_country}",
                "restaurant_name": "Name if visible"
            }}
            
            Return ONLY valid JSON, no additional text.
            """
            
            response = model.generate_content([
                {
                    "mime_type": "image/jpeg",
                    "data": image_data_or_text,
                },
                prompt
            ])
        else:
            prompt = f"""
            Parse this menu text and extract items with prices in JSON format:
            
            {{
                "menu_items": [
                    {{"name": "item name", "price": 0.00, "description": "brief description"}},
                ],
                "currency": "{target_country}",
                "restaurant_name": "Name if mentioned"
            }}
            
            Text to parse:
            {image_data_or_text}
            
            Return ONLY valid JSON, no additional text.
            """
            
            response = model.generate_content(prompt)
        
        menu_data = extract_json_from_text(response.text)
        
        if not menu_data:
            menu_data = {
                "menu_items": [],
                "currency": target_country,
                "restaurant_name": "Unknown",
            }
        
        exchange_rate = get_exchange_rate(target_country)
        
        analyzed_items = []
        for item in menu_data.get("menu_items", []):
            item_name = item.get("name", "Unknown")
            local_price = item.get("price", 0.0)
            krw_price = local_price * exchange_rate
            
            average_price = get_average_price(target_country, item_name)
            
            if average_price:
                price_diff = local_price - average_price
                price_diff_percent = (price_diff / average_price * 100) if average_price > 0 else 0
                
                if price_diff > 0:
                    comparison = f"현재 설정된 {target_country}의 {item_name} 평균가는 약 {average_price:.2f}입니다. 이 메뉴는 평균 대비 약 {price_diff_percent:.1f}% 높게 책정되어 있습니다."
                elif price_diff < 0:
                    comparison = f"현재 설정된 {target_country}의 {item_name} 평균가는 약 {average_price:.2f}입니다. 이 메뉴는 평균 대비 약 {abs(price_diff_percent):.1f}% 낮게 책정되어 있습니다."
                else:
                    comparison = f"현재 설정된 {target_country}의 {item_name} 평균가는 약 {average_price:.2f}입니다. 이 메뉴는 평균 가격과 동일하게 책정되어 있습니다."
            else:
                comparison = f"이 메뉴의 평균 가격 정보가 없습니다."
            
            analyzed_items.append({
                "name": item_name,
                "price_local": local_price,
                "price_krw": round(krw_price, 2),
                "currency": target_country,
                "description": item.get("description", ""),
                "average_price_local": average_price,
                "price_comparison": comparison,
            })
        
        result = {
            "restaurant_name": menu_data.get("restaurant_name", "Unknown"),
            "menu_items": analyzed_items,
            "currency": target_country,
            "exchange_rate": exchange_rate,
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "restaurant_name": "Error",
            "menu_items": [],
            "currency": target_country,
        }
