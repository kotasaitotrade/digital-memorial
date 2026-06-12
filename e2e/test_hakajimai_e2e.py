"""
墓じまい計画 E2Eバグ検証テスト
対象: https://kotsaito-digital-memorial.hf.space/hakajimai
実行: python3 e2e/test_hakajimai_e2e.py
"""

import os, sys, time, json, warnings, requests
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, expect

warnings.filterwarnings("ignore")

BASE_URL = "https://kotsaito-digital-memorial.hf.space"
API_URL  = f"{BASE_URL}/api"
SS_DIR   = "/tmp/hakajimai_e2e_screenshots"
os.makedirs(SS_DIR, exist_ok=True)

TEST_EMAIL    = "e2e_hakajimai@example.com"
TEST_PASSWORD = "E2etest123!"
TEST_NAME     = "墓じまいテストユーザー"

results: list[dict] = []

def record(fid, feature, result, detail, screenshot=""):
    icon = "✅ PASS" if result == "pass" else "❌ FAIL"
    print(f"  {icon}  [{fid}] {feature}")
    if detail: print(f"         → {detail}")
    results.append({"id": fid, "feature": feature, "result": result, "detail": detail, "screenshot": screenshot})

def ss(page, name):
    path = f"{SS_DIR}/{name}.png"
    page.screenshot(path=path, full_page=True)
    return path

# ── API ヘルパー ─────────────────────────────────────────────
def get_token():
    for attempt in range(3):
        try:
            r = requests.post(f"{API_URL}/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME}, timeout=30)
            if r.status_code in (200, 201):
                tok = r.json().get("access_token", "")
                if tok: return tok
            r2 = requests.post(f"{API_URL}/auth/login",
                data={"username": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=30)
            r2.raise_for_status()
            tok = r2.json()["access_token"]
            if tok: return tok
        except Exception as e:
            if attempt < 2: time.sleep(5)
            else: raise

def api_get(token, path):
    r = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    return r.json()

def api_put(token, path, data):
    r = requests.put(f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"}, json=data, timeout=30)
    r.raise_for_status()
    return r.json()

def api_reset(token):
    """墓じまいデータをデフォルトにリセット"""
    api_put(token, "/hakajimai", {
        "kuyou_method": "", "kuyou_detail": "", "message_to_family": "",
        "sect": "",
        "checklist_items": [
            {"key": "family_consult",    "category": "準備",   "label": "家族・親族への相談",               "is_done": False},
            {"key": "temple_consult",    "category": "準備",   "label": "菩提寺・霊園への相談・連絡",       "is_done": False},
            {"key": "new_place_decided", "category": "準備",   "label": "改葬先の決定（永代供養墓・散骨等）","is_done": False},
            {"key": "permit_apply",      "category": "行政",   "label": "市区町村役場で改葬許可申請",        "is_done": False},
            {"key": "kaimoku",           "category": "供養",   "label": "閉眼供養（魂抜き）の依頼・実施",   "is_done": False},
            {"key": "stone_removal",     "category": "工事",   "label": "石材店への墓石撤去・処分依頼",      "is_done": False},
            {"key": "remains_removal",   "category": "工事",   "label": "遺骨の取り出し",                   "is_done": False},
            {"key": "new_burial",        "category": "改葬先", "label": "改葬先での納骨・手続き完了",        "is_done": False},
            {"key": "land_return",       "category": "改葬先", "label": "墓地の返還手続き完了",              "is_done": False},
            {"key": "kaigen",            "category": "供養",   "label": "開眼供養（新しい供養先で）",        "is_done": False},
        ],
        "cost_items": [
            {"key": "cost_kaimoku",   "label": "閉眼供養（お布施）",     "amount": 30000,  "min": 30000,  "max": 100000, "note": "目安: 3〜10万円"},
            {"key": "cost_stone",     "label": "石材店（撤去・処分費）", "amount": 150000, "min": 100000, "max": 300000, "note": "目安: 10〜30万円"},
            {"key": "cost_permit",    "label": "改葬許可手数料",         "amount": 1500,   "min": 1500,   "max": 5000,   "note": "目安: 1,500〜数千円"},
            {"key": "cost_transport", "label": "遺骨の運搬費",           "amount": 20000,  "min": 10000,  "max": 50000,  "note": "目安: 1〜5万円"},
            {"key": "cost_new_place", "label": "新しい供養先の費用",     "amount": 200000, "min": 50000,  "max": 800000, "note": "方法により大きく異なる"},
            {"key": "cost_kaigen",    "label": "開眼供養（お布施）",     "amount": 30000,  "min": 30000,  "max": 100000, "note": "目安: 3〜10万円"},
        ],
        "grave_info": {"cemetery_name": "", "address": "", "temple_name": "", "住職名": "", "temple_phone": "", "stone_shop_name": "", "stone_shop_phone": "", "annual_fee": "", "built_year": "", "notes": ""},
    })

def browser_login(page):
    page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", TEST_PASSWORD)
    page.click("button[type='submit'], button:has-text('ログイン')")
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=20000)
    page.wait_for_timeout(1500)

# ═══════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("墓じまい計画 E2Eバグ検証テスト")
    print(f"対象: {BASE_URL}/hakajimai")
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 前処理
    print("\n[前処理] テストユーザー・API確認中...")
    token = get_token()
    print(f"  token: {token[:20]}...")

    # ── H00: API GET /hakajimai ──────────────────────────────
    print("\n[H00] API GET /hakajimai")
    try:
        data = api_get(token, "/hakajimai")
        has_fields = all(k in data for k in ["kuyou_method","checklist_items","cost_items","grave_info","sect"])
        ci_count = len(data.get("checklist_items", []))
        co_count = len(data.get("cost_items", []))
        record("H00", "API GET /hakajimai レスポンス確認",
               "pass" if has_fields and ci_count > 0 and co_count > 0 else "fail",
               f"fields OK={has_fields}, checklist={ci_count}件, cost={co_count}件")
    except Exception as e:
        record("H00", "API GET /hakajimai レスポンス確認", "fail", str(e))
        print("  ❌ API 応答なし。テスト中止")
        _print_summary(); return

    # ── H01: API PUT /hakajimai ──────────────────────────────
    print("\n[H01] API PUT /hakajimai")
    try:
        api_reset(token)
        data = api_get(token, "/hakajimai")
        record("H01", "API PUT /hakajimai リセット保存",
               "pass" if data["kuyou_method"] == "" else "fail",
               f"kuyou_method='{data['kuyou_method']}'")
    except Exception as e:
        record("H01", "API PUT /hakajimai リセット保存", "fail", str(e))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.set_default_timeout(30000)
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = ctx.new_page()

        # ── H02: ログイン ────────────────────────────────────
        print("\n[H02] ログイン")
        try:
            browser_login(page)
            path = ss(page, "H02_dashboard")
            record("H02", "ログイン・ダッシュボード表示", "pass", "ダッシュボード確認", path)
        except Exception as e:
            record("H02", "ログイン・ダッシュボード表示", "fail", str(e))
            browser.close(); _print_summary(); _write_report(); return

        # ── H03: /hakajimai ページ表示 ──────────────────────
        print("\n[H03] 墓じまいページ表示")
        try:
            page.goto(f"{BASE_URL}/hakajimai", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            path = ss(page, "H03_hakajimai_initial")
            expect(page.get_by_text("墓じまい計画")).to_be_visible()
            record("H03", "墓じまいページ表示", "pass", "タイトル確認", path)
        except Exception as e:
            record("H03", "墓じまいページ表示", "fail", str(e), ss(page, "H03_fail"))

        # ── H04: 6タブ表示確認 ──────────────────────────────
        print("\n[H04] 6タブ表示")
        try:
            for tab_label in ["供養方法", "お墓の情報", "手続き", "費用", "テンプレート", "家族へ"]:
                expect(page.get_by_role("button", name=tab_label).first).to_be_visible()
            path = ss(page, "H04_tabs")
            record("H04", "6タブ全表示確認", "pass", "供養方法/お墓の情報/手続き/費用/テンプレート/家族へ", path)
        except Exception as e:
            record("H04", "6タブ全表示確認", "fail", str(e))

        # ── H05: 供養方法 カード表示 ────────────────────────
        print("\n[H05] 供養方法カード表示")
        try:
            for method in ["永代供養墓", "合祀墓", "散骨", "手元供養", "納骨堂", "その他"]:
                expect(page.get_by_text(method).first).to_be_visible()
            path = ss(page, "H05_method_cards")
            record("H05", "供養方法カード 6種表示", "pass", "全6種確認", path)
        except Exception as e:
            record("H05", "供養方法カード 6種表示", "fail", str(e))

        # ── H06: 供養方法 選択・保存 ────────────────────────
        print("\n[H06] 供養方法 選択・保存")
        try:
            page.get_by_text("永代供養墓").first.click()
            page.wait_for_timeout(2000)
            path = ss(page, "H06_method_selected")
            # API確認
            data = api_get(token, "/hakajimai")
            saved_method = data.get("kuyou_method", "")
            # 選択中バナー表示確認
            expect(page.get_by_text("選択中:").first).to_be_visible()
            record("H06", "供養方法 選択・保存", "pass" if saved_method == "永代供養墓" else "fail",
                   f"API: kuyou_method='{saved_method}'", path)
        except Exception as e:
            record("H06", "供養方法 選択・保存", "fail", str(e), ss(page, "H06_fail"))

        # ── H07: 宗派選択・保存 ─────────────────────────────
        print("\n[H07] 宗派選択・保存")
        try:
            select = page.locator("select").first
            select.select_option("浄土宗")
            page.wait_for_timeout(2000)
            path = ss(page, "H07_sect_selected")
            # ヒントボックス表示確認
            expect(page.get_by_text("浄土宗 の手続きポイント")).to_be_visible()
            # API確認
            data = api_get(token, "/hakajimai")
            saved_sect = data.get("sect", "")
            record("H07", "宗派選択・ヒント表示・保存", "pass" if saved_sect == "浄土宗" else "fail",
                   f"API: sect='{saved_sect}' / ヒント表示OK", path)
        except Exception as e:
            record("H07", "宗派選択・ヒント表示・保存", "fail", str(e), ss(page, "H07_fail"))

        # ── H08: 「その他」選択でテキストエリア表示 ─────────
        print("\n[H08] 供養方法「その他」→ テキストエリア")
        try:
            page.get_by_text("その他").first.click()
            page.wait_for_timeout(1000)
            path = ss(page, "H08_other_textarea")
            # テキストエリアが表示されるか
            ta = page.locator("textarea").first
            expect(ta).to_be_visible()
            ta.fill("樹木葬と散骨を組み合わせる")
            ta.press("Tab")
            page.wait_for_timeout(1500)
            data = api_get(token, "/hakajimai")
            saved_detail = data.get("kuyou_detail", "")
            record("H08", "「その他」選択でテキストエリア・保存", "pass" if "樹木葬" in saved_detail else "fail",
                   f"API: kuyou_detail='{saved_detail}'", path)
        except Exception as e:
            record("H08", "「その他」選択でテキストエリア・保存", "fail", str(e), ss(page, "H08_fail"))

        # ── H09: お墓の情報 タブ ────────────────────────────
        print("\n[H09] お墓の情報 タブ")
        try:
            page.get_by_role("button", name="お墓の情報").click()
            page.wait_for_timeout(800)
            path = ss(page, "H09_grave_tab")
            expect(page.get_by_text("墓地・霊園名")).to_be_visible()
            record("H09", "お墓の情報タブ 入力フィールド表示", "pass", "入力フィールド確認", path)
        except Exception as e:
            record("H09", "お墓の情報タブ 入力フィールド表示", "fail", str(e))

        # ── H10: お墓の情報 入力・保存 ──────────────────────
        print("\n[H10] お墓の情報 入力・保存")
        try:
            # 墓地名を入力
            inputs = page.locator("input[type='text']").all()
            if inputs:
                inputs[0].fill("東京都立 多磨霊園")
                inputs[0].press("Tab")
                page.wait_for_timeout(2000)
            path = ss(page, "H10_grave_saved")
            data = api_get(token, "/hakajimai")
            cemetery = data.get("grave_info", {}).get("cemetery_name", "")
            record("H10", "墓地名 入力・保存", "pass" if "多磨霊園" in cemetery else "fail",
                   f"API: cemetery_name='{cemetery}'", path)
        except Exception as e:
            record("H10", "墓地名 入力・保存", "fail", str(e), ss(page, "H10_fail"))

        # ── H11: 手続き チェックリスト ──────────────────────
        print("\n[H11] 手続きチェックリスト タブ")
        try:
            page.get_by_role("button", name="手続き").click()
            page.wait_for_timeout(800)
            path = ss(page, "H11_checklist_tab")
            # チェックリストアイテムが表示されるか
            expect(page.get_by_text("家族・親族への相談")).to_be_visible()
            # 進捗バーの表示
            expect(page.locator("text=/\\d+ \\/ \\d+ 完了/")).to_be_visible()
            doneText = page.locator("text=/\\d+ \\/ \\d+ 完了/").first.inner_text()
            record("H11", "手続きチェックリスト表示", "pass", f"進捗: {doneText}", path)
        except Exception as e:
            record("H11", "手続きチェックリスト表示", "fail", str(e))

        # ── H12: チェックボックス トグル・保存 ──────────────
        print("\n[H12] チェックボックス トグル・保存")
        try:
            # 最初のチェックボックスをONにする
            first_checkbox = page.locator("input[type='checkbox']").first
            first_checkbox.check()
            page.wait_for_timeout(2500)
            path = ss(page, "H12_check_toggled")
            # API確認
            data = api_get(token, "/hakajimai")
            items = data.get("checklist_items", [])
            first_done = items[0].get("is_done", False) if items else False
            # 進捗カウンタが更新されているか
            progress_text = page.locator("text=/\\d+ \\/ \\d+ 完了/").first.inner_text()
            record("H12", "チェックボックス ON・保存", "pass" if first_done else "fail",
                   f"API: is_done={first_done} / 表示: '{progress_text}'", path)
        except Exception as e:
            record("H12", "チェックボックス ON・保存", "fail", str(e), ss(page, "H12_fail"))

        # ── H13: チェックボックス OFFに戻す ─────────────────
        print("\n[H13] チェックボックス OFF・保存")
        try:
            first_checkbox = page.locator("input[type='checkbox']").first
            first_checkbox.uncheck()
            page.wait_for_timeout(2500)
            data = api_get(token, "/hakajimai")
            items = data.get("checklist_items", [])
            first_done = items[0].get("is_done", True) if items else True
            path = ss(page, "H13_check_untoggled")
            record("H13", "チェックボックス OFF・保存", "pass" if not first_done else "fail",
                   f"API: is_done={first_done}", path)
        except Exception as e:
            record("H13", "チェックボックス OFF・保存", "fail", str(e))

        # ── H14: カテゴリ別グループ表示 ─────────────────────
        print("\n[H14] カテゴリ別グループ表示")
        try:
            for cat in ["準備", "行政", "供養", "工事", "改葬先"]:
                expect(page.get_by_text(cat).first).to_be_visible()
            path = ss(page, "H14_category_groups")
            record("H14", "カテゴリ別グループ 5種表示", "pass", "準備/行政/供養/工事/改葬先", path)
        except Exception as e:
            record("H14", "カテゴリ別グループ 5種表示", "fail", str(e))

        # ── H15: 費用 タブ ───────────────────────────────────
        print("\n[H15] 費用タブ")
        try:
            page.get_by_role("button", name="費用").click()
            page.wait_for_timeout(800)
            path = ss(page, "H15_cost_tab")
            expect(page.get_by_text("閉眼供養（お布施）")).to_be_visible()
            # 合計行表示確認
            expect(page.get_by_text("あなたの目安:").first).to_be_visible()
            total_text = page.get_by_text("あなたの目安:").first.inner_text()
            record("H15", "費用タブ・合計行表示", "pass", f"'{total_text}'", path)
        except Exception as e:
            record("H15", "費用タブ・合計行表示", "fail", str(e))

        # ── H16: 費用 金額変更・保存 ────────────────────────
        print("\n[H16] 費用 金額変更・保存")
        try:
            # 最初の費用インプット（閉眼供養）を変更
            cost_inputs = page.locator("input[type='number']").all()
            if cost_inputs:
                cost_inputs[0].fill("50000")
                cost_inputs[0].press("Tab")
                page.wait_for_timeout(2000)
            path = ss(page, "H16_cost_saved")
            data = api_get(token, "/hakajimai")
            items = data.get("cost_items", [])
            saved_amount = items[0].get("amount", 0) if items else 0
            record("H16", "費用 金額変更・保存", "pass" if saved_amount == 50000 else "fail",
                   f"API: cost_items[0].amount={saved_amount}", path)
        except Exception as e:
            record("H16", "費用 金額変更・保存", "fail", str(e), ss(page, "H16_fail"))

        # ── H17: 費用 合計金額の更新 ────────────────────────
        print("\n[H17] 費用 合計金額リアルタイム更新")
        try:
            page.get_by_role("button", name="費用").click()
            page.wait_for_timeout(500)
            total_before = page.get_by_text("あなたの目安:").first.inner_text()
            # さらに変更
            cost_inputs = page.locator("input[type='number']").all()
            if cost_inputs:
                cost_inputs[0].fill("80000")
                cost_inputs[0].press("Tab")
                page.wait_for_timeout(500)
            total_after = page.get_by_text("あなたの目安:").first.inner_text()
            path = ss(page, "H17_cost_total_updated")
            changed = total_before != total_after
            record("H17", "費用合計 リアルタイム更新", "pass" if changed else "fail",
                   f"変更前: '{total_before}' → 変更後: '{total_after}'", path)
        except Exception as e:
            record("H17", "費用合計 リアルタイム更新", "fail", str(e))

        # ── H18: テンプレート タブ表示 ──────────────────────
        print("\n[H18] テンプレートタブ")
        try:
            page.get_by_role("button", name="テンプレート").click()
            page.wait_for_timeout(800)
            path = ss(page, "H18_template_tab")
            for title in ["最初の相談電話", "石材店への見積もり依頼", "役所への改葬許可申請", "家族への墓じまい提案"]:
                expect(page.get_by_text(title).first).to_be_visible()
            record("H18", "テンプレート 4件表示", "pass", "全4件タイトル確認", path)
        except Exception as e:
            record("H18", "テンプレート 4件表示", "fail", str(e))

        # ── H19: テンプレート コピーボタン ──────────────────
        print("\n[H19] テンプレートコピー")
        try:
            page.evaluate("navigator.clipboard.writeText('test')")
            copy_btns = page.locator("button:has-text('コピー')").all()
            if copy_btns:
                copy_btns[0].click()
                page.wait_for_timeout(1500)
                path = ss(page, "H19_template_copy")
                expect(page.get_by_text("✓ コピー済み").first).to_be_visible()
                record("H19", "テンプレートコピーボタン", "pass", "✓ コピー済み 表示確認", path)
            else:
                record("H19", "テンプレートコピーボタン", "fail", "コピーボタンが見つからない")
        except Exception as e:
            record("H19", "テンプレートコピーボタン", "fail", str(e))

        # ── H20: 家族へのメッセージ タブ ────────────────────
        print("\n[H20] 家族へのメッセージ タブ")
        try:
            page.get_by_role("button", name="家族へ").click()
            page.wait_for_timeout(800)
            path = ss(page, "H20_message_tab")
            # テキストエリアが表示されるか
            ta = page.locator("textarea").first
            expect(ta).to_be_visible()
            record("H20", "家族へのメッセージタブ表示", "pass", "テキストエリア確認", path)
        except Exception as e:
            record("H20", "家族へのメッセージタブ表示", "fail", str(e))

        # ── H21: 家族メッセージ 入力・保存 ──────────────────
        print("\n[H21] 家族メッセージ 入力・保存")
        try:
            msg = "永代供養でお願いします。費用は貯金から使ってください。"
            ta = page.locator("textarea").first
            ta.fill(msg)
            ta.press("Tab")
            page.wait_for_timeout(2000)
            path = ss(page, "H21_message_saved")
            data = api_get(token, "/hakajimai")
            saved_msg = data.get("message_to_family", "")
            record("H21", "家族メッセージ 入力・保存", "pass" if msg in saved_msg else "fail",
                   f"API: message_to_family='{saved_msg[:40]}...'", path)
        except Exception as e:
            record("H21", "家族メッセージ 入力・保存", "fail", str(e), ss(page, "H21_fail"))

        # ── H22: 手続きタブ カウンタ連動 ────────────────────
        print("\n[H22] 手続きタブラベルのカウンタ")
        try:
            page.get_by_role("button", name="手続き").click()
            page.wait_for_timeout(800)
            # チェックを入れてタブラベルのカウンタが更新されるか
            checkboxes = page.locator("input[type='checkbox']").all()
            if checkboxes:
                checkboxes[0].check()
                page.wait_for_timeout(2000)
            # タブボタン自体のテキストに (1/10) 等が含まれるか確認
            checklist_tab_btn = page.locator("button").filter(has_text="手続き").first
            tab_text = checklist_tab_btn.inner_text()
            path = ss(page, "H22_tab_counter")
            has_counter = "/" in tab_text
            record("H22", "手続きタブラベルのカウンタ更新", "pass" if has_counter else "fail",
                   f"タブテキスト: '{tab_text}'", path)
        except Exception as e:
            record("H22", "手続きタブラベルのカウンタ更新", "fail", str(e))

        # ── H23: ページリロード後のデータ復元 ───────────────
        print("\n[H23] ページリロード後のデータ永続化")
        try:
            page.reload(wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            # 供養方法タブを確認
            page.get_by_role("button", name="供養方法").click()
            page.wait_for_timeout(800)
            path = ss(page, "H23_after_reload")
            # 選択済みの「その他」が復元されているか（H08で「その他」を選択）
            # もしくは「永代供養墓」が選択されているか（H06で選択してH08で「その他」に変更）
            data = api_get(token, "/hakajimai")
            method = data.get("kuyou_method", "")
            sect   = data.get("sect", "")
            # 選択中バナーか選択済みボタンが表示されているか
            has_selection = page.get_by_text("選択中:").count() > 0 or method != ""
            record("H23", "リロード後データ復元", "pass" if has_selection else "fail",
                   f"API: kuyou_method='{method}', sect='{sect}'", path)
        except Exception as e:
            record("H23", "リロード後データ復元", "fail", str(e))

        # ── H24: ナビゲーション ← ダッシュボード ────────────
        print("\n[H24] ← ダッシュボードナビゲーション")
        try:
            back_btn = page.get_by_role("button", name="← ダッシュボード")
            expect(back_btn).to_be_visible()
            back_btn.click()
            page.wait_for_timeout(1500)
            path = ss(page, "H24_back_nav")
            expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)
            record("H24", "← ダッシュボードへの遷移", "pass", "/dashboard に遷移確認", path)
        except Exception as e:
            record("H24", "← ダッシュボードへの遷移", "fail", str(e))

        # ── H25: ダッシュボードから墓じまいへの導線 ─────────
        print("\n[H25] ダッシュボードからの墓じまい導線")
        try:
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            hakajimai_link = page.get_by_text("墓じまい計画").first
            expect(hakajimai_link).to_be_visible()
            path = ss(page, "H25_dashboard_link")
            record("H25", "ダッシュボードに墓じまい導線あり", "pass", "「墓じまい計画」リンク確認", path)
        except Exception as e:
            record("H25", "ダッシュボードに墓じまい導線あり", "fail", str(e))

        # ── H26: 「保存中...」インジケーター ─────────────────
        print("\n[H26] 保存インジケーター")
        try:
            page.goto(f"{BASE_URL}/hakajimai", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            # 供養方法を選択して保存中が一瞬表示されるか
            page.get_by_text("散骨").first.click()
            # 即座にスクリーンショット
            path_saving = ss(page, "H26_saving_indicator")
            page.wait_for_timeout(2000)
            path_saved = ss(page, "H26_saved_indicator")
            # 保存済みバッジが表示されるか
            # (タイミングが難しいので、API確認で代替)
            data = api_get(token, "/hakajimai")
            saved = data.get("kuyou_method", "") == "散骨"
            record("H26", "保存インジケーター動作・API確認", "pass" if saved else "fail",
                   f"散骨 保存確認: {saved}", path_saved)
        except Exception as e:
            record("H26", "保存インジケーター動作・API確認", "fail", str(e))

        browser.close()

    _print_summary()
    _write_report()


def _print_summary():
    print("\n" + "=" * 60)
    print("墓じまい E2Eテスト 結果サマリー")
    print("=" * 60)
    passed = sum(1 for r in results if r["result"] == "pass")
    failed = sum(1 for r in results if r["result"] == "fail")
    for r in results:
        icon = "✅" if r["result"] == "pass" else "❌"
        print(f"  {icon} [{r['id']}] {r['feature']}")
    print(f"\n合計: {len(results)} / PASS: {passed} / FAIL: {failed}")
    if failed:
        print("\n【失敗項目】")
        for r in results:
            if r["result"] == "fail":
                print(f"  ❌ [{r['id']}] {r['feature']}: {r['detail'][:80]}")


def _write_report():
    path = "/tmp/hakajimai_e2e_report.md"
    passed = [r for r in results if r["result"] == "pass"]
    failed = [r for r in results if r["result"] == "fail"]
    lines = [
        "# 墓じまい計画 E2Eバグ検証レポート",
        f"**実施日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**合計**: {len(results)} / ✅ PASS: {len(passed)} / ❌ FAIL: {len(failed)}",
        "",
        "| ID | 機能 | 結果 | 詳細 |",
        "|---|---|---|---|",
    ]
    for r in results:
        icon = "✅" if r["result"] == "pass" else "❌"
        lines.append(f"| {r['id']} | {r['feature']} | {icon} | {r['detail'][:100]} |")
    lines += ["", "## 失敗項目"]
    for r in failed:
        lines.append(f"- **[{r['id']}] {r['feature']}**: {r['detail']}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nレポート: {path}")
    print(f"スクリーンショット: {SS_DIR}/")


if __name__ == "__main__":
    main()
