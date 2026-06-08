"""
ペルソナ型モニター E2Eスクリプト
各ペルソナのシナリオを実行し、スクリーンショットを保存する
"""
import os
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, expect

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"
SHOT_DIR = "/Users/user01/digital-memorial/docs/screenshots/persona-monitor"
DATE_STR = datetime.now().strftime("%Y%m%d")

TEST_EMAIL = "persona_test@example.com"
TEST_PASS = "TestPass123!"
TEST_NAME = "テスト太郎"

issues: list[dict] = []
bugs_fixed: list[dict] = []
_cached_token: str | None = None


def get_auth_token() -> str:
    """テストアカウントのJWTを取得（初回のみ登録・ログイン）"""
    global _cached_token
    if _cached_token:
        return _cached_token
    import requests
    try:
        requests.post(f"{API_URL}/api/auth/register", json={
            "email": TEST_EMAIL, "password": TEST_PASS, "name": TEST_NAME
        }, timeout=30)
    except Exception:
        pass
    resp = requests.post(f"{API_URL}/api/auth/login", data={
        "username": TEST_EMAIL, "password": TEST_PASS
    }, timeout=30)
    resp.raise_for_status()
    _cached_token = resp.json()["access_token"]
    return _cached_token


def shot(page: Page, persona: str, scenario: str, label: str):
    fname = f"{DATE_STR}-{persona}-{scenario}-{label}.png"
    path = os.path.join(SHOT_DIR, fname)
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {fname}")
    return fname


def log_issue(category: str, persona: str, content: str, priority: str = "Medium",
              background: str = "", recommendation: str = ""):
    issues.append({
        "category": category,
        "persona": persona,
        "content": content,
        "priority": priority,
        "background": background,
        "recommendation": recommendation,
    })
    print(f"  [{category}] {content}")


def log_bug(persona: str, scenario: str, description: str, fix: str, files: list[str]):
    bugs_fixed.append({
        "persona": persona,
        "scenario": scenario,
        "description": description,
        "fix": fix,
        "files": files,
    })
    print(f"  🐛 BUG FIXED: {description}")


def ensure_test_account(page: Page):
    """テストアカウントのJWTをlocalStorageにセットしてダッシュボードへ移動"""
    token = get_auth_token()
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate(f"localStorage.setItem('token', '{token}')")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_load_state("domcontentloaded")


# ─────────────────────────────────────────────────
# ペルソナ1: 初心者ユーザー
# ─────────────────────────────────────────────────
def persona1_beginner(page: Page):
    print("\n=== ペルソナ1: 初心者ユーザー ===")

    # シナリオ1-1: 新規登録フロー
    print("  シナリオ1-1: 新規登録")
    page.goto(f"{BASE_URL}/register")
    shot(page, "p1-beginner", "s1-register", "01-empty")

    # 「登録」ボタンのラベルを確認（作成/登録/Register いずれかあればOK）
    btn = page.locator('button[type="submit"]')
    btn_text = btn.inner_text()
    if not any(kw in btn_text for kw in ["登録", "作成", "Register", "Sign up"]):
        log_issue("B", "初心者", f"登録ボタンのテキストが不明瞭: '{btn_text}'", "Medium")

    # 空送信バリデーション
    btn.click()
    shot(page, "p1-beginner", "s1-register", "02-empty-submit")

    # パスワード強度ガイダンス確認
    pw = page.locator('input[type="password"]').first
    if pw.count() > 0:
        pw.fill("abc")
    shot(page, "p1-beginner", "s1-register", "03-weak-password")

    # シナリオ1-2: ログインフロー（初心者が間違えやすいポイント）
    print("  シナリオ1-2: ログイン")
    page.goto(f"{BASE_URL}/login")
    shot(page, "p1-beginner", "s1-login", "01-empty")

    # 誤パスワードのエラーメッセージ確認
    page.fill('input[type="email"]', TEST_EMAIL)
    page.fill('input[type="password"]', "wrongpassword")
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)
    shot(page, "p1-beginner", "s1-login", "02-wrong-password")

    # エラーメッセージが表示されているか確認
    body_text = page.inner_text("body")
    if "パスワード" not in body_text and "認証" not in body_text and "ログイン" not in body_text.split("ログイン")[1:]:
        log_issue("B", "初心者", "ログイン失敗時のエラーメッセージが不明確", "High",
                  "初心者が失敗原因を把握できない", "明確なエラーメッセージを表示する")

    # シナリオ1-3: 正常ログイン後のオンボーディング
    print("  シナリオ1-3: ログイン後オンボーディング")
    ensure_test_account(page)
    page.wait_for_timeout(1000)
    shot(page, "p1-beginner", "s1-dashboard", "01-after-login")

    # オンボーディングモーダルの存在確認
    # (localStorage.dm_onboarding_done をクリアしてリロード)
    page.evaluate("localStorage.removeItem('dm_onboarding_done')")
    page.reload()
    page.wait_for_timeout(1000)
    shot(page, "p1-beginner", "s1-dashboard", "02-onboarding-modal")

    # シナリオ1-4: 終活ノートへの導線
    print("  シナリオ1-4: 終活ノートへの導線")
    page.goto(f"{BASE_URL}/shukatsu")
    shot(page, "p1-beginner", "s1-shukatsu", "01-overview")

    # クイックリンクが分かりやすいか確認
    quick_links = page.locator("a").all()
    print(f"    リンク数: {len(quick_links)}")


# ─────────────────────────────────────────────────
# ペルソナ2: 日常利用ユーザー
# ─────────────────────────────────────────────────
def persona2_daily(page: Page):
    print("\n=== ペルソナ2: 日常利用ユーザー ===")
    ensure_test_account(page)

    # シナリオ2-1: エンディングノート編集の効率
    print("  シナリオ2-1: エンディングノート自動保存")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_timeout(1500)
    shot(page, "p2-daily", "s2-ending-note", "01-overview")

    # 自動保存インジケーターを確認
    page.wait_for_timeout(1000)
    body_text = page.inner_text("body")
    has_save_indicator = "保存" in body_text or "saved" in body_text.lower()
    if not has_save_indicator:
        log_issue("B", "日常利用", "自動保存状態インジケーターが見当たらない", "Medium")

    # 医療タブに切り替えてデータ入力
    medical_tab = page.locator("text=医療・介護").first
    medical_tab.click()
    page.wait_for_timeout(500)
    shot(page, "p2-daily", "s2-ending-note", "02-medical-tab")

    # シナリオ2-2: チェックリスト進捗確認
    print("  シナリオ2-2: チェックリスト進捗")
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_timeout(1500)
    shot(page, "p2-daily", "s2-checklist", "01-progress")

    # スコアカードが表示されているか
    score_visible = page.locator("text=終活準備スコア").count() > 0
    if not score_visible:
        log_issue("A", "日常利用", "終活スコアカードが表示されない", "High")

    # シナリオ2-3: デジタルキー設定の流れ
    print("  シナリオ2-3: デジタルキー設定")
    page.goto(f"{BASE_URL}/digital-key")
    page.wait_for_timeout(1500)
    shot(page, "p2-daily", "s2-digital-key", "01-overview")

    # 生存確認ボタンが操作しやすいか
    checkin_btn = page.locator("text=今日の生存確認").count()
    if checkin_btn == 0:
        # deadman が無効の場合はOK
        pass


# ─────────────────────────────────────────────────
# ペルソナ3: 急いでいるユーザー
# ─────────────────────────────────────────────────
def persona3_hurry(page: Page):
    print("\n=== ペルソナ3: 急いでいるユーザー ===")
    ensure_test_account(page)

    # シナリオ3-1: 墓誌作成の最短手順
    print("  シナリオ3-1: 墓誌作成最短フロー")
    page.goto(f"{BASE_URL}/memorials/new")
    page.wait_for_timeout(1000)
    shot(page, "p3-hurry", "s3-memorial-create", "01-form")

    # 必須項目だけ入力して保存できるか確認
    name_input = page.locator('input[name="name"], input[placeholder*="名前"], input[placeholder*="故人"]').first
    if name_input.count() > 0:
        name_input.fill("テスト故人")
        shot(page, "p3-hurry", "s3-memorial-create", "02-filled-minimum")

    # シナリオ3-2: 相続計算の最短フロー
    print("  シナリオ3-2: 相続計算最短フロー")
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_timeout(1500)
    shot(page, "p3-hurry", "s3-estate", "01-list")

    # シナリオ3-3: ナビゲーションの迷いやすさ
    print("  シナリオ3-3: ナビゲーション確認")
    # ダッシュボードから終活ノートへ
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1000)

    # 「終活ノートを開く」バナーが見えるか
    banner = page.locator("text=終活ノートを開く").count()
    if banner == 0:
        log_issue("B", "急いでいる", "ダッシュボードから終活ノートへの導線が不明瞭", "High")
    shot(page, "p3-hurry", "s3-navigation", "01-dashboard")

    # 各ページに戻るボタンがあるか確認
    pages_to_check = [
        ("/shukatsu", "終活ノート"),
        ("/ending-note", "エンディングノート"),
        ("/digital-key", "デジタルキー"),
        ("/settings/reminders", "リマインダー"),
    ]
    for path, name in pages_to_check:
        page.goto(f"{BASE_URL}{path}")
        page.wait_for_timeout(800)
        body = page.inner_text("body")
        has_back = "← " in body or "戻る" in body
        if not has_back:
            log_issue("B", "急いでいる", f"{name}ページに戻るリンクがない", "Medium")


# ─────────────────────────────────────────────────
# ペルソナ4: 境界値・異常系ユーザー
# ─────────────────────────────────────────────────
def persona4_edge(page: Page):
    print("\n=== ペルソナ4: 境界値・異常系ユーザー ===")
    ensure_test_account(page)

    # シナリオ4-1: エンディングノート長文入力
    print("  シナリオ4-1: 長文入力テスト")
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_timeout(1500)

    # 医療タブで長文入力
    page.locator("text=医療・介護").first.click()
    page.wait_for_timeout(500)

    long_text = "あ" * 5000
    textarea = page.locator("textarea").first
    if textarea.count() > 0:
        textarea.fill(long_text)
        page.wait_for_timeout(1500)  # 自動保存待ち
        shot(page, "p4-edge", "s4-long-text", "01-after-input")
        # エラーが出ないか確認
        error_visible = page.locator("text=エラー").count() > 0 or page.locator("text=error").count() > 0
        if error_visible:
            log_issue("A", "境界値", "長文入力でエラーが発生", "High")

    # シナリオ4-2: 存在しないページへのアクセス
    print("  シナリオ4-2: 404ページ確認")
    page.goto(f"{BASE_URL}/nonexistent-page-xyz")
    page.wait_for_timeout(1000)
    shot(page, "p4-edge", "s4-404", "01-not-found")

    # シナリオ4-3: 公開ページの不正アクセス
    print("  シナリオ4-3: 公開ページ不正slug")
    page.goto(f"{BASE_URL}/m/invalid-slug-xyz-123")
    page.wait_for_timeout(1500)
    shot(page, "p4-edge", "s4-public-invalid", "01-not-found")

    not_found_shown = "見つかりません" in page.inner_text("body") or "404" in page.inner_text("body")
    if not not_found_shown:
        log_issue("A", "境界値", "不正なslugで公開墓誌ページが適切なエラーを表示しない", "High")

    # シナリオ4-4: ログアウト後の認証ガード
    print("  シナリオ4-4: ログアウト後ガード")
    page.evaluate("localStorage.removeItem('token')")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1500)
    shot(page, "p4-edge", "s4-auth-guard", "01-redirect")
    # ログインページへリダイレクトされているか
    current_url = page.url
    if "login" not in current_url:
        log_issue("A", "境界値", "トークン削除後もダッシュボードにアクセスできる", "High",
                  "認証ガードが機能していない可能性", "フロントエンドのルートガードを確認する")

    # シナリオ4-5: 解除キーURLの不正トークン
    print("  シナリオ4-5: 不正な解除キーURL")
    page.goto(f"{BASE_URL}/unlock/99999?token=invalid-token")
    page.wait_for_timeout(1500)
    shot(page, "p4-edge", "s4-unlock-invalid", "01-error")


# ─────────────────────────────────────────────────
# ペルソナ5: アクセシビリティ重視ユーザー
# ─────────────────────────────────────────────────
def persona5_a11y(page: Page):
    print("\n=== ペルソナ5: アクセシビリティ重視ユーザー ===")

    # シナリオ5-1: ログインフォームのlabelチェック
    print("  シナリオ5-1: フォームラベル確認")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_timeout(800)

    # input要素のラベル確認
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        input_id = inp.get_attribute("id")
        input_type = inp.get_attribute("type")
        placeholder = inp.get_attribute("placeholder")
        aria_label = inp.get_attribute("aria-label")

        # idがあればlabelとの紐付きを確認
        has_label = False
        if input_id:
            label = page.locator(f'label[for="{input_id}"]').count()
            has_label = label > 0
        has_aria = aria_label is not None
        has_placeholder = placeholder is not None

        if not has_label and not has_aria and input_type not in ["submit", "button", "hidden"]:
            log_issue("B", "a11y", f"input[type={input_type}]にlabelまたはaria-labelがない(placeholder='{placeholder}')",
                      "Medium", "スクリーンリーダーで読み取れない可能性",
                      "label要素またはaria-labelを追加する")

    shot(page, "p5-a11y", "s5-login", "01-form-labels")

    # シナリオ5-2: キーボードナビゲーション
    print("  シナリオ5-2: キーボードナビゲーション")
    page.goto(f"{BASE_URL}/login")
    # Tabキーでフォーカス移動
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    shot(page, "p5-a11y", "s5-login", "02-keyboard-nav")

    # シナリオ5-3: ボタンにアイコンのみで文字がないものの確認
    print("  シナリオ5-3: アイコンのみボタン確認")
    ensure_test_account(page)
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1000)

    buttons = page.locator("button").all()
    icon_only_buttons = []
    for btn in buttons:
        text = btn.inner_text().strip()
        aria_label = btn.get_attribute("aria-label")
        title = btn.get_attribute("title")
        if len(text) <= 2 and not aria_label and not title:  # 絵文字のみ等
            icon_only_buttons.append(text)

    if icon_only_buttons:
        log_issue("B", "a11y", f"アイコンのみでaria-labelなしのボタンが{len(icon_only_buttons)}個ある: {icon_only_buttons[:3]}",
                  "Medium", "スクリーンリーダーでボタンの意味が伝わらない")

    shot(page, "p5-a11y", "s5-dashboard", "01-buttons")


# ─────────────────────────────────────────────────
# ペルソナ6: 管理者・運用担当者
# ─────────────────────────────────────────────────
def persona6_admin(page: Page):
    print("\n=== ペルソナ6: 管理者・運用担当者 ===")
    ensure_test_account(page)

    # シナリオ6-1: アカウント設定・危険操作の確認
    print("  シナリオ6-1: アカウント削除の確認ダイアログ")
    page.goto(f"{BASE_URL}/account")
    page.wait_for_timeout(1000)
    shot(page, "p6-admin", "s6-account", "01-overview")

    # 退会ボタンに確認ステップがあるか
    delete_btn = page.locator("text=アカウントを削除する").first
    if delete_btn.count() > 0:
        delete_btn.click()
        page.wait_for_timeout(500)
        shot(page, "p6-admin", "s6-account", "02-delete-confirm")
        # パスワード入力が必要か確認
        pw_input = page.locator('input[type="password"]').count()
        if pw_input == 0:
            log_issue("A", "管理者", "アカウント削除に再認証（パスワード入力）がない", "High",
                      "誤操作でアカウント削除される危険", "必ずパスワード確認を求める")

    # シナリオ6-2: 活動ログ確認
    print("  シナリオ6-2: 活動ログ")
    page.goto(f"{BASE_URL}/account")
    page.wait_for_timeout(500)
    log_btn = page.locator("text=活動ログを表示する").first
    if log_btn.count() > 0:
        log_btn.click()
        page.wait_for_timeout(1500)
        shot(page, "p6-admin", "s6-activity-log", "01-log-displayed")

    # シナリオ6-3: データエクスポートの動作
    print("  シナリオ6-3: データエクスポート")
    shot(page, "p6-admin", "s6-export", "01-buttons")

    # シナリオ6-4: 2FA設定フロー確認（危険操作保護）
    print("  シナリオ6-4: 2FA設定")
    totp_btn = page.locator("text=2段階認証を設定する").first
    if totp_btn.count() > 0:
        shot(page, "p6-admin", "s6-2fa", "01-setup-available")


def main():
    os.makedirs(SHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        try:
            persona1_beginner(page)
            persona2_daily(page)
            persona3_hurry(page)
            persona4_edge(page)
            persona5_a11y(page)
            persona6_admin(page)
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

    print("\n" + "="*60)
    print(f"📊 発見した課題: {len(issues)}件")
    for i, issue in enumerate(issues, 1):
        print(f"  [{i}] [{issue['category']}] {issue['persona']}: {issue['content']}")

    return issues, bugs_fixed


if __name__ == "__main__":
    issues_found, bugs = main()
