"""
サンプルPDF生成スクリプト
PDF出力対象ページ（相続計算結果・エンディングノート・遺言書シミュレーター）を
Playwright の page.pdf() で生成し docs/samples/ に保存する。
実行方法: cd /Users/user01/digital-memorial && python3 docs/generate_sample_pdfs.py
"""
import os, sys, time, requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
API_URL  = "http://localhost:8000/api"
OUT_DIR  = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)

EMAIL = "pdf_sample@example.com"
NAME  = "山田 花子"
PW    = "samplepdf123"

PDF_OPTIONS = {
    "format": "A4",
    "print_background": True,
    "margin": {"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
}

def api_register_or_login(email, name, pw):
    # 登録試行（既存ユーザーなら400が返るが無視して続行）
    requests.post(f"{API_URL}/auth/register",
                  json={"email": email, "name": name, "password": pw}, timeout=5)
    # 常にloginでトークン取得（registerレスポンスにはtokenが含まれないため）
    res = requests.post(f"{API_URL}/auth/login",
                        data={"username": email, "password": pw}, timeout=5)
    return res.json().get("access_token", "") if res.status_code == 200 else ""

def setup_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    # 相続計画作成
    res = requests.post(f"{API_URL}/estate-plans",
                        json={"title": "山田家 相続計画（サンプル）", "total_assets": 50000000,
                              "total_debts": 5000000, "description": "PDF出力サンプル用"},
                        headers=headers, timeout=5)
    plan_id = res.json().get("id") if res.status_code == 200 else None

    if plan_id:
        # 家族構成追加
        members = [
            {"name": "山田 太郎", "relationship": "配偶者", "is_alive": True,
             "is_disqualified": False, "has_renounced": False, "is_adopted": False,
             "is_half_blood": False},
            {"name": "山田 一郎", "relationship": "長男", "is_alive": True,
             "is_disqualified": False, "has_renounced": False, "is_adopted": False,
             "is_half_blood": False},
            {"name": "山田 二郎", "relationship": "次男", "is_alive": True,
             "is_disqualified": False, "has_renounced": False, "is_adopted": False,
             "is_half_blood": False},
        ]
        for m in members:
            requests.post(f"{API_URL}/estate-plans/{plan_id}/family",
                          json=m, headers=headers, timeout=5)
    return plan_id

def browser_login(page, email, pw):
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[type='email']", email)
    page.fill("input[type='password']", pw)
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
    try:
        page.evaluate("localStorage.setItem('dm_onboarding_done', '1')")
        close = page.locator("button:has-text('✕'), button:has-text('始める')")
        if close.first.is_visible(timeout=1500):
            close.first.click()
    except Exception:
        pass

def main():
    print("=" * 60)
    print("  📄 サンプルPDF生成")
    print("=" * 60)

    token = api_register_or_login(EMAIL, NAME, PW)
    if not token:
        print("  ❌ 認証失敗")
        sys.exit(1)
    print(f"  ✅ 認証OK")

    plan_id = setup_data(token)
    if not plan_id:
        print("  ❌ 相続計画作成失敗")
        sys.exit(1)
    print(f"  ✅ テストデータ作成完了 (plan_id={plan_id})")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        browser_login(page, EMAIL, PW)

        # ── 1. 相続計算結果 ──────────────────────────────
        print("  📄 相続計算結果PDF生成中...")
        page.goto(f"{BASE_URL}/estate/{plan_id}/result")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        out = os.path.join(OUT_DIR, "sample_estate_result.pdf")
        page.pdf(path=out, **PDF_OPTIONS)
        print(f"  ✅ {os.path.basename(out)} ({os.path.getsize(out)//1024} KB)")

        # ── 2. エンディングノート ─────────────────────────
        print("  📄 エンディングノートPDF生成中...")
        # 各タブにデータを入力してから印刷ビューをキャプチャ
        page.goto(f"{BASE_URL}/ending-note")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # 医療タブ入力
        ta = page.locator("textarea").first
        if ta.count() > 0:
            ta.fill("延命治療は希望しません。自然な形での最期を望んでいます。")
            page.wait_for_timeout(1500)
        # 家族へのメッセージタブ
        try:
            page.click("button:has-text('家族へ'), [role='tab']:has-text('家族')")
            page.wait_for_timeout(500)
            msg = page.locator("textarea").first
            if msg.count() > 0:
                msg.fill("いつも支えてくれてありがとう。みんなのことをいつも想っています。")
                page.wait_for_timeout(1500)
        except Exception:
            pass
        out = os.path.join(OUT_DIR, "sample_ending_note.pdf")
        page.pdf(path=out, **PDF_OPTIONS)
        print(f"  ✅ {os.path.basename(out)} ({os.path.getsize(out)//1024} KB)")

        # ── 3. 遺言書シミュレーター ──────────────────────
        print("  📄 遺言書シミュレーターPDF生成中...")
        page.goto(f"{BASE_URL}/estate/{plan_id}/will")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        # 配分入力
        inputs = page.locator("input[type='number']").all()
        # 相続財産 = 50000000 - 5000000 = 45000000
        # 配偶者 1/2 = 22500000, 子各 1/4 = 11250000
        allocations = [22500000, 12000000, 10500000]
        for i, inp in enumerate(inputs[:3]):
            inp.fill(str(allocations[i]))
            page.wait_for_timeout(200)
        # メモ入力
        memo_area = page.locator("textarea").first
        if memo_area.count() > 0:
            memo_area.fill("妻の老後の生活を最優先に考え、子どもたちには等しく感謝の気持ちを込めて配分しました。")
            page.wait_for_timeout(1500)
        out = os.path.join(OUT_DIR, "sample_will_simulator.pdf")
        page.pdf(path=out, **PDF_OPTIONS)
        print(f"  ✅ {os.path.basename(out)} ({os.path.getsize(out)//1024} KB)")

        browser.close()

    print()
    print(f"  📁 出力先: {OUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
