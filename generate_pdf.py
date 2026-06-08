#!/usr/bin/env python3
"""
REQUIREMENTS.md → PDF 変換スクリプト（reportlab使用・日本語対応）
Usage: python3 generate_pdf.py
"""
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_LEFT

# --- 日本語CIDフォント登録 ---
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))   # ゴシック（本文・見出し）
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))       # 明朝（細字）

JP      = "HeiseiKakuGo-W5"
JP_BOLD = "HeiseiKakuGo-W5"   # CIDフォントはウェイト切替不可なので同じフォント
MONO    = "Courier"

# --- カラー定義 ---
GREEN_DARK  = colors.HexColor("#1a5c38")
GREEN_MID   = colors.HexColor("#2d7a4f")
GREEN_LIGHT = colors.HexColor("#e8f5ee")
GRAY_LIGHT  = colors.HexColor("#f5f5f5")
GRAY_BORDER = colors.HexColor("#cccccc")
TEXT_DARK   = colors.HexColor("#1a1a1a")
TEXT_GRAY   = colors.HexColor("#555555")
WHITE       = colors.white

# --- スタイル定義 ---
def build_styles():
    s = {}

    s["title"] = ParagraphStyle("title",
        fontName=JP_BOLD, fontSize=20, leading=30,
        textColor=GREEN_DARK, spaceAfter=8, spaceBefore=0)

    s["h1"] = ParagraphStyle("h1",
        fontName=JP_BOLD, fontSize=15, leading=22,
        textColor=GREEN_DARK, spaceBefore=16, spaceAfter=6)

    s["h2"] = ParagraphStyle("h2",
        fontName=JP_BOLD, fontSize=12, leading=18,
        textColor=GREEN_DARK, spaceBefore=14, spaceAfter=4)

    s["h3"] = ParagraphStyle("h3",
        fontName=JP_BOLD, fontSize=10.5, leading=16,
        textColor=GREEN_MID, spaceBefore=10, spaceAfter=3,
        leftIndent=10)

    s["h4"] = ParagraphStyle("h4",
        fontName=JP_BOLD, fontSize=9.5, leading=14,
        textColor=TEXT_DARK, spaceBefore=8, spaceAfter=2,
        leftIndent=10)

    s["body"] = ParagraphStyle("body",
        fontName=JP, fontSize=9, leading=16,
        textColor=TEXT_DARK, spaceAfter=4)

    s["bullet"] = ParagraphStyle("bullet",
        fontName=JP, fontSize=9, leading=15,
        textColor=TEXT_DARK, spaceAfter=2,
        leftIndent=16, firstLineIndent=-10)

    s["bullet2"] = ParagraphStyle("bullet2",
        fontName=JP, fontSize=9, leading=15,
        textColor=TEXT_DARK, spaceAfter=2,
        leftIndent=28, firstLineIndent=-10)

    s["numbered"] = ParagraphStyle("numbered",
        fontName=JP, fontSize=9, leading=15,
        textColor=TEXT_DARK, spaceAfter=2,
        leftIndent=16, firstLineIndent=-10)

    s["code"] = ParagraphStyle("code",
        fontName=JP, fontSize=7.5, leading=13,
        textColor=TEXT_DARK, backColor=GRAY_LIGHT,
        leftIndent=10, rightIndent=10,
        spaceBefore=4, spaceAfter=4,
        borderPad=8)

    s["blockquote"] = ParagraphStyle("blockquote",
        fontName=JP, fontSize=9, leading=16,
        textColor=colors.HexColor("#333333"),
        backColor=GREEN_LIGHT,
        leftIndent=14, rightIndent=4,
        spaceBefore=4, spaceAfter=4,
        borderPad=8)

    s["table_header"] = ParagraphStyle("table_header",
        fontName=JP_BOLD, fontSize=8, leading=12,
        textColor=WHITE)

    s["table_cell"] = ParagraphStyle("table_cell",
        fontName=JP, fontSize=8, leading=12,
        textColor=TEXT_DARK)

    s["footer"] = ParagraphStyle("footer",
        fontName=JP, fontSize=8, leading=12,
        textColor=TEXT_GRAY)

    return s


# --- インライン Markdown 変換 ---
def inline_md(text, base_font=JP):
    """**bold**, `code`, [text](url) を ReportLab XML に変換する"""
    # XMLエスケープ
    text = (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # `code`
    text = re.sub(r"`([^`]+)`",
                  rf"<font name='{MONO}' size='8'>\1</font>", text)
    # [text](url) → text のみ表示
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text


def parse_markdown(md_path, styles):
    flowables = []
    is_title_done = False

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_code = False
    code_buf = []
    in_table = False
    table_rows = []
    num_counter = [0]  # 番号付きリスト用（参照渡し）

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        col_count = max(len(r) for r in table_rows)
        page_w = 170 * mm

        # 列幅：1列目をやや広く、残りを均等
        if col_count == 1:
            col_widths = [page_w]
        elif col_count == 2:
            col_widths = [page_w * 0.35, page_w * 0.65]
        elif col_count == 3:
            col_widths = [page_w * 0.25, page_w * 0.40, page_w * 0.35]
        elif col_count == 4:
            col_widths = [page_w * 0.20, page_w * 0.30, page_w * 0.25, page_w * 0.25]
        else:
            col_widths = [page_w / col_count] * col_count

        tbl_data = []
        for ri, row in enumerate(table_rows):
            row_cells = []
            for ci in range(col_count):
                raw = row[ci] if ci < len(row) else ""
                txt = inline_md(raw)
                st = styles["table_header"] if ri == 0 else styles["table_cell"]
                row_cells.append(Paragraph(txt, st))
            tbl_data.append(row_cells)

        tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  GREEN_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.4, GRAY_BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flowables.append(tbl)
        flowables.append(Spacer(1, 4 * mm))
        table_rows.clear()

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")

        # ── コードブロック ──────────────────────────────────────
        if raw.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                # コードブロックをTableで枠付き表示（日本語対応）
                code_text = "\n".join(code_buf)
                # 行ごとにParagraphに変換
                code_paras = []
                for cl in code_buf:
                    escaped = (cl.replace("&", "&amp;")
                                 .replace("<", "&lt;")
                                 .replace(">", "&gt;"))
                    code_paras.append(Paragraph(escaped, styles["code"]))
                if not code_paras:
                    code_paras.append(Paragraph("", styles["code"]))
                code_tbl = Table([[code_paras]], colWidths=[170 * mm])
                code_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), GRAY_LIGHT),
                    ("BOX",        (0, 0), (0, 0), 0.8, GRAY_BORDER),
                    ("LEFTPADDING",  (0, 0), (0, 0), 10),
                    ("RIGHTPADDING", (0, 0), (0, 0), 10),
                    ("TOPPADDING",   (0, 0), (0, 0), 8),
                    ("BOTTOMPADDING",(0, 0), (0, 0), 8),
                    ("VALIGN",       (0, 0), (0, 0), "TOP"),
                ]))
                flowables.append(code_tbl)
                flowables.append(Spacer(1, 3 * mm))
                code_buf = []
            i += 1
            continue

        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        # ── テーブル ──────────────────────────────────────────
        if raw.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            cells = [c.strip() for c in raw.strip().split("|")[1:-1]]
            # セパレーター行（|---|---|）はスキップ
            if not all(re.match(r"^[-: ]+$", c) for c in cells if c):
                table_rows.append(cells)
            i += 1
            continue
        else:
            if in_table:
                in_table = False
                flush_table()

        # ── 空行 ────────────────────────────────────────────
        if not raw.strip():
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # ── 水平線 ──────────────────────────────────────────
        if re.match(r"^-{3,}$", raw.strip()):
            flowables.append(HRFlowable(
                width="100%", thickness=0.8, color=GRAY_BORDER,
                spaceBefore=2, spaceAfter=2))
            i += 1
            continue

        # ── 見出し ──────────────────────────────────────────
        h_match = re.match(r"^(#{1,4}) +(.*)", raw)
        if h_match:
            level = len(h_match.group(1))
            text = inline_md(h_match.group(2))

            if level == 1:
                if not is_title_done:
                    flowables.append(Paragraph(text, styles["title"]))
                    flowables.append(HRFlowable(
                        width="100%", thickness=2.5, color=GREEN_DARK,
                        spaceBefore=2, spaceAfter=8))
                    is_title_done = True
                else:
                    flowables.append(PageBreak())
                    flowables.append(Paragraph(text, styles["h1"]))
                    flowables.append(HRFlowable(
                        width="100%", thickness=1.5, color=GREEN_DARK,
                        spaceBefore=2, spaceAfter=4))
            elif level == 2:
                flowables.append(Spacer(1, 2 * mm))
                flowables.append(Paragraph(text, styles["h2"]))
                flowables.append(HRFlowable(
                    width="100%", thickness=0.6, color=GRAY_BORDER,
                    spaceBefore=1, spaceAfter=3))
            elif level == 3:
                flowables.append(Paragraph(
                    f"<font color='#1a5c38'>■</font> {text}",
                    styles["h3"]))
            elif level == 4:
                flowables.append(Paragraph(
                    f"<font color='#2d7a4f'>◆</font> {text}",
                    styles["h4"]))
            i += 1
            continue

        # ── 箇条書き（ネスト対応）────────────────────────────
        li_match = re.match(r"^( *)[-*] +(.*)", raw)
        if li_match:
            indent_level = len(li_match.group(1)) // 2
            text = inline_md(li_match.group(2))
            st = styles["bullet2"] if indent_level >= 1 else styles["bullet"]
            flowables.append(Paragraph(f"• {text}", st))
            i += 1
            continue

        # ── 番号付きリスト ───────────────────────────────────
        num_match = re.match(r"^ *(\d+)\. +(.*)", raw)
        if num_match:
            num = num_match.group(1)
            text = inline_md(num_match.group(2))
            flowables.append(Paragraph(f"{num}. {text}", styles["numbered"]))
            i += 1
            continue

        # ── 引用（blockquote）────────────────────────────────
        bq_match = re.match(r"^> *(.*)", raw)
        if bq_match:
            text = inline_md(bq_match.group(1))
            flowables.append(Paragraph(text, styles["blockquote"]))
            i += 1
            continue

        # ── 通常テキスト ─────────────────────────────────────
        text = inline_md(raw)
        flowables.append(Paragraph(text, styles["body"]))
        i += 1

    # ファイル末尾でテーブルが閉じていない場合
    if in_table:
        flush_table()

    return flowables


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(JP, 7.5)
    canvas.setFillColor(TEXT_GRAY)
    page_num = canvas.getPageNumber()
    # フッター
    canvas.drawString(20 * mm, 11 * mm, "Digital Memorial — 要件定義書 v1.0")
    canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"- {page_num} -")
    # フッター上の区切り線
    canvas.setStrokeColor(GRAY_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    canvas.restoreState()


def generate_pdf(md_path, pdf_path):
    styles = build_styles()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title="Digital Memorial 要件定義書",
        author="Digital Memorial",
        subject="終活サービス要件定義書",
    )

    flowables = parse_markdown(md_path, styles)
    doc.build(flowables,
              onFirstPage=add_header_footer,
              onLaterPages=add_header_footer)
    print(f"PDF生成完了: {pdf_path}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    generate_pdf("REQUIREMENTS.md", "REQUIREMENTS.pdf")
    os.system("open REQUIREMENTS.pdf")
