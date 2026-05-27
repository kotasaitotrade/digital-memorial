#!/usr/bin/env python3
"""
REQUIREMENTS.md → HTML → PDF 変換スクリプト
Usage: python3 convert_to_pdf.py
"""
import subprocess
import sys
import os

MD_FILE = "REQUIREMENTS.md"
HTML_FILE = "REQUIREMENTS.html"
PDF_FILE = "REQUIREMENTS.pdf"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

* { box-sizing: border-box; }

body {
    font-family: 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
    font-size: 10pt;
    line-height: 1.8;
    color: #1a1a1a;
    max-width: 210mm;
    margin: 0 auto;
    padding: 15mm 20mm;
}

h1 {
    font-size: 20pt;
    color: #1a5c38;
    border-bottom: 3px solid #1a5c38;
    padding-bottom: 8px;
    margin-top: 0;
}

h2 {
    font-size: 14pt;
    color: #1a5c38;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 6px;
    margin-top: 30px;
}

h3 {
    font-size: 12pt;
    color: #2d7a4f;
    border-left: 4px solid #2d7a4f;
    padding-left: 10px;
    margin-top: 20px;
}

h4 {
    font-size: 10pt;
    color: #333;
    margin-top: 15px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9pt;
}

th {
    background-color: #1a5c38;
    color: white;
    padding: 6px 8px;
    text-align: left;
}

td {
    padding: 5px 8px;
    border: 1px solid #ddd;
}

tr:nth-child(even) td {
    background-color: #f7f7f7;
}

code, pre {
    font-family: 'Courier New', Courier, monospace;
    font-size: 8.5pt;
    background-color: #f4f4f4;
    padding: 2px 5px;
    border-radius: 3px;
}

pre {
    padding: 12px;
    overflow-x: auto;
    border-left: 3px solid #1a5c38;
    line-height: 1.5;
}

pre code {
    background: none;
    padding: 0;
}

blockquote {
    margin: 10px 0;
    padding: 10px 15px;
    background: #f0f7f4;
    border-left: 4px solid #1a5c38;
    color: #333;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 20px 0;
}

.cover {
    text-align: center;
    padding: 50mm 0 30mm;
}

@media print {
    body { padding: 0; }
    h2 { page-break-before: auto; }
    table { page-break-inside: avoid; }
}
"""


def convert_md_to_html(md_path, html_path):
    try:
        import markdown
        with open(md_path, encoding="utf-8") as f:
            md_content = f.read()

        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc"]
        )

        html_full = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Digital Memorial 要件定義書</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_full)

        print(f"HTML生成完了: {html_path}")
        return True
    except ImportError:
        print("markdown パッケージが見つかりません: pip3 install markdown")
        return False


def convert_html_to_pdf_weasyprint(html_path, pdf_path):
    try:
        import weasyprint
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        print(f"PDF生成完了 (weasyprint): {pdf_path}")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"weasyprint エラー: {e}")
        return False


def convert_with_pandoc(md_path, pdf_path):
    result = subprocess.run(
        ["pandoc", md_path, "-o", pdf_path,
         "--pdf-engine=xelatex",
         "-V", "mainfont=Hiragino Sans",
         "-V", "geometry:margin=25mm",
         "-V", "fontsize=10pt",
         "--toc"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"PDF生成完了 (pandoc): {pdf_path}")
        return True
    else:
        print(f"pandoc エラー: {result.stderr}")
        return False


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=== REQUIREMENTS.md → PDF 変換 ===")

    # Step 1: Markdown → HTML
    if not convert_md_to_html(MD_FILE, HTML_FILE):
        print("HTMLへの変換に失敗しました")
        sys.exit(1)

    # Step 2: HTML → PDF (weasyprint優先、次にpandoc)
    if convert_html_to_pdf_weasyprint(HTML_FILE, PDF_FILE):
        print(f"\n完了！ {PDF_FILE} を確認してください。")
        subprocess.run(["open", PDF_FILE])
    elif convert_with_pandoc(MD_FILE, PDF_FILE):
        print(f"\n完了！ {PDF_FILE} を確認してください。")
        subprocess.run(["open", PDF_FILE])
    else:
        print(f"\nPDF変換ツールが見つかりませんでした。")
        print(f"代わりに HTML ファイルを Safari で開いてPDF印刷してください:")
        print(f"  open {HTML_FILE}")
        subprocess.run(["open", HTML_FILE])


if __name__ == "__main__":
    main()
