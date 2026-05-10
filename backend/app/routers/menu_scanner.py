"""
메뉴판 가격 분석 및 비교 라우터
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services import gemini_service

router = APIRouter(prefix="/api/menu", tags=["menu"])


class MenuAnalysisRequest(BaseModel):
    """메뉴판 분석 요청"""
    image_base64: Optional[str] = None
    text: Optional[str] = None
    currency: str = "USD"


class MenuAnalysisResponse(BaseModel):
    """메뉴판 분석 응답"""
    success: bool
    items: Optional[list] = None
    error: Optional[str] = None


@router.post("/analyze")
async def analyze_menu(body: MenuAnalysisRequest):
    """
    메뉴판 가격 분석 및 평균가 비교
    
    - 이미지 또는 텍스트 입력 지원
    - 평균가와 비교하여 저렴/평균/비쌈 판정
    - 평균 대비 가격 차이 퍼센트 제공
    """
    try:
        if not body.image_base64 and not body.text:
            raise HTTPException(
                status_code=400,
                detail="Either image_base64 or text is required"
            )
        
        result = await gemini_service.analyze_menu_price(
            image_base64=body.image_base64,
            text=body.text,
            currency=body.currency
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "success": True,
            "items": result.get("items", []),
            "currency": body.currency,
            "analysis_summary": _generate_summary(result.get("items", []), body.currency),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_summary(items: list, currency: str) -> dict:
    """메뉴판 분석 요약 생성"""
    if not items:
        return {}
    
    # 저렴한 항목, 평균 항목, 비싼 항목 분류
    cheap_items = [item for item in items if item.get("price_comparison") == "저렴"]
    avg_items = [item for item in items if item.get("price_comparison") == "평균"]
    expensive_items = [item for item in items if item.get("price_comparison") == "비쌈"]
    
    # 평균 가격 차이 계산
    avg_diff = sum(item.get("percentage_diff", 0) for item in items) / len(items) if items else 0
    
    # 요약 메시지 생성
    if avg_diff < -10:
        overall_assessment = f"이 지역의 음식 가격은 평균보다 약 {abs(avg_diff):.1f}% 저렴합니다."
    elif avg_diff > 10:
        overall_assessment = f"이 지역의 음식 가격은 평균보다 약 {avg_diff:.1f}% 비쌉니다."
    else:
        overall_assessment = "이 지역의 음식 가격은 평균 수준입니다."
    
    return {
        "overall_assessment": overall_assessment,
        "cheap_items_count": len(cheap_items),
        "average_items_count": len(avg_items),
        "expensive_items_count": len(expensive_items),
        "average_price_difference": round(avg_diff, 2),
        "currency": currency,
    }
