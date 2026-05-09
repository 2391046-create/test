"""영수증/메뉴판 스캐너 (Gemini AI)"""
import base64
import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gemini_service import analyze_receipt, analyze_price_before_purchase

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


class ScanReceiptRequest(BaseModel):
    image_base64: str
    target_country: str = "USD"


class AnalyzePriceRequest(BaseModel):
    image_base64: Optional[str] = None
    text: Optional[str] = None
    target_country: str = "USD"


class ScannerResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/receipt", response_model=ScannerResponse)
async def scan_receipt(body: ScanReceiptRequest):
    """영수증 이미지 분석 (Gemini 1.5 Flash)"""
    try:
        if not body.image_base64:
            raise ValueError("image_base64 is required")

        # Base64 디코딩
        try:
            image_data = base64.b64decode(body.image_base64)
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {str(e)}")

        result = await analyze_receipt(image_data, body.target_country)

        if isinstance(result, dict) and "error" in result:
            return ScannerResponse(success=False, error=result["error"])

        return ScannerResponse(success=True, data=result)

    except Exception as e:
        return ScannerResponse(success=False, error=str(e))


@router.post("/price", response_model=ScannerResponse)
async def analyze_price(body: AnalyzePriceRequest):
    """메뉴판/가격표 분석 (이미지 또는 텍스트)"""
    try:
        if not body.image_base64 and not body.text:
            raise ValueError("Either image_base64 or text is required")

        image_data = None
        is_image = False

        if body.image_base64:
            try:
                image_data = base64.b64decode(body.image_base64)
                is_image = True
            except Exception as e:
                raise ValueError(f"Invalid base64 image: {str(e)}")

        result = await analyze_price_before_purchase(
            image_data or body.text, body.target_country, is_image
        )

        if isinstance(result, dict) and "error" in result:
            return ScannerResponse(success=False, error=result["error"])

        return ScannerResponse(success=True, data=result)

    except Exception as e:
        return ScannerResponse(success=False, error=str(e))
