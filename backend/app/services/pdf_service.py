"""
PDF 생성 서비스 - 거래 내역 증빙 자료
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


async def generate_transaction_report(
    user_name: str,
    transactions: List[Dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
    currency: str = "KRW",
) -> BytesIO:
    """
    거래 내역 PDF 보고서 생성
    
    Args:
        user_name: 사용자 이름
        transactions: 거래 내역 리스트
        start_date: 시작 날짜
        end_date: 종료 날짜
        currency: 통화
    
    Returns:
        BytesIO 객체 (PDF 파일)
    """
    
    # PDF 생성
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # 스타일
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
    )
    
    # 문서 요소
    elements = []
    
    # 제목
    elements.append(Paragraph("거래 내역 보고서", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 사용자 정보
    user_info = f"사용자: {user_name} | 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))
    
    # 요약 통계
    total_amount = sum(Decimal(str(tx.get("amount_krw", 0))) for tx in transactions)
    category_summary = _calculate_category_summary(transactions)
    
    elements.append(Paragraph("요약 통계", heading_style))
    summary_data = [
        ["항목", "금액"],
        ["총 지출액", f"{total_amount:,.0f} {currency}"],
        ["거래 건수", f"{len(transactions)}건"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # 카테고리별 요약
    elements.append(Paragraph("카테고리별 지출", heading_style))
    category_data = [["카테고리", "금액", "건수", "비율"]]
    
    for category, info in category_summary.items():
        percentage = (info["amount"] / total_amount * 100) if total_amount > 0 else 0
        category_data.append([
            category,
            f"{info['amount']:,.0f}",
            f"{info['count']}건",
            f"{percentage:.1f}%",
        ])
    
    category_table = Table(category_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(category_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # 거래 내역 상세
    elements.append(PageBreak())
    elements.append(Paragraph("거래 내역 상세", heading_style))
    
    # 거래 테이블
    transaction_data = [[
        "날짜",
        "상호명",
        "카테고리",
        "금액 (현지)",
        "금액 (원화)",
        "환율",
    ]]
    
    for tx in sorted(transactions, key=lambda x: x.get("transaction_date", ""), reverse=True):
        tx_date = tx.get("transaction_date", "")
        if isinstance(tx_date, datetime):
            tx_date = tx_date.strftime("%Y-%m-%d")
        
        transaction_data.append([
            tx_date,
            tx.get("merchant_name", ""),
            tx.get("category", ""),
            f"{tx.get('amount_local', 0):.2f} {tx.get('currency', '')}",
            f"{tx.get('amount_krw', 0):,.0f}",
            f"{tx.get('exchange_rate', 1):.4f}",
        ])
    
    tx_table = Table(transaction_data, colWidths=[1 * inch, 1.5 * inch, 1 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(tx_table)
    
    # PDF 생성
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


def _calculate_category_summary(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """카테고리별 요약 계산"""
    summary = {}
    
    for tx in transactions:
        category = tx.get("category", "other")
        amount = Decimal(str(tx.get("amount_krw", 0)))
        
        if category not in summary:
            summary[category] = {"amount": Decimal(0), "count": 0}
        
        summary[category]["amount"] += amount
        summary[category]["count"] += 1
    
    return summary
