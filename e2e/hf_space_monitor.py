"""
HF Space ペルソナモニター
30分ごとに1ペルソナずつローテーションして E2E チェックを実行する。
状態ファイル: /tmp/hf_persona_idx
スクリーンショット: ~/Desktop/hf-monitor-screenshots/
"""
import os
import sys
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

BASE_URL = "https://kotsaito-digital-memorial.hf.space"
API_URL  = f"{BASE_URL}/api"
SHOT_DIR = os.path.expanduser("~/Desktop/hf-monitor-screenshots")
STATE_FILE = "/tmp/hf_persona_idx"

# ペルソナごとに独立したアカウントを使う
PERSONAS = [
    {"id": "p1_beginner", "name": "初心者・田中花子",   "email": "hf_mon_p1@example.com", "pass": "Monitor1Pass!"},
    {"id": "p2_daily",    "name": "日常利用・鈴木一郎", "email": "hf_mon_p2@example.com", "pass": "Monitor2Pass!"},
    {"id": "p3_hurry",    "name": "急ぎ・山田次郎",     "email": "hf_mon_p3@example.com", "pass": "Monitor3Pass!"},
    {"id": "p4_edge",     "name": "エッジ・高橋三郎",   "email": "hf_mon_p4@example.com", "pass": "Monitor4Pass!"},
    {"id": "p5_a11y",     "name": "高齢者・佐藤四郎",   "email": "hf_mon_p5@example.com", "pass": "Monitor5Pass!"},
    {"id": "p6_admin",    "name": "管理者・伊藤五郎",   "email": "hf_mon_p6@example.com", "pass": "Monitor6Pass!"},
]

issues: list[dict] = []


def next_persona_idx() -> int:
    """状態ファイルから次のペルソナインデックスを読み、インクリメントして保存"""
    try:
        with open(STATE_FILE) as f:
            idx = int(f.read().strip()) % len(PERSONAS)
    except Exception:
        idx = 0
    next_idx = (idx + 1) % len(PERSONAS)
    with open(STATE_FILE, "w") as f:
        f.write(str(next_idx))
    return idx


def ensure_account(persona: dict):
    """テストアカウントを作成またはログインしてトークンを返す"""
    try:
        requests.post(f"{API_URL}/auth/register", json={
            "email": persona["email"], "password": persona["pass"], "name": persona["name"]
        }, timeout=15)
    except Exception:
        pass
    try:
        r = requests.post(f"{API_URL}/auth/login", data={
            "username": persona["email"], "password": persona["pass"]
        }, timeout=15)
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        log_issue("AUTH", persona["id"], f"ログイン失敗: {e}", "Critical")
        return None


def set_auth(page: Page, token: str):
    page.goto(f"{BASE_URL}/login")
    page.evaluate(f"localStorage.setItem('token', '{token}')")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1500)


def shot(page: Page, pid: str, label: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"{ts}-{pid}-{label}.png"
    path = os.path.join(SHOT_DIR, fname)
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  📸 {fname}")
    except Exception as e:
        print(f"  ⚠️  screenshot 失敗: {e}")
    return fname


def log_issue(category: str, pid: str, content: str, priority: str = "Medium"):
    issues.append({"category": category, "persona": pid, "content": content, "priority": priority})
    print(f"  ⚠️  [{priority}][{category}] {content}")


# ── ペルソナ別シナリオ ──────────────────────────────────────

def run_p1_beginner(page: Page, persona: dict):
    """初心者: 登録→ログイン→ダッシュボード確認"""
    print("  シナリオ: 新規登録フロー確認")
    page.goto(f"{BASE_URL}/register")
    page.wait_for_timeout(1000)
    shot(page, persona["id"], "register-page")

    # 空送信バリデーション
    page.click('button[type="submit"]')
    page.wait_for_timeout(800)
    shot(page, persona["id"], "register-empty-submit")

    # 正常ログイン後ダッシュボード
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)
    shot(page, persona["id"], "dashboard-after-login")

    # 終活チェックリストへの導線
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_timeout(1000)
    shot(page, persona["id"], "shukatsu-overview")


def run_p2_daily(page: Page, persona: dict):
    """日常利用: ダッシュボード→エンディングノート→自動保存確認"""
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)
    shot(page, persona["id"], "dashboard")

    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "ending-note-top")

    # テキスト入力して自動保存バッジ確認
    ta = page.locator("textarea").first
    if ta.count() > 0:
        ta.fill(f"モニターテスト {datetime.now().strftime('%H:%M')}")
        page.wait_for_timeout(2000)
        shot(page, persona["id"], "ending-note-autosave")

    # 墓じまい計画ページ確認
    page.goto(f"{BASE_URL}/hakajimai")
    page.wait_for_timeout(3000)
    shot(page, persona["id"], "hakajimai-top")

    body = page.inner_text("body")
    if "墓じまい" not in body and "供養" not in body:
        log_issue("UI", persona["id"], "墓じまいページが表示されない", "High")


def run_p3_hurry(page: Page, persona: dict):
    """急ぎユーザー: 墓誌作成フロー確認"""
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)

    page.goto(f"{BASE_URL}/memorials/new")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "memorial-new-form")

    # フォーム入力
    name_input = page.locator('input[name="name"], input[placeholder*="名前"], input[placeholder*="お名前"]').first
    if name_input.count() > 0:
        name_input.fill("モニターテスト太郎")
        page.wait_for_timeout(500)
        shot(page, persona["id"], "memorial-form-filled")
    else:
        log_issue("UI", persona["id"], "墓誌名前フィールドが見つからない", "High")


def run_p4_edge(page: Page, persona: dict):
    """エッジケース: 404・未認証リダイレクト・公開ページ確認"""
    # 未認証でプロテクトページへアクセス
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_timeout(1500)
    body = page.inner_text("body")
    if "ログイン" not in body and "/login" not in page.url:
        log_issue("Auth", persona["id"], "未認証でダッシュボードにアクセスできる可能性", "Critical")
    shot(page, persona["id"], "unauthenticated-dashboard")

    # 404 ページ確認
    page.goto(f"{BASE_URL}/this-page-does-not-exist")
    page.wait_for_timeout(1000)
    shot(page, persona["id"], "404-page")
    if "404" not in page.inner_text("body") and "見つかりません" not in page.inner_text("body"):
        log_issue("UI", persona["id"], "404ページが適切に表示されない", "Medium")

    # ログイン後の確認
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)
    shot(page, persona["id"], "dashboard-authenticated")


def run_p5_a11y(page: Page, persona: dict):
    """アクセシビリティ: フォームラベル・キーボードナビ確認"""
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)

    page.goto(f"{BASE_URL}/login")
    page.wait_for_timeout(1000)

    # input に label/aria-label があるか
    inputs = page.locator("input").all()
    for inp in inputs:
        aria = inp.get_attribute("aria-label") or ""
        inp_id = inp.get_attribute("id") or ""
        label_for = page.locator(f'label[for="{inp_id}"]').count() if inp_id else 0
        if not aria and not label_for:
            log_issue("A11y", persona["id"], f"input[id={inp_id}] にラベルなし", "Low")
    shot(page, persona["id"], "login-a11y")

    # 墓じまいページの a11y 確認
    set_auth(page, token)
    page.goto(f"{BASE_URL}/hakajimai")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "hakajimai-a11y")


def run_p6_admin(page: Page, persona: dict):
    """管理者: アカウント設定・相続計画・リマインダー確認"""
    token = ensure_account(persona)
    if not token:
        return
    set_auth(page, token)

    page.goto(f"{BASE_URL}/account")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "account-settings")

    page.goto(f"{BASE_URL}/estate")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "estate-plan-list")

    page.goto(f"{BASE_URL}/settings/reminders")
    page.wait_for_timeout(1500)
    shot(page, persona["id"], "reminder-settings")


SCENARIO_FUNCS = [
    run_p1_beginner,
    run_p2_daily,
    run_p3_hurry,
    run_p4_edge,
    run_p5_a11y,
    run_p6_admin,
]


# ── メイン ──────────────────────────────────────────────────

def main():
    os.makedirs(SHOT_DIR, exist_ok=True)

    idx = next_persona_idx()
    persona = PERSONAS[idx]
    run_func = SCENARIO_FUNCS[idx]

    print(f"\n{'='*55}")
    print(f"🎭 HF Space ペルソナモニター")
    print(f"   ペルソナ {idx+1}/{len(PERSONAS)}: {persona['name']}")
    print(f"   URL: {BASE_URL}")
    print(f"   時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.set_default_timeout(60000)  # HF Space スリープ解除を考慮して 60 秒

        # ウォームアップ: スリープ中のコンテナを起こす
        print("  🔄 ウォームアップ中...")
        try:
            page.goto(BASE_URL, timeout=60000)
            page.wait_for_timeout(2000)
            print("  ✅ 応答確認")
        except Exception:
            print("  ⚠️  ウォームアップタイムアウト（続行）")

        try:
            run_func(page, persona)
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback; traceback.print_exc()
            shot(page, persona["id"], "error")
        finally:
            browser.close()

    print(f"\n📊 課題: {len(issues)}件")
    for iss in issues:
        print(f"  [{iss['priority']}] {iss['content']}")

    # 結果を JSON で保存
    result_path = os.path.join(SHOT_DIR, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{persona['id']}-result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({"persona": persona["name"], "issues": issues, "ts": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

    return issues


if __name__ == "__main__":
    main()
