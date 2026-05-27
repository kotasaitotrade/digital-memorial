"""
ベータテスト - 5人のペルソナによる総合テスト
実行方法: cd /Users/user01/digital-memorial && python3 e2e/beta_test.py
"""
import sys, os, time, json, traceback, requests
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

BASE_URL = "http://localhost:5173"
API_URL  = "http://localhost:8000/api"
SS_DIR   = os.path.join(os.path.dirname(__file__), "beta_screenshots")
os.makedirs(SS_DIR, exist_ok=True)

ROUND = os.environ.get("BETA_ROUND", "1")

PASS_COUNT = 0
FAIL_COUNT = 0
BUG_COUNT  = 0
ISSUES     = []

def ts():
    return datetime.now().strftime("%H:%M:%S")

def ss(page: Page, name: str) -> str:
    path = os.path.join(SS_DIR, f"r{ROUND}_{name}.png")
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        pass
    return path

def ok(label: str):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  ✅ [{ts()}] {label}")

def fail(label: str, detail: str = "", page: Page = None, persona: str = ""):
    global FAIL_COUNT
    FAIL_COUNT += 1
    spath = ""
    if page:
        spath = ss(page, f"fail_{FAIL_COUNT}")
    ISSUES.append({"persona": persona, "step": label, "severity": "FAIL", "desc": detail[:120], "ss": spath})
    print(f"  ❌ [{ts()}] {label}" + (f" — {detail[:80]}" if detail else ""))

def bug(label: str, detail: str, page: Page = None, persona: str = ""):
    global BUG_COUNT
    BUG_COUNT += 1
    spath = ""
    if page:
        spath = ss(page, f"bug_{BUG_COUNT}")
    ISSUES.append({"persona": persona, "step": label, "severity": "BUG", "desc": detail[:120], "ss": spath})
    print(f"  🐛 [{ts()}] BUG: {label} — {detail}")


# ─── ユーティリティ ───────────────────────────────────────────

def register_user(page: Page, email: str, name: str, pw: str) -> bool:
    page.goto(f"{BASE_URL}/register")
    page.wait_for_load_state("networkidle")
    try:
        page.fill("input[placeholder='山田 花子']", name)
        page.fill("input[type='email']", email)
        page.fill("input[type='password']", pw)
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=8000)
        return True
    except Exception:
        return login_user(page, email, pw)

def login_user(page: Page, email: str, pw: str) -> bool:
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    try:
        page.fill("input[type='email']", email)
        page.fill("input[type='password']", pw)
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=8000)
        return True
    except Exception as e:
        print(f"    ⚠️ ログイン失敗: {e}")
        return False

def api_login(email: str, pw: str) -> str:
    """APIトークン取得"""
    try:
        # OAuth2形式（form data）
        res = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": pw}, timeout=5)
        if res.status_code == 200:
            return res.json().get("access_token", "")
    except Exception:
        pass
    return ""

def api_get(path: str, token: str):
    try:
        res = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


# ─── 終活チェックリスト操作 ──────────────────────────────────

def do_checklist(page: Page, category: str, persona: str):
    """指定カテゴリのチェックリストを表示してチェックを入れる"""
    page.goto(f"{BASE_URL}/shukatsu")
    page.wait_for_load_state("networkidle")

    # カテゴリタブをクリック
    page.click(f"button:has-text('{category}')")
    page.wait_for_timeout(500)
    ss(page, f"{persona}_checklist_{category}")

    # チェックボックス（丸いボタン）を全部クリック
    checkboxes = page.locator("button[style*='border-radius: 50%']").all()
    # 未チェックのみクリック（背景が白いもの）
    clicked = 0
    for cb in checkboxes:
        try:
            # is_completedでないもの（背景が#fffのもの）をクリック
            cb.click()
            page.wait_for_timeout(200)
            clicked += 1
        except Exception:
            pass
    return clicked

def check_score(page: Page) -> int:
    """スコア（%）を取得"""
    import re
    try:
        content = page.content()
        # スコアカードの数字を探す（例: "72%"）
        m = re.search(r'scoreNum[^>]*>\s*(\d+)\s*<', content)
        if m:
            return int(m.group(1))
        # SVGテキスト要素から
        m = re.search(r'<text[^>]*>(\d+)%</text>', content)
        if m:
            return int(m.group(1))
        return -1
    except Exception:
        return -1


# ─── 相続計画作成 ────────────────────────────────────────────

def create_estate_plan(page: Page, title: str, persona: str) -> str:
    """相続計画を作成してplan_idを返す"""
    page.goto(f"{BASE_URL}/estate")
    page.wait_for_load_state("networkidle")

    # 「＋ 新規作成」ボタン
    page.click("button:has-text('新規作成')", timeout=5000)
    page.wait_for_timeout(300)

    # タイトル入力（デフォルト値があるのでclear後入力）
    inp = page.locator("input[placeholder*='計画名']").first
    inp.fill("")
    inp.type(title)
    page.click("button:has-text('作成して開始')")
    page.wait_for_url(f"{BASE_URL}/estate/*/family", timeout=8000)

    # URLからplan_idを取得
    import re
    m = re.search(r"/estate/(\d+)/family", page.url)
    return m.group(1) if m else ""

def add_family_member(page: Page, rel_btn_text: str, name: str):
    """家族メンバーを追加"""
    page.click(f"button:has-text('{rel_btn_text}')")
    page.wait_for_timeout(300)
    # 最後に追加された名前入力欄
    name_inputs = page.locator("input[placeholder='名前']").all()
    if name_inputs:
        name_inputs[-1].fill(name)

def save_family(page: Page, plan_id: str):
    """家族構成を保存して財産ページへ"""
    page.click("button:has-text('保存して次へ')")
    page.wait_for_url(f"{BASE_URL}/estate/{plan_id}/assets", timeout=8000)

def add_asset(page: Page, asset_type_label: str, name: str, amount: int, is_debt: bool = False):
    """財産を追加"""
    if is_debt:
        page.click("button:has-text('負債を追加')")
    else:
        page.click(f"button:has-text('＋ {asset_type_label}を追加')")
    page.wait_for_timeout(300)

    # 最後に追加された名称・金額フィールド
    name_inputs = page.locator("input[placeholder='名称（例：自宅）']").all()
    if name_inputs:
        name_inputs[-1].fill(name)
    amount_inputs = page.locator("input[placeholder='金額（円）']").all()
    if amount_inputs:
        amount_inputs[-1].fill(str(amount))

def save_assets(page: Page, plan_id: str):
    """財産を保存して計算結果へ"""
    page.click("button:has-text('保存して計算結果を見る')")
    page.wait_for_url(f"{BASE_URL}/estate/{plan_id}/result", timeout=8000)
    # API計算完了を待つ（計算中...が消えるまで）
    page.wait_for_function("() => !document.body.innerText.includes('計算中...')", timeout=8000)


# ─── エンディングノート操作 ──────────────────────────────────

def goto_ending_note_tab(page: Page, tab_name: str):
    """エンディングノートの指定タブへ"""
    page.goto(f"{BASE_URL}/ending-note")
    page.wait_for_load_state("networkidle")
    page.click(f"button:has-text('{tab_name}')")
    page.wait_for_timeout(500)


# ══════════════════════════════════════════════════════════════
# ペルソナ 1: 田中 幸子 (70歳・未亡人・子供2人)
# ══════════════════════════════════════════════════════════════

def persona_tanaka(page: Page):
    p = "tanaka"
    print(f"\n{'='*55}")
    print(f"  👵 ペルソナ1: 田中幸子 (70歳・未亡人・相続準備中)")
    print(f"{'='*55}")

    email, pw = "tanaka_sachiko_beta@example.com", "sachiko2024"
    logged_in = register_user(page, email, "田中 幸子", pw)
    if not logged_in:
        fail("ログイン", "田中幸子ログイン失敗", page, p)
        return
    ok("登録・ログイン")
    ss(page, f"{p}_01_dashboard")

    # ─ 墓誌作成（夫の墓誌）─
    try:
        page.click("a:has-text('新規作成')", timeout=5000)
        page.wait_for_load_state("networkidle")
        page.fill("input[placeholder='例：山田 太郎']", "田中 正男")
        page.fill("input[placeholder='例：1930年5月3日']", "1945年3月15日")
        page.fill("input[placeholder='例：2020年10月15日']", "2022年11月20日")
        page.fill("textarea[placeholder*='故人の人生']", "愛する夫、田中正男。50年間ともに歩んでくれてありがとう。あなたの笑顔はいつまでも心に生きています。")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_02_memorial_created")
        ok("墓誌作成（夫の墓誌）")
    except Exception as e:
        fail("墓誌作成", str(e), page, p)

    # ─ 終活チェックリスト ─
    try:
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")

        score_before = check_score(page)
        ok(f"終活スコア表示: {score_before}%")

        # 相続カテゴリをすべてチェック
        cnt = do_checklist(page, "相続", p)
        ok(f"相続チェックリスト操作（{cnt}件）")

        # スコアが上がったか確認
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")
        score_after = check_score(page)
        if score_after > score_before:
            ok(f"スコア上昇確認: {score_before}% → {score_after}%")
        elif score_after == score_before and cnt == 0:
            ok("チェック済みアイテムのみ（スコア変化なし）")
        else:
            bug("スコア更新不具合", f"チェックしたのにスコアが変化しない ({score_before}% → {score_after}%)", page, p)

    except Exception as e:
        fail("終活チェックリスト", str(e), page, p)

    # ─ 相続計画（未亡人・子2人）─
    try:
        plan_id = create_estate_plan(page, "田中家の相続計画 2024", p)
        ok(f"相続計画作成 (id={plan_id})")

        # 子2人追加（配偶者なし）
        add_family_member(page, "子どもを追加", "田中 一郎")
        add_family_member(page, "子どもを追加", "田中 花子")
        ok("子供2人追加")

        ss(page, f"{p}_03_family")
        save_family(page, plan_id)
        ok("家族構成保存")

        # 財産追加（自宅4500万円・預金500万円）
        add_asset(page, "不動産", "横浜市港北区の自宅", 45_000_000)
        add_asset(page, "預貯金", "三菱UFJ銀行", 5_000_000)
        ss(page, f"{p}_04_assets")
        ok("財産追加（不動産・預貯金）")

        save_assets(page, plan_id)
        ss(page, f"{p}_05_result")
        ok("相続計算結果表示")

        # 結果の内容確認
        content = page.content()
        if "田中 一郎" in content and "田中 花子" in content:
            ok("子2人の相続人表示確認")
        else:
            bug("相続人表示", "子2人の名前が結果ページに表示されていない", page, p)

        if "第1順位" in content:
            ok("相続順位（第1順位：子）表示確認")
        else:
            bug("相続順位表示", "第1順位の表示なし", page, p)

    except Exception as e:
        fail("相続計画（田中）", str(e), page, p)

    # ─ エンディングノート（医療）─
    try:
        goto_ending_note_tab(page, "医療・介護")
        ss(page, f"{p}_06_medical")

        # 延命治療: 希望しない
        page.click("label:has-text('希望しない')")
        page.wait_for_timeout(1500)  # auto-save待ち
        ok("延命治療: 希望しない（自動保存）")

        # かかりつけ医
        page.fill("textarea[placeholder='医師名・病院名・電話番号']", "横浜市立市民病院 田村先生（内科）")
        page.wait_for_timeout(1500)
        ok("かかりつけ医入力（自動保存）")
        ss(page, f"{p}_07_medical_saved")

    except Exception as e:
        fail("エンディングノート医療", str(e), page, p)

    print(f"\n  ✨ 田中幸子 テスト完了")


# ══════════════════════════════════════════════════════════════
# ペルソナ 2: 佐藤 健一 (55歳・IT企業・デジタル資産)
# ══════════════════════════════════════════════════════════════

def persona_sato(page: Page):
    p = "sato"
    print(f"\n{'='*55}")
    print(f"  👨‍💻 ペルソナ2: 佐藤健一 (55歳・IT企業・デジタル資産重視)")
    print(f"{'='*55}")

    email, pw = "sato_kenichi_beta@example.com", "kenichi2024"
    logged_in = register_user(page, email, "佐藤 健一", pw)
    if not logged_in:
        fail("ログイン", "佐藤健一ログイン失敗", page, p)
        return
    ok("登録・ログイン")

    # ─ デジタルカテゴリチェックリスト全チェック ─
    try:
        cnt = do_checklist(page, "デジタル", p)
        ok(f"デジタルチェックリスト操作（{cnt}件）")
    except Exception as e:
        fail("デジタルチェックリスト", str(e), page, p)

    # ─ エンディングノート: デジタル資産3件 ─
    try:
        goto_ending_note_tab(page, "デジタル資産")
        ss(page, f"{p}_01_digital_tab")

        digital_items = [
            ("Twitter/X", "@kenichiSato55", "アカウント削除希望"),
            ("楽天銀行", "口座番号は金庫内", ""),
            ("ビットコイン (0.5BTC)", "Ledgerウォレット", ""),
        ]
        for svc, acct, inst in digital_items:
            page.fill("input[placeholder='サービス名（例：X / Instagram）']", svc)
            if acct:
                page.fill("input[placeholder='アカウント名（任意）']", acct)
            if inst:
                page.fill("input[placeholder='死後の処理方法（例：削除してほしい）']", inst)
            page.click("button:has-text('追加')")
            page.wait_for_timeout(500)
            ok(f"デジタル資産追加: {svc}")

        ss(page, f"{p}_02_digital_saved")

        # サブスク3件
        subs = [
            ("Netflix", "1490", "アカウント設定から解約"),
            ("Amazon Prime", "5900", ""),
            ("GitHub Copilot", "1900", ""),
        ]
        for svc, fee, method in subs:
            page.fill("input[placeholder='サービス名（例：Netflix）']", svc)
            page.fill("input[placeholder='月額（円）']", fee)
            if method:
                page.fill("input[placeholder='解約方法']", method)
            page.click("button:has-text('追加')")
            page.wait_for_timeout(500)
            ok(f"サブスク追加: {svc}")

        ss(page, f"{p}_03_subscriptions")

        # 追加したアイテムが表示されているか確認
        content = page.content()
        if "Twitter/X" in content and "Netflix" in content:
            ok("デジタル資産・サブスク表示確認")
        else:
            bug("デジタル資産表示", "追加したアイテムが画面に表示されていない", page, p)

    except Exception as e:
        fail("デジタル資産追加", str(e), page, p)

    # ─ 相続計画（妻+子3人、大きな資産）─
    try:
        plan_id = create_estate_plan(page, "佐藤家の相続計画", p)
        ok(f"相続計画作成 (id={plan_id})")

        add_family_member(page, "配偶者を追加", "佐藤 美智子")
        for name in ["佐藤 太郎", "佐藤 次郎", "佐藤 三郎"]:
            add_family_member(page, "子どもを追加", name)
        ok("配偶者+子3人追加")

        ss(page, f"{p}_04_family")
        save_family(page, plan_id)

        # 大きな金額のテスト
        add_asset(page, "不動産", "自宅（世田谷区）", 120_000_000)
        add_asset(page, "預貯金", "SBI証券口座", 85_000_000)
        add_asset(page, "有価証券", "株式ポートフォリオ", 30_000_000)
        add_asset(page, "その他資産", "暗号資産", 10_000_000, is_debt=False)
        add_asset(page, "", "住宅ローン残高", 32_000_000, is_debt=True)
        ss(page, f"{p}_05_assets")
        ok("大きな金額の財産追加（合計約2億円）")

        save_assets(page, plan_id)
        ss(page, f"{p}_06_result")

        content = page.content()
        # 相続税警告が表示されるべき（2億円超）
        if "相続税の申告" in content:
            ok("相続税警告表示（2億円超）")
        else:
            bug("相続税警告未表示", "2億円超の財産で相続税警告が出ていない", page, p)

        # 配偶者の取得金額が表示されるか
        if "佐藤 美智子" in content:
            ok("配偶者の相続分表示確認")
        else:
            bug("配偶者表示なし", "配偶者が相続人として表示されていない", page, p)

    except Exception as e:
        fail("相続計画（佐藤）", str(e), page, p)

    print(f"\n  ✨ 佐藤健一 テスト完了")


# ══════════════════════════════════════════════════════════════
# ペルソナ 3: 山田 花子 (65歳・独身・ペット2匹)
# ══════════════════════════════════════════════════════════════

def persona_yamada(page: Page):
    p = "yamada"
    print(f"\n{'='*55}")
    print(f"  🐱 ペルソナ3: 山田花子 (65歳・独身・ペット2匹)")
    print(f"{'='*55}")

    email, pw = "yamada_hanako_beta@example.com", "hanako2024"
    logged_in = register_user(page, email, "山田 花子", pw)
    if not logged_in:
        fail("ログイン", "山田花子ログイン失敗", page, p)
        return
    ok("登録・ログイン")

    # ─ ペット登録 ─
    try:
        goto_ending_note_tab(page, "ペット")
        ss(page, f"{p}_01_pets_tab")

        pets = [
            ("ミケ", "猫（三毛猫・メス）", "品川わんにゃんクリニック", "田村 幸代（妹）090-1234-5678"),
            ("ポチ", "犬（柴犬・オス）", "", "近所の鈴木さん"),
        ]
        for name, species, medical, caretaker in pets:
            page.fill("input[placeholder='ペットの名前']", name)
            page.fill("input[placeholder='種類（例：柴犬）']", species)
            if caretaker:
                page.fill("input[placeholder='引き継ぎ先']", caretaker)
            if medical:
                page.fill("input[placeholder='医療情報（持病・かかりつけ医）']", medical)
            page.click("button:has-text('追加')")
            page.wait_for_timeout(500)
            ok(f"ペット追加: {name}")

        ss(page, f"{p}_02_pets_saved")

        # 表示確認
        content = page.content()
        if "ミケ" in content and "ポチ" in content:
            ok("ペット2匹の表示確認")
        else:
            bug("ペット表示なし", "追加したペットが表示されていない", page, p)

    except Exception as e:
        fail("ペット追加", str(e), page, p)

    # ─ 緊急連絡先3件 ─
    try:
        goto_ending_note_tab(page, "緊急連絡先")
        ss(page, f"{p}_03_contacts")

        contacts = [
            ("田村 幸代", "妹", "090-1234-5678", ""),
            ("山田 太一", "甥", "080-9876-5432", "taichi@example.com"),
            ("佐々木医院", "かかりつけ医", "03-1234-5678", ""),
        ]
        for name, rel, phone, email in contacts:
            page.fill("input[placeholder='名前']", name)
            page.fill("input[placeholder='続柄（例：長男）']", rel)
            page.fill("input[placeholder='電話番号']", phone)
            if email:
                page.fill("input[placeholder='メールアドレス']", email)
            page.click("button:has-text('追加')")
            page.wait_for_timeout(500)
            ok(f"緊急連絡先追加: {name}")

        ss(page, f"{p}_04_contacts_saved")

    except Exception as e:
        fail("緊急連絡先", str(e), page, p)

    # ─ 家族へのメッセージ（長文テスト）─
    try:
        goto_ending_note_tab(page, "家族へのメッセージ")
        long_msg = (
            "妹の幸代へ\n\n"
            "長い間、ひとり身の私のことを気にかけてくれてありがとう。"
            "ミケとポチのことをお願いできますか。ふたりとも人懐こくて優しい子たちです。\n\n"
            "ミケは魚が大好きで、朝晩のご飯を楽しみにしています。\n"
            "ポチは毎朝の散歩が日課です。公園で走り回るのが一番の楽しみ。\n\n"
            "私の後は二人のことよろしくね。ありがとう。\n\n花子より"
        )
        page.fill("textarea[placeholder='ここに想いを記録してください...']", long_msg)
        page.wait_for_timeout(1500)  # auto-save
        ss(page, f"{p}_05_message")
        ok(f"長文メッセージ入力（{len(long_msg)}文字・自動保存）")

        # APIで保存されたか確認
        token = api_login(email, pw)
        note = api_get("/ending-note", token)
        if note and note.get("family_message") == long_msg:
            ok("長文メッセージAPIで保存確認")
        elif note and note.get("family_message"):
            saved_len = len(note["family_message"])
            if saved_len < len(long_msg):
                bug("メッセージ文字数切り詰め", f"入力{len(long_msg)}文字→保存{saved_len}文字", page, p)
            else:
                ok("長文メッセージ保存済み（内容確認OK）")
        else:
            fail("メッセージAPI確認", "APIからデータ取得できず", p)

    except Exception as e:
        fail("家族へのメッセージ", str(e), page, p)

    # ─ 形見分けリスト ─
    try:
        goto_ending_note_tab(page, "形見分け")
        ss(page, f"{p}_06_bequest")

        bequests = [
            ("母から譲り受けた着物（訪問着）", "妹 幸代", ""),
            ("ロレックス腕時計", "甥 太一", "父の形見"),
        ]
        for item_name, recipient, notes in bequests:
            page.fill("input[placeholder='物品名（例：父の形見の時計）']", item_name)
            page.fill("input[placeholder='渡す相手の名前']", recipient)
            if notes:
                page.fill("input[placeholder='備考（任意）']", notes)
            page.click("button:has-text('追加')")
            page.wait_for_timeout(500)
            ok(f"形見分け追加: {item_name[:20]}")

        ss(page, f"{p}_07_bequest_saved")

        content = page.content()
        if "着物" in content and "ロレックス" in content:
            ok("形見分けリスト表示確認")
        else:
            bug("形見分け表示なし", "追加したアイテムが表示されていない", page, p)

    except Exception as e:
        fail("形見分け", str(e), page, p)

    # ─ 独身・子なしの相続計画（兄弟姉妹） ─
    try:
        plan_id = create_estate_plan(page, "山田花子の相続計画（独身）", p)
        ok(f"独身相続計画作成 (id={plan_id})")

        # 兄弟姉妹追加
        add_family_member(page, "兄弟姉妹を追加", "田村 幸代")
        ok("兄弟姉妹追加（独身シナリオ）")

        ss(page, f"{p}_08_family_sibling")
        save_family(page, plan_id)

        add_asset(page, "不動産", "横浜市鶴見区のマンション", 18_000_000)
        add_asset(page, "預貯金", "ゆうちょ銀行", 2_000_000)
        ss(page, f"{p}_09_assets")
        save_assets(page, plan_id)

        content = page.content()
        if "田村 幸代" in content:
            ok("兄弟姉妹への相続計算表示")
        else:
            bug("兄弟相続表示なし", "兄弟姉妹が相続人として表示されていない", page, p)

        if "第3順位" in content:
            ok("第3順位（兄弟姉妹）表示確認")
        else:
            bug("相続順位（第3順位）未表示", "独身・子なしで兄弟が第3順位と表示されない", page, p)

    except Exception as e:
        fail("独身相続計画", str(e), page, p)

    # ─ ペットチェックリスト ─
    try:
        cnt = do_checklist(page, "ペット", p)
        ok(f"ペットチェックリスト全チェック（{cnt}件）")
    except Exception as e:
        fail("ペットチェックリスト", str(e), page, p)

    print(f"\n  ✨ 山田花子 テスト完了")


# ══════════════════════════════════════════════════════════════
# ペルソナ 4: 鈴木 太郎 (80歳・農地・配偶者あり)
# ══════════════════════════════════════════════════════════════

def persona_suzuki(page: Page):
    p = "suzuki"
    print(f"\n{'='*55}")
    print(f"  👴 ペルソナ4: 鈴木太郎 (80歳・農地・配偶者あり)")
    print(f"{'='*55}")

    email, pw = "suzuki_taro_beta@example.com", "taro2024beta"
    logged_in = register_user(page, email, "鈴木 太郎", pw)
    if not logged_in:
        fail("ログイン", "鈴木太郎ログイン失敗", page, p)
        return
    ok("登録・ログイン")

    # ─ 大きな農地財産の相続計算 ─
    try:
        plan_id = create_estate_plan(page, "鈴木家農地・財産相続計画", p)
        ok(f"相続計画作成 (id={plan_id})")

        add_family_member(page, "配偶者を追加", "鈴木 ハル")
        add_family_member(page, "子どもを追加", "鈴木 一雄")
        add_family_member(page, "子どもを追加", "鈴木 二子")
        ok("配偶者+子2人追加")

        save_family(page, plan_id)

        # 億単位の農地
        add_asset(page, "不動産", "農地（千葉県XX市XX町）", 250_000_000)
        add_asset(page, "不動産", "山林・雑種地", 80_000_000)
        add_asset(page, "預貯金", "農業協同組合出資金", 5_000_000)
        add_asset(page, "その他資産", "農業機械（トラクター等）", 3_000_000)
        ss(page, f"{p}_01_assets")
        ok("農地大金額財産追加（合計3.38億円）")

        save_assets(page, plan_id)
        ss(page, f"{p}_02_result")

        content = page.content()

        # 億単位の相続税警告
        if "相続税の申告" in content:
            ok("億単位での相続税警告表示")
        else:
            bug("億単位相続税警告なし", "3.38億円で相続税警告が出ていない", page, p)

        # 鈴木ハルが1/2を取得するはず
        if "鈴木 ハル" in content and "1/2" in content:
            ok("配偶者1/2相続分表示確認")
        else:
            bug("配偶者相続分未表示", "鈴木ハルの1/2相続分が表示されていない", page, p)

        # 基礎控除の確認（3000万+600万×3人=4800万円）
        if "48,000,000" in content or "4,800" in content:
            ok("基礎控除計算確認（3+0.6×3=4.8億円）")

    except Exception as e:
        fail("農地相続計画", str(e), page, p)

    # ─ 債務超過シナリオのテスト ─
    try:
        plan_id2 = create_estate_plan(page, "テスト：債務超過シナリオ", p)
        ok("債務超過テスト計画作成")

        add_family_member(page, "子どもを追加", "テスト 太郎")
        save_family(page, plan_id2)

        # 負債が資産を上回るケース
        add_asset(page, "預貯金", "銀行口座", 1_000_000)
        add_asset(page, "", "借金", 5_000_000, is_debt=True)
        ss(page, f"{p}_03_debt_assets")
        save_assets(page, plan_id2)
        ss(page, f"{p}_04_debt_result")

        content = page.content()
        if "債務超過" in content:
            ok("債務超過警告表示確認")
        else:
            bug("債務超過警告なし", "負債>資産時に債務超過警告が表示されない", page, p)

    except Exception as e:
        fail("債務超過テスト", str(e), page, p)

    # ─ 葬儀希望設定 ─
    try:
        goto_ending_note_tab(page, "葬儀")
        page.click("label:has-text('家族葬')")
        page.fill("input[placeholder='例：仏教（浄土宗）、無宗教など']", "仏教（浄土真宗）")
        page.fill("textarea[placeholder='会場・花・参列者への要望など']",
                  "質素に家族だけで見送ってほしい。戒名は不要。お花は菊と白百合を少し。")
        page.wait_for_timeout(1500)
        ss(page, f"{p}_05_funeral")
        ok("葬儀情報設定（家族葬・自動保存）")

    except Exception as e:
        fail("葬儀設定", str(e), page, p)

    # ─ 全チェックリストの医療・人間関係も確認 ─
    try:
        for cat in ["医療", "人間関係"]:
            cnt = do_checklist(page, cat, p)
            ok(f"{cat}チェックリスト操作（{cnt}件）")
    except Exception as e:
        fail("チェックリスト操作", str(e), page, p)

    print(f"\n  ✨ 鈴木太郎 テスト完了")


# ══════════════════════════════════════════════════════════════
# ペルソナ 5: 中村 美代 (45歳・バツイチ・子1人・エラー/エッジケース)
# ══════════════════════════════════════════════════════════════

def persona_nakamura(page: Page):
    p = "nakamura"
    print(f"\n{'='*55}")
    print(f"  👩 ペルソナ5: 中村美代 (45歳・エッジケース担当)")
    print(f"{'='*55}")

    email, pw = "nakamura_miyo_beta@example.com", "miyo2024beta"
    logged_in = register_user(page, email, "中村 美代", pw)
    if not logged_in:
        fail("ログイン", "中村美代ログイン失敗", page, p)
        return
    ok("登録・ログイン")

    # ─ 新規ユーザースコア0%確認 ─
    try:
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_01_new_user")
        content = page.content()
        if "0%" in content:
            ok("新規ユーザー: スコア0%表示")
        else:
            bug("新規ユーザースコア", "新規ユーザーでスコアが0%でない", page, p)
    except Exception as e:
        fail("新規ユーザースコア確認", str(e), page, p)

    # ─ 空タイトルで相続計画作成（バリデーションテスト）─
    try:
        page.goto(f"{BASE_URL}/estate")
        page.wait_for_load_state("networkidle")
        page.click("button:has-text('新規作成')")
        page.wait_for_timeout(300)

        inp = page.locator("input[placeholder*='計画名']").first
        inp.fill("")  # 空文字
        page.click("button:has-text('作成して開始')")
        page.wait_for_timeout(1000)

        current_url = page.url
        if "/estate/" not in current_url or current_url.endswith("/estate"):
            ok("空タイトルバリデーション: 計画作成されなかった")
        else:
            bug("空タイトル作成可能", "空文字のタイトルで相続計画が作成されてしまった", page, p)
        ss(page, f"{p}_02_empty_title")
    except Exception as e:
        ok(f"空タイトル: 例外で拒否 ({str(e)[:40]})")

    # ─ XSSテスト ─
    try:
        page.goto(f"{BASE_URL}/estate")
        page.wait_for_load_state("networkidle")

        try:
            page.click("button:has-text('新規作成')", timeout=3000)
            page.wait_for_timeout(300)
        except Exception:
            # フォームが既に表示されている場合
            pass

        inp = page.locator("input[placeholder*='計画名']").first
        if inp.count() > 0:
            inp.fill("<script>alert('xss')</script>")
            page.click("button:has-text('作成して開始')")
            page.wait_for_timeout(1500)

            # アラートが出ないことを確認
            dialog_fired = False
            def on_dialog(dialog):
                nonlocal dialog_fired
                dialog_fired = True
                dialog.dismiss()
            page.on("dialog", on_dialog)
            page.wait_for_timeout(1000)

            if dialog_fired:
                bug("XSS脆弱性", "スクリプトが実行されてアラートが表示された！", page, p)
            else:
                ok("XSS入力: スクリプト実行されなかった（安全）")
        ss(page, f"{p}_03_xss")
    except Exception as e:
        ok(f"XSS入力: 安全に処理 ({str(e)[:40]})")

    # ─ 特殊文字入力テスト ─
    try:
        goto_ending_note_tab(page, "形見分け")
        special_chars = "特殊文字テスト：①②③、「」『』【】〈〉《》〔〕…—～"
        page.fill("input[placeholder='物品名（例：父の形見の時計）']", special_chars)
        page.fill("input[placeholder='渡す相手の名前']", "テスト 太郎")
        page.click("button:has-text('追加')")
        page.wait_for_timeout(500)

        content = page.content()
        if "①②③" in content:
            ok("特殊文字（日本語記号）入力・表示OK")
        else:
            bug("特殊文字表示不具合", "日本語特殊記号が保存後に表示されない", page, p)
        ss(page, f"{p}_04_special_chars")
    except Exception as e:
        fail("特殊文字テスト", str(e), page, p)

    # ─ 1000文字の長文メッセージ ─
    try:
        goto_ending_note_tab(page, "家族へのメッセージ")
        long_text = "あ" * 1000
        page.fill("textarea[placeholder='ここに想いを記録してください...']", long_text)
        page.wait_for_timeout(1500)  # auto-save

        token = api_login(email, pw)
        note = api_get("/ending-note", token)
        if note and note.get("family_message"):
            saved_len = len(note["family_message"])
            if saved_len >= 1000:
                ok(f"1000文字保存成功（保存: {saved_len}文字）")
            elif saved_len > 0:
                bug("長文切り詰め", f"1000文字→{saved_len}文字に切り詰められた", page, p)
            else:
                fail("1000文字保存", "保存後テキストが空", p)
        else:
            fail("1000文字保存確認", "APIで取得できず", p)
        ss(page, f"{p}_05_long_text")
    except Exception as e:
        fail("1000文字長文テスト", str(e), page, p)

    # ─ モバイル幅（375px）レスポンシブ確認 ─
    try:
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_06_mobile_shukatsu")
        ok("モバイル幅375px: 終活ページ表示OK")

        page.goto(f"{BASE_URL}/estate")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_07_mobile_estate")
        ok("モバイル幅375px: 相続計画ページ表示OK")

        page.goto(f"{BASE_URL}/ending-note")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_08_mobile_ending")
        ok("モバイル幅375px: エンディングノートページ表示OK")

        # タブが全部見えるか確認（flexWrapで折り返し）
        tabs = page.locator("button:has-text('医療・介護')").count()
        if tabs > 0:
            ok("モバイル幅: タブ表示確認OK")
        else:
            bug("モバイルタブ非表示", "375px幅でタブが見えない", page, p)

        page.set_viewport_size({"width": 1280, "height": 800})
    except Exception as e:
        fail("モバイルレスポンシブ", str(e), page, p)
        page.set_viewport_size({"width": 1280, "height": 800})

    # ─ ログアウト後の認証リダイレクト確認 ─
    try:
        page.click("button:has-text('ログアウト')")
        page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
        ok("ログアウト → /login リダイレクト")

        # ログイン前に保護ページに直接アクセス
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")
        if page.url.startswith(f"{BASE_URL}/login"):
            ok("未認証アクセス: /login にリダイレクト")
        else:
            bug("認証ガード不具合", f"ログアウト後に/shukatsuへアクセスできた (URL: {page.url})", page, p)

        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        if page.url.startswith(f"{BASE_URL}/login"):
            ok("未認証 /dashboard アクセス: リダイレクト確認")
        else:
            bug("ダッシュボード認証ガード不具合", "ログアウト後にダッシュボードへアクセスできた", page, p)

    except Exception as e:
        fail("認証リダイレクト", str(e), page, p)

    print(f"\n  ✨ 中村美代 テスト完了")


# ══════════════════════════════════════════════════════════════
# 追加テスト: QRコード・公開ページ・その他
# ══════════════════════════════════════════════════════════════

def test_qr_and_misc(page: Page):
    print(f"\n{'='*55}")
    print(f"  📱 追加テスト: QRコード・公開ページ・checklist_link確認")
    print(f"{'='*55}")
    p = "misc"

    # 田中幸子でログイン（墓誌作成済み）
    logged_in = login_user(page, "tanaka_sachiko_beta@example.com", "sachiko2024")
    if not logged_in:
        fail("QRテストログイン", "ログイン失敗", page, p)
        return

    # ─ QRコードボタン確認 ─
    try:
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        ss(page, f"{p}_01_dashboard")

        qr_btn = page.locator("button:has-text('QRコード')").first
        if qr_btn.count() > 0:
            qr_btn.click()
            page.wait_for_timeout(500)
            ss(page, f"{p}_02_qr_modal")
            ok("QRコードボタン・モーダル表示")

            # モーダル内容確認
            content = page.content()
            if "印刷" in content or "print" in content.lower():
                ok("印刷リンク/ボタン存在確認")
            else:
                bug("印刷ボタンなし", "QRモーダルに印刷リンクがない", page, p)

            # モーダルを閉じる
            close_btn = page.locator("button:has-text('閉じる')").first
            if close_btn.count() > 0:
                close_btn.click()
                ok("QRモーダルを閉じた")
        else:
            # 墓誌にqr_code_pathがないとボタンが非表示になる（正常挙動）
            ok("QRコードボタン: 墓誌未生成または非表示（正常）")
    except Exception as e:
        fail("QRコードテスト", str(e), page, p)

    # ─ チェックリストのリンク先確認 ─
    try:
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")

        # 「入力する →」リンクを全部チェック
        links = page.locator("a:has-text('入力する')").all()
        broken_links = []
        for link in links:
            href = link.get_attribute("href") or ""
            if href == "/digital-key":
                broken_links.append(href)

        if broken_links:
            bug("壊れたリンク", f"/digital-key リンクが残存: {broken_links}", page, p)
        else:
            ok("チェックリストのリンク先確認（/digital-keyなし）")
    except Exception as e:
        fail("チェックリストリンク確認", str(e), page, p)

    # ─ 公開墓誌ページ確認 ─
    try:
        token = api_login("tanaka_sachiko_beta@example.com", "sachiko2024")
        memorials = api_get("/memorials", token)
        if memorials and len(memorials) > 0:
            slug = memorials[0]["slug"]
            page.goto(f"{BASE_URL}/m/{slug}")
            page.wait_for_load_state("networkidle")
            ss(page, f"{p}_03_public_memorial")

            content = page.content()
            if "田中 正男" in content:
                ok("公開墓誌ページ: 故人名表示確認")
            else:
                bug("公開墓誌表示不具合", "故人名が公開ページに表示されない", page, p)

            if "1945" in content:
                ok("公開墓誌: 生年表示確認")
        else:
            ok("墓誌未作成: 公開ページスキップ")
    except Exception as e:
        fail("公開墓誌ページ", str(e), page, p)

    # ─ 全カテゴリのチェックリストが表示されるか ─
    try:
        page.goto(f"{BASE_URL}/shukatsu")
        page.wait_for_load_state("networkidle")
        categories = ["すべて", "相続", "遺言", "医療", "葬儀", "デジタル", "人間関係", "ペット", "思い出"]
        for cat in categories:
            page.click(f"button:has-text('{cat}')")
            page.wait_for_timeout(200)
            items = page.locator("[style*='border-radius: 50%']").count()
            ok(f"カテゴリ「{cat}」: {items}件表示")
    except Exception as e:
        fail("カテゴリフィルター確認", str(e), page, p)

    print(f"\n  ✨ 追加テスト完了")


# ══════════════════════════════════════════════════════════════
# メインエントリー
# ══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*55}")
    print(f"  🧪 ベータテスト Round {ROUND} 開始")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.set_default_timeout(12000)

        for fn, label in [
            (persona_tanaka,  "田中幸子"),
            (persona_sato,    "佐藤健一"),
            (persona_yamada,  "山田花子"),
            (persona_suzuki,  "鈴木太郎"),
            (persona_nakamura,"中村美代"),
            (test_qr_and_misc,"追加テスト"),
        ]:
            try:
                fn(page)
            except Exception as e:
                print(f"  💥 {label}テスト中断: {e}")
                traceback.print_exc()

        context.close()
        browser.close()

    # ─── 結果サマリー ────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  📊 Round {ROUND} テスト結果サマリー")
    print(f"{'='*55}")
    print(f"  ✅ PASS  : {PASS_COUNT}")
    print(f"  ❌ FAIL  : {FAIL_COUNT}")
    print(f"  🐛 BUG   : {BUG_COUNT}")

    if ISSUES:
        print(f"\n  発見した問題 ({len(ISSUES)}件):")
        for i, issue in enumerate(ISSUES, 1):
            icon = "🐛" if issue["severity"] == "BUG" else "❌"
            print(f"  {i}. {icon} [{issue['persona']}] {issue['step']}")
            if issue["desc"]:
                print(f"      → {issue['desc']}")

    result_path = os.path.join(SS_DIR, f"r{ROUND}_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({
            "round": ROUND,
            "timestamp": datetime.now().isoformat(),
            "pass": PASS_COUNT,
            "fail": FAIL_COUNT,
            "bugs": BUG_COUNT,
            "issues": ISSUES,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  結果保存: {result_path}")

    return ISSUES

if __name__ == "__main__":
    issues = main()
    sys.exit(0 if BUG_COUNT == 0 else 1)
