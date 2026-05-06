"""
Gemini AI 연동 모듈
결제 텍스트 및 영수증 이미지 분석
"""
import json
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import google.generativeai as genai
from config import settings
from schemas import ClassifyResponse

logger = logging.getLogger(__name__)

# Gemini AI 초기화
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiClassifier:
    """Gemini AI를 사용한 지출 분류기"""
    
    # 지원하는 카테고리
    CATEGORIES = {
        'food': '식비',
        'transport': '교통',
        'housing': '주거',
        'study': '학업',
        'shopping': '쇼핑',
        'health': '의료',
        'transfer': '송금',
        'other': '기타',
    }
    
    @staticmethod
    def classify_text(text: str) -> ClassifyResponse:
        """
        결제 알림 텍스트 분석 및 분류
        
        Args:
            text: 결제 알림 텍스트
            
        Returns:
            ClassifyResponse: 분류 결과
        """
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""다음 결제 알림 텍스트를 분석하고 JSON 형식으로 반환해줘:

결제 알림: {text}

다음 정보를 추출해줘:
1. merchant (상호명): 결제처 이름
2. amount (금액): 숫자만 추출
3. currency (통화): KRW, USD, EUR 등
4. category (카테고리): {', '.join(GeminiClassifier.CATEGORIES.keys())} 중 하나
5. confidence (신뢰도): 0.0 ~ 1.0 사이의 값
6. description (설명): 간단한 설명

JSON 형식으로만 반환해줘:
{{
    "merchant": "상호명",
    "amount": 0.0,
    "currency": "KRW",
    "category": "food",
    "confidence": 0.95,
    "description": "설명"
}}"""
            
            response = model.generate_content(prompt)
            
            # JSON 파싱
            result_text = response.text
            # JSON 블록 추출
            if '```json' in result_text:
                json_str = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                json_str = result_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_text.strip()
            
            result = json.loads(json_str)
            
            # 유효성 검증
            result['amount'] = float(result.get('amount', 0))
            result['confidence'] = float(result.get('confidence', 0.5))
            
            if result['category'] not in GeminiClassifier.CATEGORIES:
                result['category'] = 'other'
            
            return ClassifyResponse(
                merchant=result['merchant'],
                amount=result['amount'],
                currency=result.get('currency', 'KRW'),
                category=result['category'],
                confidence=result['confidence'],
                description=result.get('description'),
                raw_analysis=response.text
            )
            
        except Exception as e:
            logger.error(f"Gemini 텍스트 분류 오류: {str(e)}")
            # 기본값 반환
            return ClassifyResponse(
                merchant="Unknown",
                amount=0.0,
                currency="KRW",
                category="other",
                confidence=0.0,
                description=f"분류 오류: {str(e)}"
            )
    
    @staticmethod
    def classify_image(image_base64: str) -> ClassifyResponse:
        """
        영수증 이미지 분석 및 분류 (OCR)
        
        Args:
            image_base64: Base64 인코딩된 이미지
            
        Returns:
            ClassifyResponse: 분류 결과
        """
        try:
            model = genai.GenerativeModel('gemini-pro-vision')
            
            # Base64 이미지 데이터 준비
            image_data = {
                "mime_type": "image/jpeg",
                "data": image_base64
            }
            
            prompt = f"""이 영수증 이미지를 분석하고 JSON 형식으로 반환해줘:

다음 정보를 추출해줘:
1. merchant (상호명): 가게 이름
2. amount (금액): 총액 (숫자만)
3. currency (통화): KRW, USD, EUR 등
4. category (카테고리): {', '.join(GeminiClassifier.CATEGORIES.keys())} 중 하나
5. confidence (신뢰도): 0.0 ~ 1.0 사이의 값 (이미지 품질에 따라)
6. description (설명): 구매 항목 요약

JSON 형식으로만 반환해줘:
{{
    "merchant": "가게명",
    "amount": 0.0,
    "currency": "KRW",
    "category": "food",
    "confidence": 0.9,
    "description": "구매 항목"
}}"""
            
            response = model.generate_content([prompt, image_data])
            
            # JSON 파싱
            result_text = response.text
            if '```json' in result_text:
                json_str = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                json_str = result_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_text.strip()
            
            result = json.loads(json_str)
            
            # 유효성 검증
            result['amount'] = float(result.get('amount', 0))
            result['confidence'] = float(result.get('confidence', 0.5))
            
            if result['category'] not in GeminiClassifier.CATEGORIES:
                result['category'] = 'other'
            
            return ClassifyResponse(
                merchant=result['merchant'],
                amount=result['amount'],
                currency=result.get('currency', 'KRW'),
                category=result['category'],
                confidence=result['confidence'],
                description=result.get('description'),
                raw_analysis=response.text
            )
            
        except Exception as e:
            logger.error(f"Gemini 이미지 분류 오류: {str(e)}")
            return ClassifyResponse(
                merchant="Unknown",
                amount=0.0,
                currency="KRW",
                category="other",
                confidence=0.0,
                description=f"이미지 분석 오류: {str(e)}"
            )
    
    @staticmethod
    def classify_image_from_url(image_url: str) -> ClassifyResponse:
        """
        URL에서 이미지를 다운로드하여 분석
        
        Args:
            image_url: 이미지 URL
            
        Returns:
            ClassifyResponse: 분류 결과
        """
        try:
            import httpx
            
            # 이미지 다운로드
            async def download_image():
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    return base64.b64encode(response.content).decode('utf-8')
            
            # 동기 방식으로 처리 (간단한 구현)
            import asyncio
            image_base64 = asyncio.run(download_image())
            
            return GeminiClassifier.classify_image(image_base64)
            
        except Exception as e:
            logger.error(f"이미지 URL 처리 오류: {str(e)}")
            return ClassifyResponse(
                merchant="Unknown",
                amount=0.0,
                currency="KRW",
                category="other",
                confidence=0.0,
                description=f"이미지 다운로드 오류: {str(e)}"
            )
