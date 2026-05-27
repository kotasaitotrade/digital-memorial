#!/usr/bin/env python3
"""
REQUIREMENTS.md → PDF 変換スクリプト（reportlab使用・日本語対応）
Usage: python3 generate_pdf.py
"""
import os
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# --- 日本語フォント登録 ---
FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB W3.ttc",
    "/Library/Fonts/Arial Unicode MS.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]

FONT_BOLD_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
]

def register_font():
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("JP", path))
                break
            except Exception:
                continue
    for path in FONT_BOLD_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("JP-Bold", path))
                break
            except Exception:
                continue

register_font()

# フォント名（フォールバック）
def jp(bold=False):
    fonts = pdfmetrics.getRegisteredFontNames()
    if bold and "JP-Bold" in fonts:
        return "JP-Bold"
    if "JP" in fonts:
        return "JP"
    return "Helvetica-Bold" if bold else "Helvetica"

# --- カラー定義 ---
GREEN_DARK = colors.HexColor("#1a5c38")
GREEN_MID = colors.HexColor("#2d7a4f")
GREEN_LIGHT = colors.HexColor("#f0f7f4")
GRAY_LIGHT = colors.HexColor("#f7f7f7")
GRAY_BORDER = colors.HexColor("#dddddd")
TEXT_DARK = colors.HexColor("#1a1a1a")

# --- スタイル定義 ---
def build_styles():
    s = {}
    base_font = jp()
    bold_font = jp(bold=True)

    s["title"] = ParagraphStyle("title",
        fontName=bold_font, fontSize=20, leading=28,
        textColor=GREEN_DARK, spaceAfter=6, spaceBefore=0,
        alignment=TA_LEFT)

    s["h1"] = ParagraphStyle("h1",
        fontName=bold_font, fontSize=16, leading=22,
        textColor=GREEN_DARK, spaceBefore=18, spaceAfter=6,
        borderPad=(0, 0, 4, 0))

    s["h2"] = ParagraphStyle("h2",
        fontName=bold_font, fontSize=13, leading=18,
        textColor=GREEN_DARK, spaceBefore=14, spaceAfter=4)

    s["h3"] = ParagraphStyle("h3",
        fontName=bold_font, fontSize=11, leading=16,
        textColor=GREEN_MID, spaceBefore=10, spaceAfter=3,
        leftIndent=8, borderLeftColor=GREEN_MID, borderLeftWidth=3,
        borderLeftPadding=6)

    s["h4"] = ParagraphStyle("h4",
        fontName=bold_font, fontSize=10, leading=14,
        textColor=TEXT_DARK, spaceBefore=8, spaceAfter=2)

    s["body"] = ParagraphStyle("body",
        fontName=base_font, fontSize=9, leading=15,
        textColor=TEXT_DARK, spaceAfter=4)

    s["bullet"] = ParagraphStyle("bullet",
        fontName=base_font, fontSize=9, leading=15,
        textColor=TEXT_DARK, spaceAfter=2, leftIndent=12,
        firstLineIndent=-8)

    s["code"] = ParagraphStyle("code",
        fontName="Courier", fontSize=7.5, leading=12,
        textColor=TEXT_DARK, backColor=GRAY_LIGHT,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4,
        borderPad=6)

    s["meta"] = ParagraphStyle("meta",
        fontName=base_font, fontSize=8.5, leading=13,
        textColor=colors.HexColor("#555555"), spaceAfter=2)

    return s


def escape_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def parse_markdown_to_flowables(md_path, styles):
    flowables = []
    is_first = True

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip("\n")

        # コードブロック
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                flowables.append(Preformatted(code_text, styles["code"]))
                flowables.append(Spacer(1, 3*mm))
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # テーブル
        if line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            if not all(re.match(r"^[-:]+$", c) for c in cells):
                table_rows.append(cells)
            i += 1
            continue
        else:
            if in_table:
                in_table = False
                if table_rows:
                    col_count = max(len(r) for r in table_rows)
                    # 列幅を均等に
                    page_w = 170*mm
                    col_w = page_w / col_count

                    tbl_data = []
                    for ri, row in enumerate(table_rows):
                        row_data = []
                        style = styles["meta"] if ri == 0 else styles["body"]
                        for ci, cell in enumerate(row):
                            txt = escape_xml(cell)
                            if ri == 0:
                                p = Paragraph(f"<b>{txt}</b>", styles["meta"])
                            else:
                                p = Paragraph(txt, styles["body"])
                            row_data.append(p)
                        # 列数が足りない場合に空を追加
                        while len(row_data) < col_count:
                            row_data.append(Paragraph("", styles["body"]))
                        tbl_data.append(row_data)

                    tbl = Table(tbl_data, colWidths=[col_w]*col_count)
                    tbl.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), GREEN_DARK),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), jp(bold=True)),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
                        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]))
                    flowables.append(tbl)
                    flowables.append(Spacer(1, 4*mm))

        # 空行
        if not line.strip():
            flowables.append(Spacer(1, 3*mm))
            i += 1
            continue

        # 水平線
        if line.strip().startswith("---") and len(line.strip()) >= 3 and all(c == "-" for c in line.strip()):
            flowables.append(HRFlowable(width="100%", thickness=1,
                                        color=GRAY_BORDER, spaceAfter=4))
            i += 1
            continue

        # 見出し
        h_match = re.match(r"^(#{1,4})\s+(.*)", line)
        if h_match:
            level = len(h_match.group(1))
            text = escape_xml(h_match.group(2))

            if level == 1:
                if is_first:
                    flowables.append(Paragraph(text, styles["title"]))
                    flowables.append(HRFlowable(width="100%", thickness=2,
                                                color=GREEN_DARK, spaceAfter=6))
                    is_first = False
                else:
                    flowables.append(PageBreak())
                    flowables.append(Paragraph(text, styles["h1"]))
                    flowables.append(HRFlowable(width="100%", thickness=1.5,
                                                color=GREEN_DARK, spaceAfter=4))
            elif level == 2:
                flowables.append(Paragraph(text, styles["h2"]))
                flowables.append(HRFlowable(width="100%", thickness=0.7,
                                            color=GRAY_BORDER, spaceAfter=3))
            elif level == 3:
                flowables.append(Paragraph(f"<font color='#{GREEN_MID.hexval()[2:]}'>▌</font> {text}",
                                           styles["h3"]))
            elif level == 4:
                flowables.append(Paragraph(text, styles["h4"]))
            i += 1
            continue

        # リスト
        li_match = re.match(r"^(\s*)[-*]\s+(.*)", line)
        if li_match:
            indent = len(li_match.group(1))
            text = escape_xml(li_match.group(2))
            bullet_style = ParagraphStyle("bullet_indent",
                parent=styles["bullet"],
                leftIndent=12 + indent * 8,
                firstLineIndent=-8)
            flowables.append(Paragraph(f"• {text}", bullet_style))
            i += 1
            continue

        # 番号付きリスト
        num_match = re.match(r"^\s*\d+\.\s+(.*)", line)
        if num_match:
            text = escape_xml(num_match.group(1))
            flowables.append(Paragraph(f"　{text}", styles["bullet"]))
            i += 1
            continue

        # blockquote
        bq_match = re.match(r"^>\s*(.*)", line)
        if bq_match:
            text = escape_xml(bq_match.group(1))
            bq_style = ParagraphStyle("bq", parent=styles["body"],
                leftIndent=12, backColor=GREEN_LIGHT,
                borderLeftColor=GREEN_DARK, borderLeftWidth=3,
                borderLeftPadding=8, spaceBefore=4, spaceAfter=4)
            flowables.append(Paragraph(f"<i>{text}</i>", bq_style))
            i += 1
            continue

        # 通常テキスト（インラインマークダウン簡易変換）
        text = escape_xml(line)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
        flowables.append(Paragraph(text, styles["body"]))
        i += 1

    return flowables


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(jp(), 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    page_num = canvas.getPageNumber()
    canvas.drawRightString(A4[0] - 20*mm, 12*mm, f"- {page_num} -")
    canvas.drawString(20*mm, 12*mm, "Digital Memorial — 要件定義書")
    canvas.restoreState()


def generate_pdf(md_path, pdf_path):
    styles = build_styles()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title="Digital Memorial 要件定義書",
        author="Digital Memorial",
    )

    flowables = parse_markdown_to_flowables(md_path, styles)
    doc.build(flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF生成完了: {pdf_path}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    md = "REQUIREMENTS.md"
    pdf = "REQUIREMENTS.pdf"
    generate_pdf(md, pdf)
    os.system(f"open '{pdf}'")
