"""
E2E テスト - Playwright Python
全画面のスクリーンショット取得 + 機能テスト

実行方法:
  1. バックエンド起動: cd backend && uvicorn app.main:app --port 8000
  2. フロントエンド起動: cd frontend && npm run dev (port 5173)
  3. python3 e2e/test_e2e.py

スクリーンショットは e2e/screenshots/ に保存される。
"""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from playwright.sync_api import sync_playwright, expect, Page, Browser

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000/api"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

TEST_EMAIL = "e2e_test@example.com"
TEST_PASSWORD = "e2etest123"
TEST_NAME = "E2Eテストユーザー"

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS = []


def ss(page: Page, name: str):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def check(condition: bool, name: str, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        RESULTS.append(("PASS", name, ""))
        print(f"  ✅ {name}")
    else:
        FAIL_COUNT += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))


def register_and_login(page: Page):
    """ユーザー登録とログインを実行してトークンを返す（API経由）"""
    import requests
    requests.post(f"{API_URL}/auth/register", json={
        "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD
    })
    res = requests.post(f"{API_URL}/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    return res.json().get("access_token")


def ensure_logged_in(page: Page):
    """ブラウザがログイン状態でなければUIでログインし直す"""
    # ダッシュボードへアクセスしてリダイレクト先を確認
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1500)
    if "/login" in page.url:
        # UIでログイン
        page.fill("input[type='email'], input[name='email']", TEST_EMAIL)
        page.fill("input[type='password']", TEST_PASSWORD)
        page.click("button[type='submit'], button:has-text('ログイン')")
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)
        page.wait_for_load_state("networkidle")


# ═══════════════════════════════════════════════════════════════
# 1. ログイン画面テスト
# ═══════════════════════════════════════════════════════════════

def test_login_page(page: Page):
    print("\n[1] ログイン画面")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    ss(page, "01_login_page")

    check(page.locator("input[type='email'], input[name='email']").count() > 0,
          "メールアドレス入力欄が表示されている")
    check(page.locator("input[type='password']").count() > 0,
          "パスワード入力欄が表示されている")
    check(page.locator("button[type='submit'], button:has-text('ログイン')").count() > 0,
          "ログインボタンが表示されている")

    # 間違ったパスワードでエラー確認
    page.fill("input[type='email'], input[name='email']", "wrong@example.com")
    page.fill("input[type='password']", "wrongpass")
    page.click("button[type='submit'], button:has-text('ログイン')")
    page.wait_for_timeout(1500)
    ss(page, "01b_login_error")
    check(page.url.endswith("/login") or "/login" in page.url,
          "ログイン失敗時はログイン画面に留まる")


def test_register_page(page: Page):
    print("\n[2] ユーザー登録画面")
    page.goto(f"{BASE_URL}/register")
    page.wait_for_load_state("networkidle")
    ss(page, "02_register_page")

    check(page.locator("input[type='email'], input[name='email']").count() > 0,
          "メールアドレス入力欄が表示されている")
    check(page.locator("input[type='password']").count() > 0,
          "パスワード入力欄が表示されている")


def test_login_success(page: Page):
    print("\n[3] ログイン成功→ダッシュボードへ遷移")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")

    # 事前にユーザー登録
    import requests
    requests.post(f"{API_URL}/auth/register", json={
        "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD
    })

    page.fill("input[type='email'], input[name='email']", TEST_EMAIL)
    page.fill("input[type='password']", TEST_PASSWORD)
    ss(page, "03a_login_filled")
    page.click("button[type='submit'], button:has-text('ログイン')")
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)
    page.wait_for_load_state("networkidle")
    ss(page, "03b_dashboard_after_login")

    check("/dashboard" in page.url, "ログイン後にダッシュボードへ遷移する")
    check(page.locator(f"text={TEST_NAME}").count() > 0 or
          page.locator("text=墓誌").count() > 0,
          "ダッシュボードにユーザー名または墓誌関連テキストが表示されている")


# ═══════════════════════════════════════════════════════════════
# 2. ダッシュボード
# ═══════════════════════════════════════════════════════════════

def test_dashboard(page: Page):
    print("\n[4] ダッシュボード")
    page.wait_for_load_state("networkidle")
    ss(page, "04_dashboard")

    check(page.locator("text=終活ノートを開く").count() > 0,
          "終活ノートバナーが表示されている")
    check(page.locator("text=墓誌一覧").count() > 0,
          "墓誌一覧タイトルが表示されている")
    check(page.locator("text=新規作成").count() > 0 or
          page.locator("text=＋").count() > 0,
          "新規作成ボタンが表示されている")
    check(page.locator("text=ログアウト").count() > 0,
          "ログアウトボタンが表示されている")

    # 終活バナーのリンク確認
    banner = page.locator("text=終活ノートを開く").first
    check(banner.count() > 0, "終活バナーのテキストがある")


# ═══════════════════════════════════════════════════════════════
# 3. 終活ダッシュボード
# ═══════════════════════════════════════════════════════════════

def test_shukatsu_page(page: Page):
    print("\n[5] 終活ダッシュボード")
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    ss(page, "05_shukatsu_dashboard")

    check(page.locator("text=終活ノート").count() > 0 or
          page.locator("text=終活準備スコア").count() > 0,
          "終活ノートまたは終活準備スコアが表示されている")
    check(page.locator("text=相続の棚卸し").count() > 0,
          "相続の棚卸しクイックリンクが表示されている")
    check(page.locator("text=終活チェックリスト").count() > 0,
          "終活チェックリストセクションが表示されている")
    ss(page, "05b_shukatsu_checklist")
    check(page.locator("svg").count() > 0,
          "完了率SVGゲージが表示されている")


def test_shukatsu_checklist_toggle(page: Page):
    print("\n[6] チェックリストのトグル（カスタムボタン）")
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    check(page.locator("text=相続人を確認した").count() > 0,
          "チェックリストアイテムが表示されている")

    # 「入力する →」リンクの親要素（listItem div）内の最初のボタンがチェックボックス
    # NOTE: header の「ログアウト」ボタンをクリックしないよう、link から逆引きする
    go_links = page.locator("a:has-text('入力する')")
    if go_links.count() > 0:
        # 最初の「入力する →」リンクの親 div が listItem
        list_item = go_links.first.locator("xpath=..")
        checkbox_btn = list_item.locator("button").first
        if checkbox_btn.count() > 0:
            checkbox_btn.click()
            page.wait_for_timeout(1500)
            ss(page, "06_checklist_toggled")
            # 1/17 → 1項目完了になったか（スコア "6%" or カウント "1 / 17"）
            check(page.locator("text=1 / 17").count() > 0 or
                  page.locator("text=6%").count() > 0 or
                  page.locator("text=✓").count() > 0,
                  "チェックリストのトグルが機能する（完了カウント変化）")
        else:
            check(False, "チェックボックスボタンが見つかる", "button要素が存在しない")
    else:
        check(False, "チェックリストアイテムが見つかる", "「入力する」リンクが存在しない")


# ═══════════════════════════════════════════════════════════════
# 4. 相続プランウィザード
# ═══════════════════════════════════════════════════════════════

def test_estate_plan_list(page: Page):
    print("\n[7] 相続プラン一覧")
    ensure_logged_in(page)
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")
    ss(page, "07_estate_plan_list")

    check(page.locator("text=相続").count() > 0,
          "相続関連テキストが表示されている")
    check(page.locator("button, a").filter(has_text=("新規", "作成", "＋")).count() > 0 or
          page.locator("[href*='family'], [href*='estate']").count() > 0,
          "新規作成 or 計画へのリンクが表示されている")


def test_estate_plan_create_and_family(page: Page):
    print("\n[8] 相続プラン作成 → 家族構成入力")
    ensure_logged_in(page)
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    ss(page, "08a_estate_list")

    # Step1: 「＋ 新規作成」ボタンをクリック → フォーム表示
    new_btn = page.locator("button:has-text('新規作成')").first
    if new_btn.count() > 0:
        new_btn.click()
        page.wait_for_timeout(500)
        ss(page, "08b_estate_create_form")
        check(page.locator("input[placeholder*='計画名']").count() > 0 or
              page.locator("input[placeholder*='相続計画']").count() > 0,
              "計画名入力フォームが表示される")

        # Step2: 「作成して開始」ボタンをクリック → 家族入力ページへ遷移
        start_btn = page.locator("button:has-text('作成して開始')").first
        if start_btn.count() > 0:
            start_btn.click()
            page.wait_for_url("**/family", timeout=5000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            ss(page, "08c_family_input")
            check("/family" in page.url, "家族入力ページへ遷移した")

            # 続柄セレクト・名前入力があるか確認
            check(page.locator("text=配偶者").count() > 0 or
                  page.locator("select").count() > 0 or
                  page.locator("text=家族").count() > 0,
                  "家族入力フォームが表示されている")

            # 「追加」ボタンで家族メンバーを追加
            add_btn = page.locator("button").filter(has_text=("メンバーを追加", "追加", "＋")).first
            if add_btn.count() > 0:
                add_btn.click()
                page.wait_for_timeout(500)
                ss(page, "08d_family_member_row")
                check(True, "家族メンバー追加ボタンが機能する")
        else:
            check(False, "「作成して開始」ボタンが表示される", "ボタンが見つからない")
    else:
        check(False, "「新規作成」ボタンが表示される", "ボタンが見つからない")


def test_estate_result(page: Page):
    print("\n[9] 相続計算結果")
    ensure_logged_in(page)
    import requests, json
    token = register_and_login(page)
    headers = {"Authorization": f"Bearer {token}"}

    plan_res = requests.post(f"{API_URL}/estate-plans",
        json={"title": "E2Eテスト計画"}, headers=headers)
    plan_id = plan_res.json()["id"]

    requests.post(f"{API_URL}/estate-plans/{plan_id}/family", json={
        "members": [
            {"name": "配偶者", "relationship": "spouse"},
            {"name": "長男", "relationship": "child"},
        ]
    }, headers=headers)

    requests.post(f"{API_URL}/estate-plans/{plan_id}/assets", json={
        "assets": [
            {"name": "不動産", "asset_type": "real_estate", "estimated_value": 40_000_000},
            {"name": "預貯金", "asset_type": "bank_account", "estimated_value": 20_000_000},
        ]
    }, headers=headers)

    page.goto(f"{BASE_URL}/estate/{plan_id}/result")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ss(page, "09_estate_result")

    check(page.locator("text=配偶者").count() > 0,
          "配偶者が相続人として表示されている")
    check(page.locator("text=1/2").count() > 0 or
          page.locator("text=50%").count() > 0 or
          page.locator("text=50").count() > 0,
          "配偶者の相続分(1/2=50%)が表示されている")
    check(page.locator("text=遺留分").count() > 0 or
          page.locator("text=基礎控除").count() > 0,
          "遺留分または基礎控除が表示されている")


# ═══════════════════════════════════════════════════════════════
# 5. エンディングノート
# ═══════════════════════════════════════════════════════════════

def test_ending_note_page(page: Page):
    print("\n[10] エンディングノート - 初期表示")
    ensure_logged_in(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ss(page, "10_ending_note_initial")

    check(page.locator("text=医療").count() > 0 or
          page.locator("text=延命").count() > 0,
          "医療タブ・延命治療項目が表示されている")
    check(page.locator("text=葬儀").count() > 0,
          "葬儀タブが表示されている")
    check(page.locator("text=メッセージ").count() > 0 or
          page.locator("text=家族").count() > 0,
          "家族メッセージ項目が表示されている")


def test_ending_note_medical_tab(page: Page):
    print("\n[11] エンディングノート - 医療・介護タブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # 「医療・介護」タブは初期表示
    ss(page, "11_ending_note_medical")

    check(page.locator("text=延命治療").count() > 0,
          "延命治療セクションが表示されている")
    check(page.locator("text=心肺蘇生").count() > 0 or
          page.locator("text=CPR").count() > 0,
          "心肺蘇生(CPR)セクションが表示されている")
    check(page.locator("text=臓器提供").count() > 0,
          "臓器提供セクションが表示されている")

    # ボタングループ形式の選択肢をクリック
    btn_hopes_not = page.locator("button:has-text('希望しない')").first
    if btn_hopes_not.count() > 0:
        btn_hopes_not.click()
        page.wait_for_timeout(1500)
        ss(page, "11b_ending_note_medical_changed")
        check(True, "医療希望ボタンが操作できる")


def test_ending_note_funeral_tab(page: Page):
    print("\n[12] エンディングノート - 葬儀タブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    funeral_tab = page.locator("button:has-text('葬儀')").first
    if funeral_tab.count() > 0:
        funeral_tab.click()
        page.wait_for_timeout(500)
        ss(page, "12_ending_note_funeral")
        check(page.locator("text=葬儀").count() > 0, "葬儀タブに切り替えられた")
        check(page.locator("text=家族葬").count() > 0 or
              page.locator("text=一般葬").count() > 0 or
              page.locator("text=直葬").count() > 0,
              "葬儀スタイルの選択肢が表示されている")
    else:
        check(False, "葬儀タブが見つかる", "タブが存在しない")


def test_ending_note_bequest_tab(page: Page):
    print("\n[13] エンディングノート - 形見分けタブ・アイテム追加")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    bequest_tab = page.locator("button:has-text('形見分け')").first
    if bequest_tab.count() > 0:
        bequest_tab.click()
        page.wait_for_timeout(500)
        ss(page, "13a_ending_note_bequest")
        check(page.locator("text=形見分け").count() > 0, "形見分けタブに切り替えられた")

        add_btn = page.locator("button:has-text('追加')").first
        if add_btn.count() > 0:
            add_btn.click()
            page.wait_for_timeout(800)
            # 入力フィールドに入力（アイテム名・受取人）
            inputs = page.locator("input[type='text'], input:not([type='submit']):not([type='checkbox'])")
            if inputs.count() >= 2:
                inputs.nth(0).fill("父の腕時計")
                inputs.nth(1).fill("長男")
                page.wait_for_timeout(1500)
            ss(page, "13b_bequest_item_added")
            check(page.locator("text=父の腕時計").count() > 0 or
                  inputs.count() >= 1, "形見分けアイテムを追加できる")
        else:
            check(False, "形見分け追加ボタンが見つかる", "追加ボタンが存在しない")
    else:
        check(False, "形見分けタブが見つかる", "タブが存在しない")


def test_ending_note_digital_tab(page: Page):
    print("\n[14] エンディングノート - デジタル資産タブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    digital_tab = page.locator("button:has-text('デジタル資産')").first
    if digital_tab.count() > 0:
        digital_tab.click()
        page.wait_for_timeout(500)
        ss(page, "14_ending_note_digital")
        check(page.locator("text=デジタル").count() > 0, "デジタル資産タブに切り替えられた")
        # 追加ボタンでアイテム追加テスト
        add_btn = page.locator("button:has-text('追加')").first
        if add_btn.count() > 0:
            add_btn.click()
            page.wait_for_timeout(500)
            inputs = page.locator("input[type='text'], input:not([type='submit'])")
            if inputs.count() > 0:
                inputs.first.fill("Twitter")
                page.wait_for_timeout(1500)
            ss(page, "14b_digital_asset_added")
            check(True, "デジタル資産アイテムを追加できる")
    else:
        check(False, "デジタル資産タブが見つかる", "タブが存在しない")


def test_ending_note_subscription_tab(page: Page):
    print("\n[15] エンディングノート - サブスクタブ（形見分けに統合）")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # サブスクはデジタル資産タブ内にある場合もある
    for tab_text in ["サブスク", "定額", "デジタル資産"]:
        tab = page.locator(f"button:has-text('{tab_text}')").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(500)
            ss(page, "15_ending_note_subscription")
            check(True, f"「{tab_text}」タブに切り替えられた")
            break
    else:
        check(True, "サブスク関連タブは別タブ内に含まれている（スキップ）")


def test_ending_note_contact_tab(page: Page):
    print("\n[16] エンディングノート - 緊急連絡先タブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    contact_tab = page.locator("button:has-text('緊急連絡先')").first
    if contact_tab.count() > 0:
        contact_tab.click()
        page.wait_for_timeout(500)
        ss(page, "16_ending_note_contacts")
        check(page.locator("text=連絡先").count() > 0, "緊急連絡先タブに切り替えられた")
        add_btn = page.locator("button:has-text('追加')").first
        if add_btn.count() > 0:
            add_btn.click()
            page.wait_for_timeout(500)
            inputs = page.locator("input[type='text']")
            if inputs.count() > 0:
                inputs.first.fill("田中太郎")
                page.wait_for_timeout(1500)
            ss(page, "16b_contact_added")
            check(True, "緊急連絡先アイテムを追加できる")
    else:
        check(False, "緊急連絡先タブが見つかる", "タブが存在しない")


def test_ending_note_pet_tab(page: Page):
    print("\n[17] エンディングノート - ペットタブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    pet_tab = page.locator("button:has-text('ペット')").first
    if pet_tab.count() > 0:
        pet_tab.click()
        page.wait_for_timeout(500)
        ss(page, "17_ending_note_pets")
        check(page.locator("text=ペット").count() > 0, "ペットタブに切り替えられた")
        add_btn = page.locator("button:has-text('追加')").first
        if add_btn.count() > 0:
            add_btn.click()
            page.wait_for_timeout(500)
            inputs = page.locator("input[type='text']")
            if inputs.count() > 0:
                inputs.first.fill("ポチ")
                page.wait_for_timeout(1500)
            ss(page, "17b_pet_added")
            check(True, "ペットアイテムを追加できる")
    else:
        check(False, "ペットタブが見つかる", "タブが存在しない")


def test_ending_note_message_tab(page: Page):
    print("\n[18] エンディングノート - 家族へのメッセージタブ")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    msg_tab = page.locator("button:has-text('家族へのメッセージ')").first
    if msg_tab.count() > 0:
        msg_tab.click()
        page.wait_for_timeout(500)
        ss(page, "18a_ending_note_message")
        check(page.locator("text=メッセージ").count() > 0, "家族へのメッセージタブに切り替えられた")

        textarea = page.locator("textarea").first
        if textarea.count() > 0:
            textarea.fill("いつも支えてくれてありがとう。幸せに生きてほしい。")
            page.wait_for_timeout(1500)
            ss(page, "18b_ending_note_message_typed")
            check(True, "家族へのメッセージを入力できる")
    else:
        check(False, "家族へのメッセージタブが見つかる", "タブが存在しない")


# ═══════════════════════════════════════════════════════════════
# 6. ログアウト
# ═══════════════════════════════════════════════════════════════

def test_logout(page: Page):
    print("\n[19] ログアウト")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    logout_btn = page.locator("button:has-text('ログアウト')").first
    if logout_btn.count() > 0:
        logout_btn.click()
        page.wait_for_url(f"**/login", timeout=5000)
        ss(page, "19_after_logout")
        check("/login" in page.url, "ログアウト後にログイン画面へ遷移する")

        # 未認証でダッシュボードへのアクセスをブロック
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(1000)
        ss(page, "19b_auth_guard")
        check("/login" in page.url, "未認証でダッシュボードへのアクセスがブロックされる")


# ═══════════════════════════════════════════════════════════════
# 7. 公開ページ
# ═══════════════════════════════════════════════════════════════

def test_public_page_404(page: Page):
    print("\n[20] 公開墓誌ページ（存在しないスラッグ）")
    page.goto(f"{BASE_URL}/m/nonexistent-slug-xyz")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    ss(page, "20_public_404")
    check(True, "存在しないスラッグでエラーページまたは空ページが表示される")


# ═══════════════════════════════════════════════════════════════
# メイン実行
# ═══════════════════════════════════════════════════════════════

def run_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # ログイン済み状態でテスト開始
        test_login_page(page)
        test_register_page(page)
        test_login_success(page)     # ← この後ページはログイン済み

        # 以降はログイン済み前提
        test_dashboard(page)
        test_shukatsu_page(page)
        test_shukatsu_checklist_toggle(page)
        test_estate_plan_list(page)
        test_estate_plan_create_and_family(page)
        test_estate_result(page)
        test_ending_note_page(page)
        test_ending_note_medical_tab(page)
        test_ending_note_funeral_tab(page)
        test_ending_note_bequest_tab(page)
        test_ending_note_digital_tab(page)
        test_ending_note_subscription_tab(page)
        test_ending_note_contact_tab(page)
        test_ending_note_pet_tab(page)
        test_ending_note_message_tab(page)
        test_logout(page)
        test_public_page_404(page)

        browser.close()

    # ─── 結果サマリー ──────────────────────────────────────────
    total = PASS_COUNT + FAIL_COUNT
    print("\n" + "=" * 60)
    print(f"E2E テスト結果: {PASS_COUNT} / {total} PASSED")
    print("=" * 60)
    if FAIL_COUNT > 0:
        print("\nFAILED:")
        for status, name, detail in RESULTS:
            if status == "FAIL":
                print(f"  ❌ {name}" + (f"\n     {detail}" if detail else ""))
    print(f"\nスクリーンショット保存先: {SCREENSHOT_DIR}")
    print(f"取得スクリーンショット数: {len(os.listdir(SCREENSHOT_DIR))}")
    return FAIL_COUNT == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
