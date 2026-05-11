"""
메뉴판 스캐너 라우터 - 현지 물가 비교
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.services import gemini_service, exchange_rate_service

router = APIRouter(prefix="/api/menu", tags=["menu"])


class MenuAnalyzeRequest(BaseModel):
    image_base64: Optional[str] = None
    text: Optional[str] = None
    currency: str = "USD"


@router.post("/analyze")
async def analyze_menu(body: MenuAnalyzeRequest):
    """
    메뉴판 이미지 또는 텍스트 분석
    - 메뉴명 + 가격 추출
    - 현지 평균 단가와 비교
    - 몇 % 저렴/비싼지 알림
    - KRW 환산 가격 제공
    """
    if not body.image_base64 and not body.text:
        return {"success": False, "error": "image_base64 또는 text 중 하나를 제공해야 합니다"}

    result = await gemini_service.analyze_menu_image(
        image_base64=body.image_base64,
        text=body.text,
        currency=body.currency,
    )

    if not result["success"]:
        return result

    # 각 항목에 KRW 환산 추가
    currency = result.get("currency", body.currency)
    rate = await exchange_rate_service.get_rate_to_krw(currency)

    for item in result.get("items", []):
        item["price_krw"] = round(item.get("price", 0) * rate, 0)
        item["exchange_rate"] = rate

    return result
