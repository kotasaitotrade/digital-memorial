"""
全画面スクリーンショット取得スクリプト（仕様書用）
実際のコンポーネントの正確なセレクターを使用
"""
import os, time
import requests
from playwright.sync_api import sync_playwright, Page

BASE_URL = "http://localhost:5173"
API_URL  = "http://localhost:8000/api"
SS_DIR   = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SS_DIR, exist_ok=True)

# 毎回フレッシュなユーザーを使うことでデータの蓄積を防ぐ
_TS          = int(time.time())
TEST_EMAIL    = f"spec_{_TS}@example.com"
TEST_PASSWORD = "spectest123"
TEST_NAME     = "佐藤 恵子"

def ss(page: Page, name: str, full: bool = True):
    path = os.path.join(SS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  📸 {name}.png")

def api_token():
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
    """オンボーディングモーダルを閉じる"""
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

# ─────────────────────────────────────────────────────────────
# S01: ログインページ
# ─────────────────────────────────────────────────────────────
def s01_login(page: Page):
    print("\n[S01] ログインページ")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    ss(page, "s01a_login")

    # エラー表示
    page.locator("input[type='email']").fill("wrong@example.com")
    page.locator("input[type='password']").fill("badpass")
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(1800)
    ss(page, "s01b_login_error")

# ─────────────────────────────────────────────────────────────
# S02: ユーザー登録ページ
# ─────────────────────────────────────────────────────────────
def s02_register(page: Page):
    print("\n[S02] ユーザー登録ページ")
    page.goto(f"{BASE_URL}/register")
    page.wait_for_load_state("networkidle")
    ss(page, "s02a_register")

    # 入力済み状態（placeholderから特定）
    page.locator("input[placeholder='山田 花子']").fill("佐藤 恵子")
    page.locator("input[type='email']").fill("sato.keiko@example.com")
    page.locator("input[type='password']").fill("password123")
    ss(page, "s02b_register_filled")

# ─────────────────────────────────────────────────────────────
# S03: ダッシュボード（墓誌一覧）
# ─────────────────────────────────────────────────────────────
def s03_dashboard(page: Page, token: str):
    print("\n[S03] ダッシュボード")
    ensure_login(page)
    # まず空の状態
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    ss(page, "s03a_dashboard_empty")

    # 墓誌を作成
    h = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{API_URL}/memorials", headers=h, json={
        "name": "田中 正雄",
        "birth_date": "1938-05-22",
        "death_date": "2024-03-08",
        "biography": "大阪府生まれ。中学校の教師として38年間勤務。書道と囲碁を愛した。",
        "slug": f"tanaka-masao-{_TS}"
    })
    if res.status_code in (200, 201):
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        ss(page, "s03b_dashboard_memorial")

        # QRモーダル
        qr_btn = page.locator("button:has-text('QR')").first
        if qr_btn.count() > 0:
            qr_btn.click()
            page.wait_for_timeout(800)
            ss(page, "s03c_dashboard_qr_modal")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

# ─────────────────────────────────────────────────────────────
# S04: 墓誌作成フォーム
# ─────────────────────────────────────────────────────────────
def s04_memorial_new(page: Page):
    print("\n[S04] 墓誌作成フォーム")
    ensure_login(page)
    page.goto(f"{BASE_URL}/memorials/new")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    ss(page, "s04a_memorial_form_empty")

    # フォーム入力（date は type="text" + placeholder）
    page.locator("input[placeholder='例：山田 太郎']").fill("田中 花子")
    page.locator("input[placeholder='例：1930年5月3日']").fill("1955年6月20日")
    page.locator("input[placeholder='例：2020年10月15日']").fill("2023年11月5日")
    page.locator("textarea[placeholder='故人の人生・エピソードをご記入ください']").fill(
        "愛知県出身。中学校教師として30年間子供たちを育てた。趣味は俳句と園芸。"
    )
    ss(page, "s04b_memorial_form_filled")

# ─────────────────────────────────────────────────────────────
# S05: 墓誌編集フォーム
# ─────────────────────────────────────────────────────────────
def s05_memorial_edit(page: Page, token: str):
    print("\n[S05] 墓誌編集フォーム")
    h = {"Authorization": f"Bearer {token}"}
    memorials = requests.get(f"{API_URL}/memorials", headers=h).json()
    if not memorials:
        print("  ⚠ 墓誌なし。スキップ")
        return
    mid = memorials[0]["id"]
    ensure_login(page)
    page.goto(f"{BASE_URL}/memorials/{mid}/edit")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    ss(page, "s05a_memorial_edit")

    # 写真アップロードエリアまでスクロール
    page.evaluate("window.scrollTo(0, 400)")
    page.wait_for_timeout(400)
    ss(page, "s05b_memorial_edit_photo")

# ─────────────────────────────────────────────────────────────
# S06: QR印刷ページ
# ─────────────────────────────────────────────────────────────
def s06_print_qr(page: Page, token: str):
    print("\n[S06] QR印刷ページ")
    h = {"Authorization": f"Bearer {token}"}
    memorials = requests.get(f"{API_URL}/memorials", headers=h).json()
    if not memorials:
        print("  ⚠ 墓誌なし。スキップ")
        return
    mid = memorials[0]["id"]
    ensure_login(page)
    page.goto(f"{BASE_URL}/memorials/{mid}/print-qr")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ss(page, "s06_print_qr")

# ─────────────────────────────────────────────────────────────
# S07: 公開墓誌ページ（/m/:slug）
# ─────────────────────────────────────────────────────────────
def s07_public_memorial(page: Page, token: str):
    print("\n[S07] 公開墓誌ページ")
    h = {"Authorization": f"Bearer {token}"}
    memorials = requests.get(f"{API_URL}/memorials", headers=h).json()
    if not memorials:
        print("  ⚠ 墓誌なし。スキップ")
        return
    slug = memorials[0].get("slug")
    if not slug:
        print("  ⚠ slugなし。スキップ")
        return
    # 未ログイン状態で公開ページを確認（別コンテキストを使う）
    page.goto(f"{BASE_URL}/m/{slug}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ss(page, "s07a_public_memorial_top")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(400)
    ss(page, "s07b_public_memorial_bottom")

# ─────────────────────────────────────────────────────────────
# S08: 終活ダッシュボード＋チェックリスト全カテゴリ
# ─────────────────────────────────────────────────────────────
def s08_shukatsu(page: Page):
    print("\n[S08] 終活ダッシュボード")
    ensure_login(page)
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # スコアカード部分のみ（viewport内）
    ss(page, "s08a_shukatsu_scorecard", full=False)
    # 全体
    ss(page, "s08b_shukatsu_full")

    # チェックリスト - カテゴリタブを順番に撮影
    cats = ["すべて", "相続", "遺言", "医療", "葬儀", "デジタル", "人間関係", "ペット", "思い出"]
    for cat in cats:
        tab = page.locator(f"button:has-text('{cat}')").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(500)
            ss(page, f"s08c_checklist_{cat}")

# ─────────────────────────────────────────────────────────────
# S09: 相続計画一覧
# ─────────────────────────────────────────────────────────────
def s09_estate_list(page: Page):
    print("\n[S09] 相続計画一覧")
    ensure_login(page)
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    ss(page, "s09a_estate_list")

    # 新規作成フォームを展開
    page.locator("button:has-text('＋ 新規作成')").click()
    page.wait_for_timeout(400)
    ss(page, "s09b_estate_create_form")
    page.locator("button:has-text('キャンセル')").click()

# ─────────────────────────────────────────────────────────────
# S10: 家族構成入力
# ─────────────────────────────────────────────────────────────
def s10_family_input(page: Page, token: str) -> int:
    print("\n[S10] 家族構成入力")
    h = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{API_URL}/estate-plans",
        json={"title": "仕様書テスト計画"}, headers=h)
    plan_id = res.json()["id"]

    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/family")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    ss(page, "s10a_family_empty")

    # 配偶者追加
    page.locator("button:has-text('＋ 配偶者を追加')").click()
    page.wait_for_timeout(400)
    page.locator("input[placeholder='名前']").first.fill("花子")
    ss(page, "s10b_family_spouse_added")

    # 子ども追加
    page.locator("button:has-text('＋ 子どもを追加')").click()
    page.wait_for_timeout(300)
    page.locator("input[placeholder='名前']").nth(1).fill("一郎")
    page.locator("button:has-text('＋ 子どもを追加')").click()
    page.wait_for_timeout(300)
    page.locator("input[placeholder='名前']").nth(2).fill("二郎")
    ss(page, "s10c_family_children_added")

    return plan_id

# ─────────────────────────────────────────────────────────────
# S11: 財産入力
# ─────────────────────────────────────────────────────────────
def s11_asset_input(page: Page, token: str, plan_id: int):
    print("\n[S11] 財産入力")
    h = {"Authorization": f"Bearer {token}"}
    # 家族データを保存してから資産ページへ
    requests.post(f"{API_URL}/estate-plans/{plan_id}/family", headers=h, json={
        "members": [
            {"name": "花子", "relationship": "spouse"},
            {"name": "一郎", "relationship": "child"},
            {"name": "二郎", "relationship": "child"},
        ]
    })

    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/assets")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    ss(page, "s11a_asset_empty")

    # 不動産を追加
    page.locator("button:has-text('＋ 不動産を追加')").click()
    page.wait_for_timeout(300)
    page.locator("input[placeholder='名称（例：自宅）']").first.fill("自宅（〇〇市△△町）")
    page.locator("input[placeholder='金額（円）']").first.fill("50000000")
    ss(page, "s11b_asset_realestate_added")

    # 預貯金を追加
    page.locator("button:has-text('＋ 預貯金を追加')").click()
    page.wait_for_timeout(300)
    page.locator("input[placeholder='名称（例：自宅）']").nth(1).fill("〇〇銀行 普通預金")
    page.locator("input[placeholder='金額（円）']").nth(1).fill("20000000")
    ss(page, "s11c_asset_bank_added")

    # 負債を追加
    page.locator("button:has-text('＋ 負債を追加')").click()
    page.wait_for_timeout(300)
    ss(page, "s11d_asset_debt_added")

    # 合計欄まで全体撮影
    ss(page, "s11e_asset_full")

# ─────────────────────────────────────────────────────────────
# S12: 相続計算結果
# ─────────────────────────────────────────────────────────────
def s12_estate_result(page: Page, token: str, plan_id: int):
    print("\n[S12] 相続計算結果")
    h = {"Authorization": f"Bearer {token}"}
    requests.post(f"{API_URL}/estate-plans/{plan_id}/assets", headers=h, json={
        "assets": [
            {"name": "自宅不動産", "asset_type": "real_estate",    "estimated_value": 50_000_000},
            {"name": "預貯金",     "asset_type": "bank_account",   "estimated_value": 20_000_000},
            {"name": "有価証券",   "asset_type": "securities",     "estimated_value": 10_000_000},
            {"name": "生命保険金", "asset_type": "life_insurance", "estimated_value":  5_000_000, "is_deemed_estate": True},
            {"name": "住宅ローン", "asset_type": "debt",           "estimated_value":  8_000_000},
        ]
    })

    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/result")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    ss(page, "s12a_result_top", full=False)
    ss(page, "s12b_result_full")

    # 下部（遺留分・基礎控除）
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(400)
    ss(page, "s12c_result_bottom", full=False)

# ─────────────────────────────────────────────────────────────
# S13: エンディングノート - 医療・介護
# ─────────────────────────────────────────────────────────────
def s13_ending_medical(page: Page):
    print("\n[S13] エンディングノート - 医療・介護")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ss(page, "s13a_medical_default")

    # RadioGroup は <label> 要素（radio input は hidden）
    # 延命治療「希望しない」選択
    page.locator("label:has-text('希望しない')").first.click()
    page.wait_for_timeout(800)
    # 心肺蘇生「希望しない」
    page.locator("label:has-text('希望しない')").nth(1).click()
    page.wait_for_timeout(800)
    # 臓器提供「提供する」
    page.locator("label:has-text('提供する')").first.click()
    page.wait_for_timeout(800)
    # かかりつけ医入力
    page.locator("textarea[placeholder='医師名・病院名・電話番号']").fill(
        "〇〇病院 田中先生（03-xxxx-xxxx）")
    page.locator("textarea[placeholder='薬の名前・用量・処方医']").fill(
        "リバーロキサバン 15mg 朝1錠")
    page.wait_for_timeout(1200)
    ss(page, "s13b_medical_filled")

# ─────────────────────────────────────────────────────────────
# S14: エンディングノート - 葬儀
# ─────────────────────────────────────────────────────────────
def s14_ending_funeral(page: Page):
    print("\n[S14] エンディングノート - 葬儀")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('葬儀')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s14a_funeral_default")

    page.locator("label:has-text('家族葬')").first.click()
    page.wait_for_timeout(500)
    page.locator("input[placeholder='例：仏教（浄土宗）、無宗教など']").fill("仏教（曹洞宗）")
    page.locator("textarea[placeholder='曲名・アーティスト名など']").fill(
        "サザンオールスターズ「真夏の果実」")
    page.wait_for_timeout(1000)
    ss(page, "s14b_funeral_filled")

# ─────────────────────────────────────────────────────────────
# S15: エンディングノート - 形見分け
# ─────────────────────────────────────────────────────────────
def s15_ending_bequest(page: Page):
    print("\n[S15] エンディングノート - 形見分け")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('形見分け')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s15a_bequest_empty")

    # アイテム入力フォーム
    page.locator("input[placeholder='物品名（例：父の形見の時計）']").fill("父の懐中時計")
    page.locator("input[placeholder='渡す相手の名前']").fill("長男 一郎")
    page.locator("input[placeholder='備考（任意）']").fill("明治時代の骨董品")
    ss(page, "s15b_bequest_form_filled")

    page.locator("button:has-text('追加')").first.click()
    page.wait_for_timeout(1000)
    ss(page, "s15c_bequest_item_saved")

    # 2件目追加
    page.locator("input[placeholder='物品名（例：父の形見の時計）']").fill("母の着物（振袖）")
    page.locator("input[placeholder='渡す相手の名前']").fill("長女 花子")
    page.locator("button:has-text('追加')").first.click()
    page.wait_for_timeout(1000)
    ss(page, "s15d_bequest_two_items")

# ─────────────────────────────────────────────────────────────
# S16: エンディングノート - デジタル資産
# ─────────────────────────────────────────────────────────────
def s16_ending_digital(page: Page):
    print("\n[S16] エンディングノート - デジタル資産")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('デジタル資産')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s16a_digital_empty")

    # デジタル資産追加フォームを確認する（DigitalSectionの先頭部分を撮影）
    # サービス名・アカウント・死後の処理
    svc_inputs = page.locator("input[placeholder='サービス名（例：Amazon, Gmail）'], input[placeholder*='サービス名']")
    if svc_inputs.count() > 0:
        svc_inputs.first.fill("Amazon")
    else:
        # フォームがある最初のinputに入力
        page.locator("input").first.fill("Amazon")
    page.wait_for_timeout(500)

    # 追加ボタン
    add_btn = page.locator("button:has-text('追加')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(1000)
        ss(page, "s16b_digital_saved")

    # 下部のサブスクリプションフォーム
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    ss(page, "s16c_digital_subscription_area")

# ─────────────────────────────────────────────────────────────
# S17: エンディングノート - 緊急連絡先
# ─────────────────────────────────────────────────────────────
def s17_ending_contacts(page: Page):
    print("\n[S17] エンディングノート - 緊急連絡先")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('緊急連絡先')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s17a_contacts_empty")

    # 連絡先フォームを探して入力
    name_input = page.locator("input[placeholder*='名前'], input[placeholder*='氏名']").first
    if name_input.count() > 0:
        name_input.fill("鈴木 雄介")
    # 続柄
    rel_input = page.locator("input[placeholder*='続柄'], input[placeholder*='関係']").first
    if rel_input.count() > 0:
        rel_input.fill("長男")
    # 電話番号
    tel_input = page.locator("input[placeholder*='電話'], input[type='tel']").first
    if tel_input.count() > 0:
        tel_input.fill("090-1234-5678")
    ss(page, "s17b_contact_form_filled")

    add_btn = page.locator("button:has-text('追加')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(1000)
        ss(page, "s17c_contact_saved")

# ─────────────────────────────────────────────────────────────
# S18: エンディングノート - ペット
# ─────────────────────────────────────────────────────────────
def s18_ending_pets(page: Page):
    print("\n[S18] エンディングノート - ペット")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('ペット')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s18a_pets_empty")

    # ペット名を入力
    name_input = page.locator("input[placeholder*='名前']").first
    if name_input.count() > 0:
        name_input.fill("ポチ")
    species_input = page.locator("input[placeholder*='種類'], input[placeholder*='品種']").first
    if species_input.count() > 0:
        species_input.fill("柴犬")
    caretaker_input = page.locator("input[placeholder*='世話'], input[placeholder*='預け先']").first
    if caretaker_input.count() > 0:
        caretaker_input.fill("長男 一郎")
    ss(page, "s18b_pet_form_filled")

    add_btn = page.locator("button:has-text('追加')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(1000)
        ss(page, "s18c_pet_saved")

# ─────────────────────────────────────────────────────────────
# S19: エンディングノート - 家族へのメッセージ
# ─────────────────────────────────────────────────────────────
def s19_ending_message(page: Page):
    print("\n[S19] エンディングノート - 家族へのメッセージ")
    ensure_login(page)
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("button:has-text('家族へのメッセージ')").first.click()
    page.wait_for_timeout(800)
    ss(page, "s19a_message_empty")

    # メッセージ入力
    textarea = page.locator("textarea").first
    if textarea.count() > 0:
        textarea.fill(
            "家族のみなさんへ\n\n"
            "長い間、本当にありがとう。皆のおかげで幸せな人生を歩めました。\n"
            "これからも家族仲良く、助け合って生きてください。\n\n"
            "愛を込めて"
        )
        page.wait_for_timeout(1200)  # 自動保存を待つ
        ss(page, "s19b_message_typed")

# ─────────────────────────────────────────────────────────────
# S20: 認証ガード・ログアウト
# ─────────────────────────────────────────────────────────────
def s21_will_simulator(page: Page, token: str, plan_id: int):
    print("\n[S21] 遺言書シミュレーター")
    ensure_login(page)
    page.goto(f"{BASE_URL}/estate/{plan_id}/will")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    ss(page, "s21a_will_default")

    # 希望配分を変更（最初の相続人に遺産の6割）
    inputs = page.locator("input[type='number']")
    if inputs.count() > 0:
        first_val = inputs.first.input_value()
        try:
            inputs.first.fill(str(int(float(first_val or "0") * 1.2)))
        except Exception:
            pass
        page.wait_for_timeout(800)
    ss(page, "s21b_will_modified")

    # 付言事項を記入
    memo_area = page.locator("textarea").first
    if memo_area.count() > 0:
        memo_area.fill("家族への感謝を込めて、この遺言書を記します。どうか仲良く過ごしてください。")
        page.wait_for_timeout(600)
    ss(page, "s21c_will_memo")


def s20_auth_guard(page: Page):
    print("\n[S20] 認証ガード・ログアウト")
    ensure_login(page)
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("networkidle")

    logout_btn = page.locator("button:has-text('ログアウト')").first
    if logout_btn.count() > 0:
        logout_btn.click()
        page.wait_for_timeout(1500)
        ss(page, "s20a_after_logout")

    # 未認証でダッシュボードアクセス
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1500)
    ss(page, "s20b_auth_redirect")

    # 未認証で終活ページアクセス
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_timeout(1500)
    ss(page, "s20c_shukatsu_redirect")

# ─────────────────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("全画面スクリーンショット取得（仕様書用）")
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

        # 最初にUIでログイン
        requests.post(f"{API_URL}/auth/register",
            json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
        login_ui(page)

        # 各画面を順番に撮影
        s01_login(page)
        s02_register(page)
        s03_dashboard(page, token)
        s04_memorial_new(page)
        s05_memorial_edit(page, token)
        s06_print_qr(page, token)
        s07_public_memorial(page, token)
        s08_shukatsu(page)
        s09_estate_list(page)
        plan_id = s10_family_input(page, token)
        s11_asset_input(page, token, plan_id)
        s12_estate_result(page, token, plan_id)
        s21_will_simulator(page, token, plan_id)
        s13_ending_medical(page)
        s14_ending_funeral(page)
        s15_ending_bequest(page)
        s16_ending_digital(page)
        s17_ending_contacts(page)
        s18_ending_pets(page)
        s19_ending_message(page)
        s20_auth_guard(page)

        # ── S16: デジタル遺品鍵 ──────────────────────────────
        ensure_login(page)
        page.goto(f"{BASE_URL}/digital-key")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        ss(page, "s16a_digital_key_empty")

        # 信頼者を追加
        try:
            page.click("button:has-text('+ 追加'), button:has-text('追加')")
            page.wait_for_timeout(500)
            name_input = page.locator("input[placeholder*='名前'], input[placeholder*='太郎']").first
            email_input = page.locator("input[type='email']").first
            if name_input.count() > 0:
                name_input.fill("山田 一郎")
                email_input.fill("ichiro@example.com")
                page.click("button:has-text('登録')")
                page.wait_for_timeout(1000)
                ss(page, "s16b_digital_key_added")
                # トークン表示
                page.click("button:has-text('解除キーURL'), button:has-text('URLを表示')")
                page.wait_for_timeout(500)
                ss(page, "s16c_digital_key_token")
        except Exception:
            ss(page, "s16b_digital_key_added")
            ss(page, "s16c_digital_key_token")

        # ── S17: リマインダー設定 ────────────────────────────
        page.goto(f"{BASE_URL}/settings/reminders")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        ss(page, "s17a_reminder_on")

        try:
            page.select_option("select", "4")
            page.wait_for_timeout(500)
            ss(page, "s17b_reminder_month")
            # 通知OFF
            page.click("div[style*='cursor: pointer']")
            page.wait_for_timeout(500)
            ss(page, "s17c_reminder_off")
        except Exception:
            ss(page, "s17b_reminder_month")
            ss(page, "s17c_reminder_off")

        # ── S18: エンディングノート — 追悼メッセージ ─────────
        page.goto(f"{BASE_URL}/ending-note")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        try:
            page.click("button:has-text('追悼メッセージ')")
            page.wait_for_timeout(500)
            ss(page, "s18a_scheduled_msg_empty")
            page.click("button:has-text('+ メッセージを追加')")
            page.wait_for_timeout(500)
            ss(page, "s18b_scheduled_msg_form")
            inputs = page.locator("input").all()
            for i, inp in enumerate(inputs[:2]):
                inp.fill(["山田 太郎", "taro@example.com"][i])
            page.locator("input[placeholder*='件名']").fill("最後のメッセージ")
            page.locator("textarea").last.fill("ありがとう。")
            page.wait_for_timeout(500)
            page.click("button:has-text('保存')")
            page.wait_for_timeout(1000)
            ss(page, "s18c_scheduled_msg_created")
        except Exception:
            ss(page, "s18b_scheduled_msg_form")
            ss(page, "s18c_scheduled_msg_created")

        # ── S19: エンディングノート — ビデオメッセージ ────────
        page.goto(f"{BASE_URL}/ending-note")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        try:
            page.click("button:has-text('ビデオメッセージ')")
            page.wait_for_timeout(500)
            ss(page, "s19a_video_empty")
            page.locator("input[placeholder*='タイトル']").fill("家族へのメッセージ")
            page.wait_for_timeout(500)
            ss(page, "s19b_video_form")
        except Exception:
            ss(page, "s19a_video_empty")
            ss(page, "s19b_video_form")

        # ── S20: 遺言書シミュレーター — テキストプレビュー ────
        # 相続計画が既存の場合のみ
        plans_resp = page.evaluate("""
            async () => {
                const r = await fetch('/api/estate-plans', {headers: {'Authorization': 'Bearer ' + localStorage.getItem('dm_token')}});
                return r.json();
            }
        """)
        if isinstance(plans_resp, list) and len(plans_resp) > 0:
            plan_id = plans_resp[0]['id']
            page.goto(f"{BASE_URL}/estate/{plan_id}/will")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            try:
                page.click("button:has-text('プレビュー'), button:has-text('テキスト')")
                page.wait_for_timeout(1000)
                ss(page, "s20a_will_preview")
            except Exception:
                ss(page, "s20a_will_preview")
            # スクロールして法的案内
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)
            ss(page, "s20b_will_legal")

        browser.close()

    # 撮影結果一覧
    files = sorted(f for f in os.listdir(SS_DIR) if f.startswith("s") and f.endswith(".png"))
    print("\n" + "=" * 60)
    print(f"撮影完了: {len(files)} 枚")
    for f in files:
        sz = os.path.getsize(os.path.join(SS_DIR, f)) // 1024
        print(f"  {f}  ({sz} KB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
