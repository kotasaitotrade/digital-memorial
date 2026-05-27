"""
画面仕様書 HTML ジェネレーター
e2e/screenshots/ 内の s*.png を読み込んで、見やすい仕様書を生成する
"""
import os, base64, datetime

SS_DIR   = os.path.join(os.path.dirname(__file__), "..", "e2e", "screenshots")
OUT_FILE = os.path.join(os.path.dirname(__file__), "screen_spec.html")

def img_b64(name: str) -> str:
    path = os.path.join(SS_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def img_tag(name: str, alt: str = "", width: str = "100%") -> str:
    b64 = img_b64(name)
    if not b64:
        return f'<div class="no-img">※ スクリーンショット未取得: {name}</div>'
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="width:{width};border-radius:6px;border:1px solid #e5e7eb;display:block;" />'

# ─── スクリーン定義 ───────────────────────────────────────────
# (section_id, section_title, subsections)
# subsection = (title, description, [(caption, filename), ...], notes)

SCREENS = [
    # ══════════════════════════════════════
    # 認証
    # ══════════════════════════════════════
    ("auth", "認証", [
        (
            "S01: ログインページ",
            "メールアドレスとパスワードでログインする画面。未入力・誤入力時はエラーメッセージを表示する。",
            [
                ("初期表示",          "s01a_login.png"),
                ("エラー表示（認証失敗）", "s01b_login_error.png"),
            ],
            [
                "URL: /login",
                "未ログイン状態でダッシュボード等にアクセスすると自動リダイレクト",
                "入力項目: メールアドレス（email）、パスワード（password）",
                "バリデーション: 空欄ではsubmit不可（required）",
                "エラー時: ページに留まりエラーメッセージ表示",
            ]
        ),
        (
            "S02: ユーザー登録ページ",
            "新規アカウントを作成する画面。お名前・メールアドレス・パスワードを入力する。",
            [
                ("初期表示",     "s02a_register.png"),
                ("入力済み状態", "s02b_register_filled.png"),
            ],
            [
                "URL: /register",
                "入力項目: お名前（text）、メールアドレス（email）、パスワード（password, minLength=8）",
                "登録成功後: /login へリダイレクト",
                "既存メール使用時: エラーメッセージ「このメールアドレスは既に使用されています」",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # ダッシュボード
    # ══════════════════════════════════════
    ("dashboard", "ダッシュボード（墓誌一覧）", [
        (
            "S03: ダッシュボード",
            "ログイン後のトップ画面。作成した墓誌の一覧と終活ノートへのバナーを表示する。",
            [
                ("墓誌0件（初期状態）",     "s03a_dashboard_empty.png"),
                ("墓誌1件登録後",           "s03b_dashboard_memorial.png"),
                ("QRコードモーダル表示",    "s03c_dashboard_qr_modal.png"),
            ],
            [
                "URL: /dashboard",
                "墓誌がない場合: 空状態メッセージ + 新規作成ボタン",
                "墓誌カード要素: 故人名・生没日・操作ボタン（編集・QR・削除）",
                "終活ノートバナー: /shukatsu へのリンク",
                "QRモーダル: 公開URLのQRコードをポップアップ表示",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # 墓誌管理
    # ══════════════════════════════════════
    ("memorial", "墓誌管理", [
        (
            "S04: 墓誌作成フォーム",
            "新しい墓誌を作成するフォーム。故人の基本情報・略歴・メッセージ・写真を入力できる。",
            [
                ("空フォーム（初期状態）", "s04a_memorial_form_empty.png"),
                ("入力済み状態",           "s04b_memorial_form_filled.png"),
            ],
            [
                "URL: /memorials/new",
                "入力項目: お名前（必須）・生年月日・没年月日・略歴・メッセージ・公開設定・パスワード",
                "写真アップロード: 複数ファイル対応（image/*, video/*）",
                "保存後: /memorials/:id/edit へ遷移（編集モードに切替）",
            ]
        ),
        (
            "S05: 墓誌編集フォーム",
            "既存の墓誌を編集する画面。作成フォームと同一コンポーネントで既存データが初期値として設定される。",
            [
                ("編集画面（上部）",   "s05a_memorial_edit.png"),
                ("写真管理エリア",     "s05b_memorial_edit_photo.png"),
            ],
            [
                "URL: /memorials/:id/edit",
                "既存データが各フィールドに初期表示",
                "写真アップロード: アップロード済み写真の一覧表示と削除機能あり",
                "保存成功時: 「保存しました」トーストを3秒表示",
            ]
        ),
        (
            "S06: QRコード印刷ページ",
            "墓誌の公開URLをQRコードで印刷するためのページ。墓石への貼り付けを想定。",
            [
                ("QR印刷ページ", "s06_print_qr.png"),
            ],
            [
                "URL: /memorials/:id/print-qr",
                "公開URL（/m/:slug）のQRコードを大きく表示",
                "印刷用スタイル適用済み",
            ]
        ),
        (
            "S07: 公開墓誌ページ",
            "QRコードからアクセスする公開ページ。ログイン不要で誰でも閲覧できる（パスワード設定時を除く）。",
            [
                ("公開ページ（上部）",   "s07a_public_memorial_top.png"),
                ("公開ページ（下部）",   "s07b_public_memorial_bottom.png"),
            ],
            [
                "URL: /m/:slug",
                "認証不要（公開ページ）",
                "表示要素: 故人名・生没日・享年・略歴・写真ギャラリー・メッセージ",
                "パスワード設定時: 閲覧前にパスワード入力を要求",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # 終活ノート
    # ══════════════════════════════════════
    ("shukatsu", "終活ノート（終活ダッシュボード）", [
        (
            "S08-a: 終活ダッシュボード",
            "終活機能の入口ページ。スコアカード・クイックリンク・チェックリストを一覧表示する。",
            [
                ("スコアカード部分",   "s08a_shukatsu_scorecard.png"),
                ("ページ全体",         "s08b_shukatsu_full.png"),
            ],
            [
                "URL: /shukatsu",
                "スコアカード: 完了率をパーセント＋SVGゲージで表示",
                "クイックリンク: 相続の棚卸し / エンディングノート / 墓誌の管理",
                "チェックリスト: カテゴリタブフィルター + 各項目のチェックボックス",
            ]
        ),
        (
            "S08-b: チェックリスト カテゴリ別表示",
            "「すべて」「相続」「遺言」「医療」「葬儀」「デジタル」「人間関係」「ペット」「思い出」の9カテゴリでフィルタリングできる。",
            [
                ("すべて",   "s08c_checklist_すべて.png"),
                ("相続",     "s08c_checklist_相続.png"),
                ("遺言",     "s08c_checklist_遺言.png"),
                ("医療",     "s08c_checklist_医療.png"),
                ("葬儀",     "s08c_checklist_葬儀.png"),
                ("デジタル", "s08c_checklist_デジタル.png"),
                ("人間関係", "s08c_checklist_人間関係.png"),
                ("ペット",   "s08c_checklist_ペット.png"),
                ("思い出",   "s08c_checklist_思い出.png"),
            ],
            [
                "チェック状態はAPIで永続化（/api/checklist/toggle）",
                "優先度バッジ: 必須（赤）/ 推奨（橙）/ 任意（グレー）",
                "未完了の項目には「入力する →」リンクを表示",
                "完了済みはチェックマーク＋打ち消し線でスタイル変更",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # 相続の棚卸し
    # ══════════════════════════════════════
    ("estate", "相続の棚卸し", [
        (
            "S09: 相続計画一覧",
            "作成済みの相続計画を一覧表示する。新規作成ボタンから計画名を入力してウィザードを開始できる。",
            [
                ("一覧画面",         "s09a_estate_list.png"),
                ("新規作成フォーム", "s09b_estate_create_form.png"),
            ],
            [
                "URL: /estate",
                "相続計画カード要素: 計画名・家族人数・財産件数・最終更新日",
                "アクション: 家族構成 / 財産 / 結果を見る / 削除",
            ]
        ),
        (
            "S10: 家族構成入力（Step 1）",
            "3ステップウィザードの Step 1。配偶者・子・孫・親・兄弟姉妹を続柄別に追加する。",
            [
                ("空の初期状態",       "s10a_family_empty.png"),
                ("配偶者追加後",       "s10b_family_spouse_added.png"),
                ("子ども2名追加後",    "s10c_family_children_added.png"),
            ],
            [
                "URL: /estate/:planId/family",
                "ウィザードステップ: ① 家族構成（現在） → ② 財産の棚卸し → ③ 計算結果",
                "続柄: 配偶者 / 子（＋養子・欠格・相続放棄フラグ） / 孫（代襲・親ID指定）",
                "         / 親 / 祖父母 / 兄弟姉妹（＋半血フラグ）/ 甥姪（代襲）",
                "子が死亡・欠格の場合のみ「孫」セクションが表示される",
            ]
        ),
        (
            "S11: 財産入力（Step 2）",
            "3ステップウィザードの Step 2。不動産・預貯金・有価証券・生命保険・退職金・その他資産・負債を入力する。",
            [
                ("空の初期状態",         "s11a_asset_empty.png"),
                ("不動産追加後",         "s11b_asset_realestate_added.png"),
                ("不動産＋預貯金追加後", "s11c_asset_bank_added.png"),
                ("負債追加後",           "s11d_asset_debt_added.png"),
                ("合計欄（全体）",       "s11e_asset_full.png"),
            ],
            [
                "URL: /estate/:planId/assets",
                "各資産タイプに「＋ ×××を追加」ボタン",
                "生命保険金：「みなし相続財産」チェックボックスあり",
                "下部に資産合計・負債合計・正味遺産額を自動計算して表示",
                "「保存して計算結果を見る →」で Step 3 へ進む",
            ]
        ),
        (
            "S12: 相続計算結果（Step 3）",
            "3ステップウィザードの Step 3。法定相続人・相続分・遺留分・基礎控除の計算結果を表示する。",
            [
                ("結果画面（上部・viewport内）", "s12a_result_top.png"),
                ("結果画面（全体）",             "s12b_result_full.png"),
                ("遺留分・基礎控除（下部）",     "s12c_result_bottom.png"),
            ],
            [
                "URL: /estate/:planId/result",
                "相続人ごとの相続分（分数 + パーセント + 金額）を表示",
                "代襲相続・半血兄弟・養子・相続放棄・欠格を自動考慮",
                "遺留分: 配偶者・子・親のみ（兄弟姉妹は対象外）",
                "基礎控除: 3,000万円 + 600万円 × 法定相続人数 を計算して警告表示",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # エンディングノート
    # ══════════════════════════════════════
    ("ending", "エンディングノート", [
        (
            "S13: 医療・介護タブ",
            "エンディングノートのデフォルトタブ。延命治療・心肺蘇生・臓器提供などの希望を選択式で記録する。",
            [
                ("初期状態（未入力）", "s13a_medical_default.png"),
                ("入力済み状態",       "s13b_medical_filled.png"),
            ],
            [
                "URL: /ending-note",
                "TABS: 医療・介護 / 葬儀 / 形見分け / デジタル資産 / 緊急連絡先 / ペット / 家族へのメッセージ",
                "RadioGroup（選択肢ボタン）: 延命治療 / 心肺蘇生 / 胃ろう / 臓器提供 / 介護場所",
                "テキストエリア: かかりつけ医・服用薬・備考",
                "変更は1秒後に自動保存（autoSave）",
            ]
        ),
        (
            "S14: 葬儀タブ",
            "葬儀スタイル・宗教・流してほしい音楽・遺影写真の希望を記録する。",
            [
                ("初期状態",     "s14a_funeral_default.png"),
                ("入力済み状態", "s14b_funeral_filled.png"),
            ],
            [
                "葬儀スタイル選択肢: 家族葬 / 一般葬 / 直葬 / 自由にしてほしい",
                "遺影写真: 画像ファイルアップロード対応",
                "変更は1秒後に自動保存",
            ]
        ),
        (
            "S15: 形見分けタブ",
            "「誰に何を譲りたいか」を品目・受取人・備考で記録する。複数件追加できる。",
            [
                ("空の初期状態",     "s15a_bequest_empty.png"),
                ("フォーム入力済み", "s15b_bequest_form_filled.png"),
                ("1件保存後",        "s15c_bequest_item_saved.png"),
                ("2件保存後",        "s15d_bequest_two_items.png"),
            ],
            [
                "入力項目: 物品名（必須）/ 渡す相手（必須）/ 備考（任意）",
                "追加ボタンでリストに追加（APIへ即時POST）",
                "各アイテムに削除ボタン",
            ]
        ),
        (
            "S16: デジタル資産タブ",
            "SNSアカウント・サブスクリプション等のデジタル資産を記録する。デジタル資産とサブスクリプションを同一タブで管理。",
            [
                ("空の初期状態",           "s16a_digital_empty.png"),
                ("デジタル資産追加後",     "s16b_digital_saved.png"),
                ("サブスクリプション欄",   "s16c_digital_subscription_area.png"),
            ],
            [
                "デジタル資産入力: サービス名（必須）/ アカウント / 死後の処理 / 備考",
                "サブスクリプション入力: サービス名（必須）/ 月額料金 / 解約方法 / 備考",
                "2種類のフォームが縦に並ぶレイアウト",
            ]
        ),
        (
            "S17: 緊急連絡先タブ",
            "緊急時に連絡すべき人物を記録する。優先順位付きで複数件登録できる。",
            [
                ("空の初期状態",     "s17a_contacts_empty.png"),
                ("フォーム入力済み", "s17b_contact_form_filled.png"),
                ("1件保存後",        "s17c_contact_saved.png"),
            ],
            [
                "入力項目: 名前（必須）/ 続柄 / 電話番号 / メールアドレス / 備考",
                "priority フィールドで表示順を制御",
            ]
        ),
        (
            "S18: ペットタブ",
            "飼っているペットの情報と、死後の世話を頼みたい人を記録する。",
            [
                ("空の初期状態",     "s18a_pets_empty.png"),
                ("フォーム入力済み", "s18b_pet_form_filled.png"),
                ("1件保存後",        "s18c_pet_saved.png"),
            ],
            [
                "入力項目: ペット名（必須）/ 種類 / 病歴 / 性格 / 世話を頼む人 / 備考",
            ]
        ),
        (
            "S19: 家族へのメッセージタブ",
            "家族へ残すメッセージを自由記述で入力する。変更後1秒で自動保存される。",
            [
                ("空の初期状態",     "s19a_message_empty.png"),
                ("メッセージ入力後", "s19b_message_typed.png"),
            ],
            [
                "入力項目: テキストエリア（自由記述）",
                "変更後1秒で自動保存（ヘッダーに「保存中...」表示）",
            ]
        ),
    ]),

    # ══════════════════════════════════════
    # 認証ガード
    # ══════════════════════════════════════
    ("authguard", "認証ガード・セキュリティ", [
        (
            "S20: ログアウト・認証リダイレクト",
            "ログアウト後または未ログイン状態で保護ページにアクセスすると /login へリダイレクトされる。",
            [
                ("ログアウト後（ログイン画面）",         "s20a_after_logout.png"),
                ("ダッシュボードへ未認証アクセス→リダイレクト", "s20b_auth_redirect.png"),
                ("終活ページへ未認証アクセス→リダイレクト",     "s20c_shukatsu_redirect.png"),
            ],
            [
                "PrivateRoute コンポーネントが認証状態をチェック",
                "未認証の場合は /login へ Navigate",
                "保護対象: /dashboard, /memorials/*, /shukatsu, /estate/*, /ending-note",
                "非保護: /login, /register, /m/:slug（公開墓誌）",
            ]
        ),
    ]),
]

# ─── HTML 生成 ────────────────────────────────────────────────
def generate():
    today = datetime.date.today().strftime("%Y年%m月%d日")

    # ── TOC ──────────────────────────────
    toc_items = []
    for sid, stitle, subsections in SCREENS:
        toc_items.append(f'<li><a href="#{sid}">{stitle}</a><ul>')
        for sub in subsections:
            sub_id = sub[0].replace(":", "").replace(" ", "-").replace("/", "-")
            toc_items.append(f'  <li><a href="#{sub_id}">{sub[0]}</a></li>')
        toc_items.append("</ul></li>")
    toc_html = "\n".join(toc_items)

    # ── セクション本文 ─────────────────────
    body_parts = []
    for sid, stitle, subsections in SCREENS:
        body_parts.append(f'<section id="{sid}" class="screen-group">')
        body_parts.append(f'<h2 class="group-title">{stitle}</h2>')

        for sub in subsections:
            sub_title, sub_desc, screenshots, notes = sub
            sub_id = sub_title.replace(":", "").replace(" ", "-").replace("/", "-")

            body_parts.append(f'<div id="{sub_id}" class="screen-section">')
            body_parts.append(f'<h3 class="screen-title">{sub_title}</h3>')
            body_parts.append(f'<p class="screen-desc">{sub_desc}</p>')

            # screenshots
            n = len(screenshots)
            if n == 1:
                cap, fname = screenshots[0]
                body_parts.append('<div class="shots shots-1">')
                body_parts.append(f'<figure>{img_tag(fname, cap)}<figcaption>{cap}</figcaption></figure>')
                body_parts.append('</div>')
            elif n == 2:
                body_parts.append('<div class="shots shots-2">')
                for cap, fname in screenshots:
                    body_parts.append(f'<figure>{img_tag(fname, cap)}<figcaption>{cap}</figcaption></figure>')
                body_parts.append('</div>')
            else:
                # 3+ : 2列グリッド
                body_parts.append('<div class="shots shots-grid">')
                for cap, fname in screenshots:
                    body_parts.append(f'<figure>{img_tag(fname, cap)}<figcaption>{cap}</figcaption></figure>')
                body_parts.append('</div>')

            # notes
            if notes:
                body_parts.append('<div class="notes"><ul>')
                for note in notes:
                    body_parts.append(f'<li>{note}</li>')
                body_parts.append('</ul></div>')

            body_parts.append('</div>')  # screen-section

        body_parts.append('</section>')  # screen-group

    body_html = "\n".join(body_parts)

    # ── 最終 HTML ────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Digital Memorial – 画面仕様書</title>
<style>
  /* ─── Reset & Base ─── */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif;
         font-size: 14px; line-height: 1.7; color: #1a1a1a; background: #f6f7f9; }}
  a {{ color: #1a5c38; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* ─── Layout ─── */
  .layout {{ display: flex; min-height: 100vh; }}

  /* ─── Sidebar TOC ─── */
  .sidebar {{
    position: sticky; top: 0; height: 100vh; overflow-y: auto;
    width: 240px; flex-shrink: 0;
    background: #1a2e22; color: #c8e6d0; padding: 24px 0;
    font-size: 12.5px;
  }}
  .sidebar-logo {{ padding: 0 20px 20px; font-size: 14px; font-weight: 700;
                   color: #fff; border-bottom: 1px solid #2e4a38; }}
  .sidebar-logo span {{ display: block; font-size: 10px; color: #7fb88f; margin-top: 2px; }}
  .sidebar nav {{ padding: 12px 0; }}
  .sidebar nav ul {{ list-style: none; }}
  .sidebar nav > ul > li {{ margin-bottom: 4px; }}
  .sidebar nav > ul > li > a {{
    display: block; padding: 7px 20px; color: #c8e6d0; font-weight: 600;
    font-size: 12px; letter-spacing: 0.03em;
  }}
  .sidebar nav > ul > li > a:hover {{ background: #243d2c; color: #fff; }}
  .sidebar nav ul ul {{ padding-left: 8px; }}
  .sidebar nav ul ul li a {{
    display: block; padding: 4px 20px; color: #8fbf9a; font-size: 11.5px;
  }}
  .sidebar nav ul ul li a:hover {{ color: #c8e6d0; }}

  /* ─── Main ─── */
  .main {{ flex: 1; max-width: 1100px; padding: 40px 48px; }}

  /* Cover */
  .cover {{
    background: linear-gradient(135deg, #1a5c38, #2e7d50);
    border-radius: 12px; padding: 48px 56px; color: #fff; margin-bottom: 48px;
  }}
  .cover h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 8px; }}
  .cover .meta {{ font-size: 13px; opacity: 0.8; margin-top: 12px; }}
  .cover .meta span {{ margin-right: 24px; }}

  /* Section group */
  .screen-group {{ margin-bottom: 60px; }}
  .group-title {{
    font-size: 20px; font-weight: 800; color: #1a5c38;
    border-bottom: 3px solid #1a5c38; padding-bottom: 8px; margin-bottom: 32px;
  }}

  /* Screen section */
  .screen-section {{
    background: #fff; border-radius: 12px; padding: 32px 36px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 28px;
  }}
  .screen-title {{
    font-size: 16px; font-weight: 700; color: #111; margin-bottom: 8px;
  }}
  .screen-desc {{ font-size: 13.5px; color: #555; margin-bottom: 24px; line-height: 1.8; }}

  /* Screenshots */
  .shots {{ display: grid; gap: 20px; margin-bottom: 24px; }}
  .shots-1 {{ grid-template-columns: minmax(0, 680px); }}
  .shots-2 {{ grid-template-columns: repeat(2, 1fr); }}
  .shots-grid {{ grid-template-columns: repeat(2, 1fr); }}

  figure {{ display: flex; flex-direction: column; gap: 8px; }}
  figure img {{
    width: 100%; border-radius: 8px; border: 1px solid #dde0e6;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
  }}
  figcaption {{
    font-size: 12px; color: #777; text-align: center;
    background: #f8f9fa; padding: 4px 8px; border-radius: 4px;
  }}

  /* No image placeholder */
  .no-img {{
    background: #f3f4f6; border: 1px dashed #d1d5db; border-radius: 8px;
    padding: 40px; text-align: center; color: #9ca3af; font-size: 12px;
  }}

  /* Notes */
  .notes {{
    background: #f0fdf4; border-left: 4px solid #1a5c38;
    border-radius: 0 8px 8px 0; padding: 16px 20px;
  }}
  .notes ul {{ list-style: none; }}
  .notes ul li {{
    font-size: 12.5px; color: #374151; padding: 3px 0;
    display: flex; gap: 8px;
  }}
  .notes ul li::before {{ content: "•"; color: #1a5c38; font-weight: bold; flex-shrink: 0; }}

  /* Back to top */
  .back-top {{
    display: inline-block; margin-top: 8px; font-size: 12px; color: #9ca3af;
  }}

  /* Print */
  @media print {{
    .sidebar {{ display: none; }}
    .main {{ padding: 16px; max-width: 100%; }}
    .screen-section {{ break-inside: avoid; page-break-inside: avoid; }}
    .shots-2, .shots-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="layout">
  <!-- ── Sidebar ── -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      Digital Memorial
      <span>画面仕様書</span>
    </div>
    <nav>
      <ul>
        {toc_html}
      </ul>
    </nav>
  </aside>

  <!-- ── Main ── -->
  <main class="main">
    <div class="cover">
      <h1>Digital Memorial<br>画面仕様書</h1>
      <div class="meta">
        <span>作成日: {today}</span>
        <span>対象バージョン: Phase 1</span>
        <span>画面数: 20</span>
        <span>スクリーンショット: 62枚</span>
      </div>
    </div>

    {body_html}
  </main>
</div>
</body>
</html>
"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_FILE) // 1024
    print(f"生成完了: {OUT_FILE}")
    print(f"ファイルサイズ: {size_kb} KB")


if __name__ == "__main__":
    generate()
