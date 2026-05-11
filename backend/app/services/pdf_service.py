"""
PDF 증빙자료 생성 서비스 - reportlab 사용
"""
import io
import json
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_transaction_report(
    transactions: List[Dict[str, Any]],
    start_date: str,
    end_date: str,
    user_name: str = "사용자",
    currency: str = "KRW"
) -> bytes:
    """
    거래 내역 PDF 보고서 생성
    
    Returns: PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # 스타일 정의
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1a1a2e"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        alignment=TA_CENTER,
        textColor=colors.gray,
    )
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading2"],
        fontSize=13,
        spaceAfter=4,
        textColor=colors.HexColor("#16213e"),
    )
    normal_style = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=2,
    )

    elements = []

    # ── 제목 ──────────────────────────────────────────
    elements.append(Paragraph("Finance Compass", title_style))
    elements.append(Paragraph("거래 내역 증빙 보고서", subtitle_style))
    elements.append(Paragraph(f"기간: {start_date} ~ {end_date}", subtitle_style))
    elements.append(Paragraph(
        f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 사용자: {user_name}",
        subtitle_style
    ))
    elements.append(Spacer(1, 8 * mm))

    # ── 요약 통계 ──────────────────────────────────────
    elements.append(Paragraph("요약", header_style))

    total_krw = sum(t.get("amount_krw", 0) for t in transactions)
    total_count = len(transactions)

    # 카테고리별 합계
    category_totals: Dict[str, float] = {}
    for t in transactions:
        cat = t.get("category", "other")
        category_totals[cat] = category_totals.get(cat, 0) + t.get("amount_krw", 0)

    summary_data = [
        ["항목", "값"],
        ["총 거래 건수", f"{total_count}건"],
        ["총 지출 (KRW)", f"₩{total_krw:,.0f}"],
        ["기간", f"{start_date} ~ {end_date}"],
    ]

    summary_table = Table(summary_data, colWidths=[80 * mm, 80 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    # ── 카테고리별 지출 ────────────────────────────────
    if category_totals:
        elements.append(Paragraph("카테고리별 지출", header_style))
        cat_data = [["카테고리", "지출 금액 (KRW)", "비율"]]
        for cat, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
            pct = (amount / total_krw * 100) if total_krw > 0 else 0
            cat_data.append([
                cat.upper(),
                f"₩{amount:,.0f}",
                f"{pct:.1f}%",
            ])

        cat_table = Table(cat_data, colWidths=[60 * mm, 70 * mm, 40 * mm])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 6 * mm))

    # ── 거래 상세 내역 ─────────────────────────────────
    elements.append(Paragraph("거래 상세 내역", header_style))

    tx_data = [["날짜", "상호명", "카테고리", "현지금액", "KRW", "출처"]]
    for t in sorted(transactions, key=lambda x: x.get("transaction_date", ""), reverse=True):
        date_str = t.get("transaction_date", "")
        if isinstance(date_str, str) and "T" in date_str:
            date_str = date_str.split("T")[0]

        tx_data.append([
            date_str,
            (t.get("merchant_name", "") or "")[:20],
            t.get("category", "other").upper(),
            f"{t.get('amount_local', 0):.2f} {t.get('currency', '')}",
            f"₩{t.get('amount_krw', 0):,.0f}",
            t.get("source", "manual")[:10],
        ])

    tx_table = Table(tx_data, colWidths=[22*mm, 45*mm, 22*mm, 30*mm, 28*mm, 18*mm])
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#533483")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (2, -1), "LEFT"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
    ]))
    elements.append(tx_table)
    elements.append(Spacer(1, 6 * mm))

    # ── 푸터 ──────────────────────────────────────────
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.gray, alignment=TA_CENTER)
    elements.append(Paragraph(
        "본 문서는 Finance Compass 앱에서 자동 생성된 거래 증빙 자료입니다.",
        footer_style
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
