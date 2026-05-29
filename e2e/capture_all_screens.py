"""
全画面スクリーンショット取得スクリプト（仕様書用）
全17画面を余すことなく、複数のUI状態を含めて撮影する
実行方法: cd /Users/user01/digital-memorial && python3 e2e/capture_all_screens.py
"""
import os, time, json
import requests
from playwright.sync_api import sync_playwright, Page

BASE_URL = "http://localhost:5173"
API_URL  = "http://localhost:8000/api"
SS_DIR   = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SS_DIR, exist_ok=True)

_TS           = int(time.time())
TEST_EMAIL    = f"spec_{_TS}@example.com"
TEST_PASSWORD = "spectest123"
TEST_NAME     = "佐藤 恵子"

def ss(page: Page, name: str, full: bool = True):
    path = os.path.join(SS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  📸 {name}.png")

def api_post(path: str, data: dict, token: str = "") -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    res = requests.post(f"{API_URL}{path}", json=data, headers=headers)
    return res.json()

def api_get(path: str, token: str) -> dict:
    res = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"})
    return res.json()

def api_token() -> str:
    requests.post(f"{API_URL}/auth/register",
        json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    res = requests.post(f"{API_URL}/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    return res.json().get("access_token", "")

def login_ui(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.locator("input[type='email']").fill(TEST_EMAIL)
    page.locator("input[type='password']").fill(TEST_PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=8000)
    page.wait_for_load_state("networkidle")

def dismiss_onboarding(page: Page):
    try:
        page.evaluate("localStorage.setItem('dm_onboarding_done', '1')")
        close = page.locator("button:has-text('✕'), button:has-text('始める →')")
        if close.first.is_visible(timeout=1000):
            close.first.click()
    except Exception:
        pass

def ensure_login(page: Page):
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1200)
    if "/login" in page.url:
        login_ui(page)
    dismiss_onboarding(page)

def wait(page: Page, ms: int = 800):
    page.wait_for_timeout(ms)

# ═══════════════════════════════════════════════════════════════
# S01: ログイン画面  → login_*.png
# ═══════════════════════════════════════════════════════════════
def capture_login(page: Page):
    print("\n[S01] ログイン画面")
    # ログアウト状態にしてからアクセス
    page.evaluate("localStorage.removeItem('token')")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "login_01_empty")

    # フォーム入力済み状態
    try:
        page.locator("input[type='email']").fill(TEST_EMAIL)
        page.locator("input[type='password']").fill(TEST_PASSWORD)
        wait(page)
        ss(page, "login_02_filled")
    except Exception as e:
        print(f"    ⚠ login_02: {e}")

    # エラー表示
    try:
        page.locator("input[type='email']").fill("wrong@example.com")
        page.locator("input[type='password']").fill("badpass")
        page.locator("button[type='submit']").click()
        wait(page, 1800)
        ss(page, "login_03_error")
    except Exception as e:
        print(f"    ⚠ login_03: {e}")

# ═══════════════════════════════════════════════════════════════
# S02: 新規登録画面  → register_*.png
# ═══════════════════════════════════════════════════════════════
def capture_register(page: Page):
    print("\n[S02] 新規登録画面")
    # ログアウト状態でアクセス
    page.evaluate("localStorage.removeItem('token'); localStorage.removeItem('dm_token')")
    page.goto(f"{BASE_URL}/register")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "register_01_empty")

    try:
        # placeholder="山田 花子" のテキスト入力が名前フィールド
        page.locator("input[type='text']").first.fill("田中 花子")
        page.locator("input[type='email']").fill("hanako@example.com")
        page.locator("input[type='password']").first.fill("mypassword123")
        wait(page)
        ss(page, "register_02_filled")
    except Exception as e:
        print(f"    ⚠ register_02: {e}")
        ss(page, "register_02_filled")

    try:
        # 重複メールエラー（既存アカウントで試す）
        page.locator("input[type='email']").fill(TEST_EMAIL)
        page.locator("button[type='submit']").click()
        wait(page, 1800)
        ss(page, "register_03_duplicate_error")
    except Exception as e:
        print(f"    ⚠ register_03: {e}")
        ss(page, "register_03_duplicate_error")

# ═══════════════════════════════════════════════════════════════
# S03: ダッシュボード  → dashboard_*.png
# ═══════════════════════════════════════════════════════════════
def capture_dashboard(page: Page, token: str):
    print("\n[S03] ダッシュボード")
    ensure_login(page)

    # 空の状態
    page.evaluate("localStorage.removeItem('dm_onboarding_done')")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "dashboard_01_onboarding_modal")

    # オンボーディングを閉じる
    try:
        close = page.locator("button:has-text('始める →'), button:has-text('✕')")
        if close.first.is_visible(timeout=2000):
            close.first.click()
            wait(page)
    except Exception:
        pass
    page.evaluate("localStorage.setItem('dm_onboarding_done', '1')")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "dashboard_02_empty")

    # 墓誌を作成してダッシュボードを再表示
    memorial_data = api_post("/memorials", {
        "name": "田中 正男",
        "birth_date": "1945-03-15",
        "death_date": "2023-11-20",
        "biography": "東京都生まれ。50年間にわたり家族のために尽力した。",
        "is_public": True,
    }, token)
    memorial_id = memorial_data.get("id")

    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "dashboard_03_with_memorial")

    # QRコードモーダル
    if memorial_id:
        try:
            qr_btn = page.locator("button:has-text('QRコード')").first
            if qr_btn.is_visible(timeout=2000):
                qr_btn.click()
                wait(page)
                ss(page, "dashboard_04_qr_modal")
                page.locator("button:has-text('閉じる')").first.click()
                wait(page)
        except Exception:
            pass

    # 未完了タスクパネル（優先度フィルター）
    try:
        priority_btn = page.locator("button:has-text('高優先度のみ'), button:has-text('優先')").first
        if priority_btn.is_visible(timeout=2000):
            priority_btn.click()
            wait(page)
            ss(page, "dashboard_05_priority_filter")
            priority_btn.click()
            wait(page)
    except Exception:
        pass

    # 終活ノートバナー・スタッツ全体
    page.evaluate("window.scrollTo(0, 0)")
    wait(page)
    ss(page, "dashboard_06_full_page")

    return memorial_id

# ═══════════════════════════════════════════════════════════════
# S04: 墓誌作成画面  → memorial_new_*.png
# ═══════════════════════════════════════════════════════════════
def capture_memorial_new(page: Page):
    print("\n[S04] 墓誌作成画面")
    ensure_login(page)
    page.goto(f"{BASE_URL}/memorials/new")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "memorial_new_01_empty")

    # フォームに入力 (placeholder="例：山田 太郎" が名前)
    try:
        page.locator("input[placeholder*='山田 太郎']").fill("山田 花子")
        page.locator("input[placeholder*='1930年']").fill("1950年6月1日")
        page.locator("input[placeholder*='2020年']").fill("2024年1月15日")
        page.locator("textarea").first.fill("長年にわたり地域のために貢献した。")
        wait(page)
        ss(page, "memorial_new_02_filled")
    except Exception as e:
        print(f"    ⚠ memorial_new_02: {e}")
        ss(page, "memorial_new_02_filled")

    # 公開設定・非公開時のパスワード欄
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        wait(page)
        ss(page, "memorial_new_03_public_options")
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
# S05: 墓誌編集画面  → memorial_edit_*.png
# ═══════════════════════════════════════════════════════════════
def capture_memorial_edit(page: Page, token: str, memorial_id: int):
    print("\n[S05] 墓誌編集画面")
    ensure_login(page)
    page.goto(f"{BASE_URL}/memorials/{memorial_id}/edit")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "memorial_edit_01_form")

    # 写真セクションまでスクロール
    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    wait(page)
    ss(page, "memorial_edit_02_photo_section")

    # 公開URLコピーボタン
    try:
        copy_btn = page.locator("button:has-text('URLをコピー'), button:has-text('公開URL')").first
        if copy_btn.is_visible(timeout=2000):
            page.evaluate("window.scrollTo(0, 0)")
            wait(page)
            ss(page, "memorial_edit_03_public_controls")
    except Exception:
        pass

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "memorial_edit_04_bottom")

# ═══════════════════════════════════════════════════════════════
# S06: QRコード印刷  → print_qr_*.png  (print_qr matches no screen_id)
# screen_spec_generatorは memorial_edit カテゴリでカバー
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# S07: 公開墓誌ページ  → memorial_public_*.png
# ═══════════════════════════════════════════════════════════════
def capture_memorial_public(page: Page, token: str, memorial_id: int):
    print("\n[S07] 公開墓誌ページ")
    memorials = api_get("/memorials", token)
    if isinstance(memorials, list) and memorials:
        slug = memorials[0]["slug"]
        page.goto(f"{BASE_URL}/m/{slug}")
        page.wait_for_load_state("networkidle")
        wait(page, 1200)
        ss(page, "memorial_public_01_top")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        wait(page)
        ss(page, "memorial_public_02_middle")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        wait(page)
        ss(page, "memorial_public_03_bottom")

    # パスワード保護（非公開墓誌）
    pw_memorial = api_post("/memorials", {
        "name": "非公開テスト",
        "is_public": False,
        "password": "secret123",
    }, token)
    if pw_slug := pw_memorial.get("slug"):
        page.goto(f"{BASE_URL}/m/{pw_slug}")
        page.wait_for_load_state("networkidle")
        wait(page)
        ss(page, "memorial_public_04_password_gate")
        try:
            page.locator("input[type='password']").fill("wrongpass")
            page.locator("button:has-text('アクセス')").click()
            wait(page)
            ss(page, "memorial_public_05_password_wrong")
        except Exception:
            pass

    # 存在しないslug → 404
    page.goto(f"{BASE_URL}/m/does-not-exist-xyz")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "memorial_public_06_not_found")

# ═══════════════════════════════════════════════════════════════
# S08: 終活チェックリスト  → shukatsu_*.png
# ═══════════════════════════════════════════════════════════════
def capture_shukatsu(page: Page):
    print("\n[S08] 終活チェックリスト")
    ensure_login(page)
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "shukatsu_01_scorecard_top")

    page.evaluate("window.scrollTo(0, 400)")
    wait(page)
    ss(page, "shukatsu_02_quick_links")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    wait(page)
    ss(page, "shukatsu_03_checklist_all")

    # カテゴリフィルター
    for cat in ["相続", "遺言", "医療", "デジタル"]:
        try:
            page.click(f"button:has-text('{cat}')")
            wait(page, 400)
        except Exception:
            pass
    ss(page, "shukatsu_04_category_filter")

    # チェックを入れる
    try:
        first_cb = page.locator("button[style*='border-radius: 50%']").first
        if first_cb.is_visible(timeout=1000):
            first_cb.click()
            wait(page)
            ss(page, "shukatsu_05_item_checked")
    except Exception:
        pass

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "shukatsu_06_bottom_disclaimer")

# ═══════════════════════════════════════════════════════════════
# S09: 相続計画一覧  → estate_list_*.png
# ═══════════════════════════════════════════════════════════════
def capture_estate_list(page: Page, token: str) -> int:
    print("\n[S09] 相続計画一覧")
    ensure_login(page)
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_list_01_empty")

    # 新規作成モーダル（UIで撮影）
    try:
        page.click("button:has-text('新規作成'), button:has-text('+ 新しい計画')")
        wait(page)
        ss(page, "estate_list_02_create_modal")
        title_inp = page.locator("input[placeholder*='計画名'], input[placeholder*='タイトル']").first
        if title_inp.is_visible(timeout=1500):
            title_inp.fill("佐藤家の相続計画")
        page.click("button:has-text('作成'), button:has-text('保存')")
        wait(page, 1500)
    except Exception:
        pass

    # APIで確実に計画を作成・取得
    plans = api_get("/estate-plans", token)
    if isinstance(plans, list) and plans:
        plan_id = plans[0]["id"]
        # タイトルを統一
        requests.patch(
            f"{API_URL}/estate-plans/{plan_id}",
            json={"title": "佐藤家の相続計画"},
            headers={"Authorization": f"Bearer {token}"},
        )
    else:
        resp = api_post("/estate-plans", {"title": "佐藤家の相続計画"}, token)
        plan_id = resp.get("id", 0)

    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_list_03_with_plan")

    # タイトル変更ボタン
    try:
        edit_btn = page.locator("button:has-text('✏'), button:has-text('変更')").first
        if edit_btn.is_visible(timeout=1000):
            edit_btn.click()
            wait(page)
            ss(page, "estate_list_04_rename_inline")
            page.keyboard.press("Escape")
    except Exception:
        pass

    print(f"  plan_id={plan_id}")
    return plan_id

# ═══════════════════════════════════════════════════════════════
# S10: 相続計画 - 家族構成  → estate_family_*.png
# ═══════════════════════════════════════════════════════════════
def capture_estate_family(page: Page, token: str, plan_id: int) -> int:
    print("\n[S10] 相続計画 - 家族構成")
    ensure_login(page)
    # まず空状態を撮影
    page.goto(f"{BASE_URL}/estate/{plan_id}/family")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_family_01_empty")

    # APIで家族を事前登録してから再ロード
    api_post(f"/estate-plans/{plan_id}/family", {
        "members": [
            {"name": "佐藤 花子", "relationship": "spouse", "is_alive": True},
            {"name": "佐藤 一郎", "relationship": "child", "is_alive": True},
            {"name": "佐藤 二郎", "relationship": "child", "is_alive": True},
        ]
    }, token)

    page.goto(f"{BASE_URL}/estate/{plan_id}/family")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_family_02_with_members")

    # 追加フォームを開いて撮影
    try:
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('家族を追加'), button:has-text('メンバー追加')").first
        if add_btn.is_visible(timeout=2000):
            add_btn.click()
            wait(page)
            ss(page, "estate_family_03_add_form")
            page.keyboard.press("Escape")
            wait(page, 500)
    except Exception:
        pass

    ss(page, "estate_family_04_scrolled")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "estate_family_05_save_button")
    return plan_id

# ═══════════════════════════════════════════════════════════════
# S11: 相続計画 - 財産・負債  → estate_assets_*.png
# ═══════════════════════════════════════════════════════════════
def capture_estate_assets(page: Page, token: str, plan_id: int):
    print("\n[S11] 相続計画 - 財産・負債")
    ensure_login(page)
    # 空状態を撮影
    page.goto(f"{BASE_URL}/estate/{plan_id}/assets")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_assets_01_empty")

    # APIで財産を事前登録
    api_post(f"/estate-plans/{plan_id}/assets", {
        "assets": [
            {"asset_type": "real_estate", "name": "自宅（東京都渋谷区）", "estimated_value": 35000000},
            {"asset_type": "bank_account", "name": "三菱UFJ銀行", "estimated_value": 8000000},
            {"asset_type": "stocks", "name": "株式（トヨタ自動車等）", "estimated_value": 5000000},
            {"asset_type": "debt", "name": "住宅ローン残債", "estimated_value": -12000000},
        ]
    }, token)

    page.goto(f"{BASE_URL}/estate/{plan_id}/assets")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "estate_assets_02_with_assets")

    # 財産追加フォームを開いて撮影
    try:
        add_btn = page.locator("button:has-text('財産を追加'), button:has-text('+ 追加'), button:has-text('追加')").first
        if add_btn.is_visible(timeout=2000):
            add_btn.click()
            wait(page)
            ss(page, "estate_assets_03_add_form")
            page.keyboard.press("Escape")
            wait(page, 500)
    except Exception:
        pass

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "estate_assets_04_total_and_save")

# ═══════════════════════════════════════════════════════════════
# S12: 相続計算結果  → estate_result_*.png
# ═══════════════════════════════════════════════════════════════
def capture_estate_result(page: Page, token: str, plan_id: int):
    print("\n[S12] 相続計算結果")
    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/result")
    page.wait_for_load_state("networkidle")
    wait(page, 2000)
    ss(page, "estate_result_01_top")

    page.evaluate("window.scrollTo(0, 400)")
    wait(page)
    ss(page, "estate_result_02_heirs_table")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    wait(page)
    ss(page, "estate_result_03_reserved_rights")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "estate_result_04_disclaimer")

# ═══════════════════════════════════════════════════════════════
# S13: 遺言書シミュレーター  → estate_will_*.png
# ═══════════════════════════════════════════════════════════════
def capture_estate_will(page: Page, token: str, plan_id: int):
    print("\n[S13] 遺言書シミュレーター")
    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/will")
    page.wait_for_load_state("networkidle")
    wait(page, 2000)
    ss(page, "estate_will_01_default")

    # 配分設定
    try:
        inputs = page.locator("input[type='number']").all()
        if inputs:
            inputs[0].fill("20000000")
            wait(page)
            ss(page, "estate_will_02_allocation_set")
    except Exception:
        pass

    # 法定相続分リセットボタン
    try:
        reset_btn = page.locator("button:has-text('法定相続分')").first
        if reset_btn.is_visible(timeout=1000):
            ss(page, "estate_will_03_reset_button")
    except Exception:
        pass

    # プレビュー
    try:
        preview_btn = page.locator("button:has-text('プレビュー'), button:has-text('テキスト')").first
        if preview_btn.is_visible(timeout=2000):
            preview_btn.click()
            wait(page, 1000)
            ss(page, "estate_will_04_text_preview")
    except Exception:
        pass

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "estate_will_05_print_button")

# ═══════════════════════════════════════════════════════════════
# S14: エンディングノート（全10タブ）  → ending_note_*.png
# ═══════════════════════════════════════════════════════════════
def capture_ending_note(page: Page):
    print("\n[S14] エンディングノート")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    wait(page, 1500)
    ss(page, "ending_note_01_overview_tabs")

    # ── 医療・介護タブ ──
    try:
        page.click("button:has-text('医療・介護')")
        wait(page)
        ss(page, "ending_note_02_medical_default")
        # 延命治療設定を変更
        radios = page.locator("input[type='radio']").all()
        if radios:
            radios[0].click()
        page.locator("textarea").first.fill("かかりつけ医: 山田クリニック 03-1234-5678")
        wait(page, 1200)
        ss(page, "ending_note_03_medical_filled")
    except Exception:
        pass

    # ── 葬儀タブ ──
    try:
        page.click("button:has-text('葬儀')")
        wait(page)
        ss(page, "ending_note_04_funeral_default")
        page.locator("textarea").first.fill("家族葬を希望。音楽はショパンのノクターンを。")
        wait(page, 1200)
        ss(page, "ending_note_05_funeral_filled")
    except Exception:
        pass

    # ── 形見分けタブ ──
    try:
        page.click("button:has-text('形見分け')")
        wait(page)
        ss(page, "ending_note_06_bequest_empty")
        # アイテム追加フォーム
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('追加')").first
        if add_btn.is_visible(timeout=1000):
            add_btn.click()
            wait(page)
            inputs = page.locator("input[type='text']").all()
            for i, inp in enumerate(inputs[:2]):
                inp.fill(["祖母の形見の時計", "長男"][i])
            page.click("button:has-text('保存'), button:has-text('登録')")
            wait(page, 1000)
            ss(page, "ending_note_07_bequest_added")
    except Exception:
        pass

    # ── デジタル資産タブ ──
    try:
        page.click("button:has-text('デジタル資産')")
        wait(page)
        ss(page, "ending_note_08_digital_empty")
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('デジタル資産を追加')").first
        if add_btn.is_visible(timeout=1000):
            add_btn.click()
            wait(page)
            inputs = page.locator("input[type='text']").all()
            if inputs:
                inputs[0].fill("Gmail")
            page.click("button:has-text('保存'), button:has-text('登録')")
            wait(page, 1000)
            ss(page, "ending_note_09_digital_added")
    except Exception:
        pass

    # ── 緊急連絡先タブ ──
    try:
        page.click("button:has-text('緊急連絡先')")
        wait(page)
        ss(page, "ending_note_10_contacts_empty")
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('連絡先を追加')").first
        if add_btn.is_visible(timeout=1000):
            add_btn.click()
            wait(page)
            inputs = page.locator("input[type='text']").all()
            for i, inp in enumerate(inputs[:2]):
                inp.fill(["佐藤 一郎", "長男"][i])
            page.click("button:has-text('保存'), button:has-text('登録')")
            wait(page, 1000)
            ss(page, "ending_note_11_contacts_added")
    except Exception:
        pass

    # ── ペットタブ ──
    try:
        page.click("button:has-text('ペット')")
        wait(page)
        ss(page, "ending_note_12_pets_empty")
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('ペットを追加')").first
        if add_btn.is_visible(timeout=1000):
            add_btn.click()
            wait(page)
            inputs = page.locator("input[type='text']").all()
            for i, inp in enumerate(inputs[:2]):
                inp.fill(["ポチ", "柴犬"][i])
            page.click("button:has-text('保存'), button:has-text('登録')")
            wait(page, 1000)
            ss(page, "ending_note_13_pets_added")
    except Exception:
        pass

    # ── お気に入りタブ ──
    try:
        page.click("button:has-text('お気に入り')")
        wait(page)
        ss(page, "ending_note_14_favorites_empty")
        textareas = page.locator("textarea").all()
        if textareas:
            textareas[0].fill("ベートーベン交響曲第9番、昭和の演歌")
        wait(page, 1200)
        ss(page, "ending_note_15_favorites_filled")
    except Exception:
        pass

    # ── 家族へのメッセージタブ ──
    try:
        page.click("button:has-text('家族へのメッセージ')")
        wait(page)
        ss(page, "ending_note_16_family_msg_empty")
        textareas = page.locator("textarea").all()
        if textareas:
            textareas[0].fill("家族へ。ありがとう。いつも支えてくれて感謝しています。健康に気をつけて元気に生きてください。")
        wait(page, 1200)
        ss(page, "ending_note_17_family_msg_filled")
    except Exception:
        pass

    # ── 追悼メッセージタブ ──
    try:
        page.click("button:has-text('追悼メッセージ')")
        wait(page)
        ss(page, "ending_note_18_scheduled_msg_empty")
        add_btn = page.locator("button:has-text('+ メッセージを追加'), button:has-text('追加')").first
        if add_btn.is_visible(timeout=1000):
            add_btn.click()
            wait(page)
            ss(page, "ending_note_19_scheduled_msg_form")
            inputs = page.locator("input").all()
            for i, inp in enumerate(inputs[:2]):
                inp.fill(["山田 太郎", "taro@example.com"][i])
            try:
                page.locator("input[placeholder*='件名']").fill("最後のメッセージ")
                page.locator("textarea").last.fill("いつも支えてくれてありがとう。")
            except Exception:
                pass
            page.click("button:has-text('保存')")
            wait(page, 1000)
            ss(page, "ending_note_20_scheduled_msg_created")
    except Exception:
        pass

    # ── ビデオメッセージタブ ──
    try:
        page.click("button:has-text('ビデオメッセージ')")
        wait(page)
        ss(page, "ending_note_21_video_msg_empty")
        try:
            page.locator("input[placeholder*='タイトル']").fill("家族へ")
            wait(page)
            ss(page, "ending_note_22_video_msg_form")
        except Exception:
            pass
    except Exception:
        pass

    # タブドットインジケーター確認（ページ先頭に戻る）
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    wait(page, 1500)
    ss(page, "ending_note_23_tab_dots")

    # 保存タイムスタンプ
    page.evaluate("window.scrollTo(0, 0)")
    wait(page)
    ss(page, "ending_note_24_autosave_timestamp")

# ═══════════════════════════════════════════════════════════════
# S15: デジタル遺品鍵  → digital_key_*.png
# ═══════════════════════════════════════════════════════════════
def capture_digital_key(page: Page, token: str):
    print("\n[S15] デジタル遺品鍵")
    ensure_login(page)
    page.goto(f"{BASE_URL}/digital-key")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "digital_key_01_top")

    # 開錠条件セクション
    page.evaluate("window.scrollTo(0, 0)")
    ss(page, "digital_key_02_unlock_condition")

    # デッドマンスイッチを有効化
    try:
        toggle = page.locator("div[style*='cursor: pointer']").first
        if toggle.is_visible(timeout=2000):
            toggle.click()
            wait(page, 1000)
            ss(page, "digital_key_03_deadman_enabled")
            # 日数選択
            day_btn = page.locator("button:has-text('90日')").first
            if day_btn.is_visible(timeout=1000):
                day_btn.click()
                wait(page)
            # チェックインボタン
            checkin = page.locator("button:has-text('生存確認')").first
            if checkin.is_visible(timeout=1000):
                ss(page, "digital_key_04_deadman_checkin")
    except Exception:
        pass

    # 信頼者追加フォーム
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "digital_key_05_trusted_persons_empty")

    try:
        add_btn = page.locator("button:has-text('+ 追加'), button:has-text('追加')").first
        if add_btn.is_visible(timeout=2000):
            add_btn.click()
            wait(page)
            ss(page, "digital_key_06_add_person_form")
            name_inp = page.locator("input[placeholder*='名前'], input[placeholder*='太郎']").first
            email_inp = page.locator("input[type='email']").first
            if name_inp.count() > 0:
                name_inp.fill("山田 一郎")
                email_inp.fill("ichiro@example.com")
                page.click("button:has-text('登録')")
                wait(page, 1000)
                ss(page, "digital_key_07_person_added")
    except Exception:
        pass

    # 解除キーURL表示
    try:
        url_btn = page.locator("button:has-text('解除キーURL'), button:has-text('URLを表示')").first
        if url_btn.is_visible(timeout=2000):
            url_btn.click()
            wait(page)
            ss(page, "digital_key_08_token_url_visible")
    except Exception:
        pass

    # 使い方ガイド
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "digital_key_09_usage_guide")

# ═══════════════════════════════════════════════════════════════
# S16: アカウント設定  → account_*.png
# ═══════════════════════════════════════════════════════════════
def capture_account(page: Page):
    print("\n[S16] アカウント設定")
    ensure_login(page)
    page.goto(f"{BASE_URL}/account")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "account_01_top")

    # パスワード変更セクション
    page.evaluate("window.scrollTo(0, 0)")
    ss(page, "account_02_password_section")

    # フォントサイズ・かんたんモード
    try:
        font_section = page.locator("text=フォントサイズ").first
        if font_section.is_visible(timeout=2000):
            font_section.scroll_into_view_if_needed()
            wait(page)
            ss(page, "account_03_font_and_simple_mode")
    except Exception:
        pass

    # 各フォントサイズ選択
    try:
        large_btn = page.locator("button:has-text('大'), button:has-text('large')").first
        if large_btn.is_visible(timeout=1000):
            large_btn.click()
            wait(page)
            ss(page, "account_04_font_large_preview")
        medium_btn = page.locator("button:has-text('標準'), button:has-text('medium')").first
        if medium_btn.is_visible(timeout=1000):
            medium_btn.click()
            wait(page)
    except Exception:
        pass

    # 活動ログ
    try:
        log_btn = page.locator("button:has-text('活動ログ'), button:has-text('ログを表示')").first
        if log_btn.is_visible(timeout=2000):
            log_btn.click()
            wait(page, 1000)
            ss(page, "account_05_activity_log")
            close = page.locator("button:has-text('閉じる')").first
            if close.is_visible(timeout=1000):
                close.click()
    except Exception:
        pass

    # 2FA セクション
    try:
        totp_section = page.locator("text=二要素認証, text=2FA, text=TOTP").first
        if totp_section.is_visible(timeout=2000):
            totp_section.scroll_into_view_if_needed()
            wait(page)
            ss(page, "account_06_2fa_section")
    except Exception:
        pass

    # エクスポートセクション
    try:
        export_section = page.locator("text=データエクスポート, text=エクスポート").first
        if export_section.is_visible(timeout=2000):
            export_section.scroll_into_view_if_needed()
            wait(page)
            ss(page, "account_07_export_section")
    except Exception:
        pass

    # アカウント削除セクション（最下部）
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "account_08_delete_section")

    # 全体スクロール
    page.evaluate("window.scrollTo(0, 0)")
    ss(page, "account_09_full_top")

# ═══════════════════════════════════════════════════════════════
# S17: リマインダー設定  → reminders_*.png
# ═══════════════════════════════════════════════════════════════
def capture_reminders(page: Page):
    print("\n[S17] リマインダー設定")
    ensure_login(page)
    page.goto(f"{BASE_URL}/settings/reminders")
    page.wait_for_load_state("networkidle")
    wait(page, 1200)
    ss(page, "reminders_01_enabled")

    # 月選択
    try:
        page.select_option("select", "5")
        wait(page)
        ss(page, "reminders_02_month_selected")
    except Exception:
        pass

    # 通知設定トグル群
    page.evaluate("window.scrollTo(0, 300)")
    wait(page)
    ss(page, "reminders_03_notification_toggles")

    # オフ状態
    try:
        toggle = page.locator("div[style*='cursor: pointer']").first
        if toggle.is_visible(timeout=2000):
            toggle.click()
            wait(page)
            ss(page, "reminders_04_disabled")
            toggle.click()
            wait(page)
    except Exception:
        pass

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait(page)
    ss(page, "reminders_05_email_input")

# ═══════════════════════════════════════════════════════════════
# S18: デジタル遺品鍵 解除申請ページ  → unlock_*.png
# ═══════════════════════════════════════════════════════════════
def capture_unlock(page: Page, token: str):
    print("\n[S18] 解除申請ページ（公開）")
    # デジタルキーの信頼者情報を取得
    key_data = api_get("/digital-key", token)
    trusted_persons = key_data.get("trusted_persons", [])

    if trusted_persons:
        person = trusted_persons[0]
        pid    = person["id"]
        tok    = person["access_token"]
        page.goto(f"{BASE_URL}/unlock/{pid}?token={tok}")
        page.wait_for_load_state("networkidle")
        wait(page, 1200)
        ss(page, "unlock_01_ready")

        # 申請ボタンクリック
        try:
            page.click("button:has-text('解除申請を送る')")
            wait(page, 1500)
            ss(page, "unlock_02_success_unlocked")
        except Exception:
            ss(page, "unlock_02_success_unlocked")
    else:
        # フォールバック: 無効なURLでエラー状態
        page.goto(f"{BASE_URL}/unlock/9999?token=invalid")
        page.wait_for_load_state("networkidle")
        wait(page)
        ss(page, "unlock_01_ready")

    # 無効なトークンでエラー表示
    page.goto(f"{BASE_URL}/unlock/9999?token=invalidtoken")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "unlock_03_invalid_url_error")

    # URLパラメーターなしのエラー
    page.goto(f"{BASE_URL}/unlock/9999")
    page.wait_for_load_state("networkidle")
    wait(page)
    ss(page, "unlock_04_missing_token_error")

# ═══════════════════════════════════════════════════════════════
# 認証ガード  → auth_guard_*.png  (dashboard/shukatsu カテゴリに含める)
# ═══════════════════════════════════════════════════════════════
def capture_auth_guard(page: Page):
    print("\n[認証ガード] 未認証アクセス")
    # ログアウト状態にする
    page.evaluate("localStorage.removeItem('token'); localStorage.removeItem('dm_token')")
    page.goto(f"{BASE_URL}/dashboard")
    wait(page, 1500)
    ss(page, "dashboard_07_auth_redirect_to_login")

    page.goto(f"{BASE_URL}/shukatsu")
    wait(page, 1500)
    ss(page, "shukatsu_07_auth_redirect")


# ═══════════════════════════════════════════════════════════════
# メイン
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("全画面スクリーンショット取得（仕様書用・全17画面網羅版）")
    print("=" * 60)

    token = api_token()
    print(f"  Token: {token[:20]}..." if token else "  ⚠ トークン取得失敗")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,
        )
        page = ctx.new_page()

        # 最初にUIログイン
        requests.post(f"{API_URL}/auth/register",
            json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
        login_ui(page)

        # ── 1. ログイン画面 ─────────────────────────────
        capture_login(page)

        # ── 2. 新規登録画面 ────────────────────────────
        capture_register(page)
        # 再ログイン（capture_register でトークンをクリアしたため）
        login_ui(page)

        # ── 3. ダッシュボード ──────────────────────────
        memorial_id = capture_dashboard(page, token)

        # ── 4. 墓誌作成 ───────────────────────────────
        capture_memorial_new(page)
        ensure_login(page)

        # ── 5. 墓誌編集 ───────────────────────────────
        if memorial_id:
            capture_memorial_edit(page, token, memorial_id)

        # ── 7. 公開墓誌 ───────────────────────────────
        capture_memorial_public(page, token, memorial_id)
        ensure_login(page)

        # ── 8. 終活チェックリスト ──────────────────────
        capture_shukatsu(page)

        # ── 9. 相続計画一覧 ───────────────────────────
        plan_id = capture_estate_list(page, token)

        if plan_id:
            # ── 10. 家族構成 ───────────────────────────
            capture_estate_family(page, token, plan_id)

            # ── 11. 財産・負債 ─────────────────────────
            capture_estate_assets(page, token, plan_id)

            # ── 12. 計算結果 ───────────────────────────
            capture_estate_result(page, token, plan_id)

            # ── 13. 遺言書シミュレーター ───────────────
            capture_estate_will(page, token, plan_id)

        # ── 14. エンディングノート（全10タブ）──────────
        capture_ending_note(page)

        # ── 15. デジタル遺品鍵 ────────────────────────
        capture_digital_key(page, token)

        # ── 16. アカウント設定 ────────────────────────
        capture_account(page)

        # ── 17. リマインダー設定 ──────────────────────
        capture_reminders(page)

        # ── 18. 解除申請ページ（公開） ─────────────────
        ensure_login(page)
        capture_unlock(page, token)

        # ── 認証ガード ────────────────────────────────
        capture_auth_guard(page)

        browser.close()

    # 撮影結果一覧
    files = sorted(f for f in os.listdir(SS_DIR) if f.endswith(".png") and
                   not f.startswith("0") and not f.startswith("s0"))
    new_files = sorted(f for f in os.listdir(SS_DIR) if f.endswith(".png") and
                       "_" in f and not f.startswith("s") and not f.startswith("0") and
                       f[0].isalpha())
    print("\n" + "=" * 60)
    print(f"撮影完了: 新形式 {len(new_files)} 枚")
    for f in new_files:
        sz = os.path.getsize(os.path.join(SS_DIR, f)) // 1024
        print(f"  {f}  ({sz} KB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
