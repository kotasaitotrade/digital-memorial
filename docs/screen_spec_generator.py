"""
画面仕様書 HTML ジェネレーター
e2e/screenshots/ 内の s*.png を読み込んで見やすい仕様書を生成する。
実行方法: cd /Users/user01/digital-memorial && python3 docs/screen_spec_generator.py
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

def img_tag(name: str, alt: str = "") -> str:
    b64 = img_b64(name)
    if not b64:
        return f'<div class="no-img">スクリーンショット未取得: {name}</div>'
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" loading="lazy" />'

# ─── スクリーン定義 ──────────────────────────────────────────────
# (section_id, section_title, subsections)
# subsection = (title, description, [(caption, filename), ...], notes)

SCREENS = [

    # ══════════════════════════════════════════════════════
    # 認証
    # ══════════════════════════════════════════════════════
    ("auth", "認証", [
        (
            "S01: ログイン",
            "メールアドレスとパスワードでサインインする画面。"
            "未ログイン状態でダッシュボード等の保護ページにアクセスすると自動でここへリダイレクトされる。",
            [
                ("初期表示",          "s01a_login.png"),
                ("認証失敗エラー表示", "s01b_login_error.png"),
            ],
            [
                "URL: /login",
                "入力項目: メールアドレス（email・必須）、パスワード（password・必須）",
                "バリデーション: 両フィールドが空の場合は submit ボタンが機能しない（required 属性）",
                "認証失敗時: ページに留まり「メールアドレスまたはパスワードが正しくありません」を表示",
                "認証成功時: /dashboard へリダイレクト",
                "下部に「アカウントを作成する」リンク（/register）",
            ]
        ),
        (
            "S02: ユーザー登録",
            "新規アカウントを作成する画面。お名前・メールアドレス・パスワードを入力して登録する。",
            [
                ("空フォーム（初期状態）", "s02a_register.png"),
                ("入力済み状態",           "s02b_register_filled.png"),
            ],
            [
                "URL: /register",
                "入力項目: お名前（text・必須）、メールアドレス（email・必須）、パスワード（password・8文字以上）",
                "登録成功後: /dashboard へ遷移し、初回ログイン時はオンボーディングモーダルを表示",
                "既存メールアドレス使用時: 「このメールアドレスは既に使用されています」エラー",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # ダッシュボード
    # ══════════════════════════════════════════════════════
    ("dashboard", "ダッシュボード", [
        (
            "S03: ダッシュボード（墓誌一覧）",
            "ログイン後のトップ画面。登録した墓誌の一覧と終活ノートへの導線を表示する。"
            "初回ログイン時はオンボーディングモーダルが表示される。",
            [
                ("墓誌 0 件（初期状態）",  "s03a_dashboard_empty.png"),
                ("墓誌 1 件登録後",        "s03b_dashboard_memorial.png"),
                ("QR コードモーダル表示",  "s03c_dashboard_qr_modal.png"),
            ],
            [
                "URL: /dashboard",
                "墓誌 0 件時: 空状態メッセージ + 「新しい墓誌を作成する」ボタン",
                "墓誌カード要素: 故人名・生没年月日・操作ボタン（編集 / QR / 削除）",
                "QR モーダル: 公開 URL（/m/:slug）の QR コードをポップアップ表示。コピーボタンあり",
                "終活ノートバナー: /shukatsu へのリンクカード",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # 墓誌管理
    # ══════════════════════════════════════════════════════
    ("memorial", "墓誌管理", [
        (
            "S04: 墓誌作成フォーム",
            "新しい墓誌を作成するフォーム。故人の基本情報・略歴・ご家族へのメッセージ・メディアを入力できる。",
            [
                ("空フォーム（初期状態）", "s04a_memorial_form_empty.png"),
                ("入力済み状態",           "s04b_memorial_form_filled.png"),
            ],
            [
                "URL: /memorials/new",
                "入力項目: お名前（必須）/ 生年月日 / 没年月日 / 享年（自動計算）/ 略歴 / ご家族へのメッセージ",
                "公開設定: 「全員に公開」「パスワード付き公開」「非公開」の3択",
                "パスワード設定時: パスワード入力欄が表示される",
                "保存後: /memorials/:id/edit（編集画面）へ遷移",
            ]
        ),
        (
            "S05: 墓誌編集フォーム",
            "既存の墓誌を編集する画面。S04 と同一コンポーネントで既存データが初期値として設定済みの状態で表示される。",
            [
                ("編集画面",         "s05a_memorial_edit.png"),
                ("写真管理エリア",   "s05b_memorial_edit_photo.png"),
            ],
            [
                "URL: /memorials/:id/edit",
                "既存データが各フィールドに初期表示される",
                "写真・動画アップロード: 複数ファイル対応（image/* / video/*）",
                "アップロード済みメディアは一覧表示され、キャプション編集・削除ができる",
                "保存成功時: 「保存しました」トーストを 3 秒間表示",
            ]
        ),
        (
            "S06: QR コード印刷ページ",
            "墓誌の公開 URL を QR コードで印刷するためのページ。墓石への貼り付けなどを想定した印刷特化レイアウト。",
            [
                ("QR 印刷ページ", "s06_print_qr.png"),
            ],
            [
                "URL: /memorials/:id/print-qr",
                "公開 URL（/m/:slug）の QR コードを大きく表示",
                "ナビゲーションを非表示にした印刷用スタイルを適用",
            ]
        ),
        (
            "S07: 公開墓誌ページ",
            "QR コードを読み取ったアクセスや直接 URL 共有で表示する公開ページ。ログイン不要で誰でも閲覧可能（パスワード設定時を除く）。",
            [
                ("公開ページ（上部）", "s07a_public_memorial_top.png"),
                ("公開ページ（下部）", "s07b_public_memorial_bottom.png"),
            ],
            [
                "URL: /m/:slug",
                "認証不要（ログイン不要）",
                "表示要素: 故人名・生没年月日・享年・略歴・写真ギャラリー・ご家族へのメッセージ",
                "パスワード設定時: 閲覧前にパスワード入力ダイアログを表示",
                "存在しない slug へのアクセス: 「墓誌が見つかりません」メッセージを表示",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # 終活ノート
    # ══════════════════════════════════════════════════════
    ("shukatsu", "終活ノート（ダッシュボード）", [
        (
            "S08-a: 終活ダッシュボード",
            "終活機能の入口ページ。完了率スコアカード・クイックリンク・チェックリストを一覧表示する。",
            [
                ("スコアカード部分", "s08a_shukatsu_scorecard.png"),
                ("ページ全体",       "s08b_shukatsu_full.png"),
            ],
            [
                "URL: /shukatsu",
                "スコアカード: チェックリストの完了率をパーセント + SVG ゲージで表示",
                "クイックリンク: 「相続の棚卸し」「エンディングノート」「墓誌の管理」の 3 リンク",
                "チェックリスト: カテゴリタブフィルター付き一覧（チェック状態は API で永続化）",
            ]
        ),
        (
            "S08-b: チェックリスト カテゴリ別表示",
            "9 カテゴリ（すべて / 相続 / 遺言 / 医療 / 葬儀 / デジタル / 人間関係 / ペット / 思い出）で"
            "フィルタリングした表示。",
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
                "チェック状態は PATCH /api/checklist/toggle で即時保存",
                "優先度バッジ: 必須（赤）/ 推奨（橙）/ 任意（グレー）",
                "未完了の項目には「入力する →」の機能別リンクを表示",
                "完了済みアイテム: チェックマーク + 打ち消し線でスタイル変更",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # 相続の棚卸し（ウィザード）
    # ══════════════════════════════════════════════════════
    ("estate", "相続の棚卸し", [
        (
            "S09: 相続計画一覧",
            "作成済み相続計画の一覧。新規作成ボタンから計画名・基本情報を入力して 4 ステップウィザードを開始する。",
            [
                ("一覧画面",         "s09a_estate_list.png"),
                ("新規作成フォーム", "s09b_estate_create_form.png"),
            ],
            [
                "URL: /estate",
                "計画カード要素: 計画名・家族人数・財産件数・最終更新日",
                "アクション: ① 家族構成 / ② 財産の棚卸し / ③ 計算結果を見る / 削除",
                "新規作成: 計画名（必須）・総資産額・総負債額・メモを入力して作成",
            ]
        ),
        (
            "S10: 家族構成入力（Step 1）",
            "4 ステップウィザードの Step 1。法定相続人となり得る家族を続柄別に追加する。"
            "入力した家族構成に基づいて Step 3 で相続分が自動計算される。",
            [
                ("空の初期状態",    "s10a_family_empty.png"),
                ("配偶者追加後",    "s10b_family_spouse_added.png"),
                ("子 2 名追加後",   "s10c_family_children_added.png"),
            ],
            [
                "URL: /estate/:planId/family",
                "ウィザードヘッダー: ① 家族構成 → ② 財産の棚卸し → ③ 計算結果 → ④ 遺言書",
                "対応続柄: 配偶者 / 子（養子・欠格・相続放棄フラグあり）/ 孫（代襲・親 ID 指定）",
                "          / 親 / 祖父母 / 兄弟姉妹（半血フラグあり）/ 甥姪（代襲）",
                "子が死亡または欠格の場合のみ「孫（代襲）」セクションが出現",
                "「② 財産の棚卸しへ →」ボタンで Step 2 へ進む",
            ]
        ),
        (
            "S11: 財産入力（Step 2）",
            "4 ステップウィザードの Step 2。不動産・預貯金・有価証券・生命保険・退職金・その他資産と"
            "負債を種別ごとに入力する。",
            [
                ("空の初期状態",           "s11a_asset_empty.png"),
                ("不動産追加後",           "s11b_asset_realestate_added.png"),
                ("不動産＋預貯金追加後",   "s11c_asset_bank_added.png"),
                ("負債追加後",             "s11d_asset_debt_added.png"),
                ("資産合計サマリー",       "s11e_asset_full.png"),
            ],
            [
                "URL: /estate/:planId/assets",
                "各資産タイプに「＋ ○○を追加」ボタン",
                "生命保険金: 「みなし相続財産（非課税枠あり）」チェックボックスを個別設定できる",
                "ページ下部に「資産合計 / 負債合計 / 正味遺産額（= 資産 − 負債）」を自動計算表示",
                "「保存して計算結果を見る →」で Step 3 へ進む",
            ]
        ),
        (
            "S12: 相続計算結果（Step 3）",
            "4 ステップウィザードの Step 3。法定相続人・相続分・遺留分・基礎控除の計算結果を表示する。"
            "結果を PDF として出力する機能と、遺言書シミュレーターへの導線もここにある。",
            [
                ("結果画面（上部）",         "s12a_result_top.png"),
                ("結果画面（全体）",         "s12b_result_full.png"),
                ("遺留分・基礎控除（下部）", "s12c_result_bottom.png"),
            ],
            [
                "URL: /estate/:planId/result",
                "相続人ごとの相続分（分数 + パーセント + 金額）を一覧表示",
                "代襲相続・半血兄弟・養子・相続放棄・欠格・胎児を自動考慮",
                "遺留分: 配偶者・子・親のみ対象（兄弟姉妹には遺留分なし）",
                "基礎控除: 3,000 万円 + 600 万円 × 法定相続人数 を計算し、課税対象かを表示",
                "ボタン（4 種）: ← 家族構成を修正する / ④ 遺言書シミュレーター → / 🖨 PDF 出力 / チェックリストに戻る",
                "PDF 出力: window.print() を呼び出し。@media print でヘッダー・ボタン類を非表示にして印刷ダイアログを表示",
            ]
        ),
        (
            "S21: 遺言書シミュレーター（Step 4）",
            "4 ステップウィザードの Step 4。法定相続分と希望配分を比較しながら遺言書の配分草案を作成する。"
            "遺留分チェック機能付き。作成した草案を遺言書テンプレートとして PDF 出力できる。",
            [
                ("初期表示（配分テーブル）", "s21a_will_default.png"),
                ("希望配分を入力した状態",   "s21b_will_modified.png"),
                ("付言事項を入力した状態",   "s21c_will_memo.png"),
            ],
            [
                "URL: /estate/:planId/will",
                "配分テーブル列: 相続人名 / 続柄 / 法定相続分（金額） / 遺留分 / 希望配分（数値入力）/ 差額",
                "遺留分警告: 希望配分が遺留分を下回る相続人に赤色でアラートを表示",
                "配分バランス: 希望配分の合計が正味遺産額と一致しない場合に「差額 ○円 未配分」を表示",
                "付言事項: テキストエリアで自由記述（「なぜこの配分にしたか」等）",
                "保存ボタン: PUT /api/estate-plans/:id/will で配分と付言を保存",
                "PDF 出力: 保存後に window.print() を呼び出し。印刷専用レイアウトで正式な遺言書テンプレートを表示",
                "印刷テンプレート内容: 遺言書タイトル / 配分一覧 / 付言事項 / 署名欄 / 作成日 / 法的免責事項",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # エンディングノート
    # ══════════════════════════════════════════════════════
    ("ending", "エンディングノート", [
        (
            "S13: 医療・介護タブ",
            "エンディングノートのデフォルトタブ。延命治療・心肺蘇生・臓器提供・介護場所などの希望を"
            "選択式で記録する。変更は 1 秒後に自動保存され、ヘッダーに保存時刻が表示される。",
            [
                ("初期状態（未入力）", "s13a_medical_default.png"),
                ("入力済み状態",       "s13b_medical_filled.png"),
            ],
            [
                "URL: /ending-note",
                "タブ: 医療・介護 / 葬儀 / 形見分け / デジタル資産 / 緊急連絡先 / ペット / 家族へのメッセージ",
                "RadioGroup（ボタン選択）: 延命治療 / 心肺蘇生 / 胃ろう / 臓器提供 / 介護・終末期の希望場所",
                "テキストエリア: 臓器提供の詳細 / かかりつけ医情報 / 服用中の薬 / 医療に関する備考",
                "自動保存: onChange 後 1 秒 debounce で PUT /api/ending-note を呼び出し",
                "保存後: ヘッダーに「○ 秒前に保存」を表示（リアルタイム更新）",
                "🖨 PDF 出力ボタン: ヘッダー右上に常時表示。全タブの内容を縦 1 ページにまとめた印刷ビューを表示",
            ]
        ),
        (
            "S14: 葬儀タブ",
            "葬儀スタイル・宗教・流してほしい音楽・葬儀に関する要望を記録する。",
            [
                ("初期状態",     "s14a_funeral_default.png"),
                ("入力済み状態", "s14b_funeral_filled.png"),
            ],
            [
                "葬儀スタイル選択肢: 家族葬 / 一般葬 / 直葬 / お任せします",
                "テキスト入力: 宗教・宗派 / 流してほしい曲 / 葬儀に関する要望",
                "遺影写真: 画像ファイルアップロード対応（upload 後プレビュー表示）",
                "変更は 1 秒後に自動保存",
            ]
        ),
        (
            "S15: 形見分けタブ",
            "「誰に何を渡したいか」を品目・受取人・備考で記録する。複数件追加できる。",
            [
                ("空の初期状態",       "s15a_bequest_empty.png"),
                ("フォーム入力済み",   "s15b_bequest_form_filled.png"),
                ("1 件保存後",         "s15c_bequest_item_saved.png"),
                ("2 件保存後",         "s15d_bequest_two_items.png"),
            ],
            [
                "入力項目: 物品名（必須）/ 渡す相手の名前（必須）/ 備考（任意）",
                "「追加する」ボタンで POST /api/ending-note/bequest を呼び出し即時保存",
                "各アイテムに削除ボタン（DELETE /api/ending-note/bequest/:id）",
            ]
        ),
        (
            "S16: デジタル資産タブ",
            "SNS アカウント・サブスクリプションサービスなどのデジタル資産を記録する。"
            "デジタル資産とサブスクリプションを同一タブで管理する。",
            [
                ("空の初期状態",         "s16a_digital_empty.png"),
                ("デジタル資産追加後",   "s16b_digital_saved.png"),
                ("サブスクリプション欄", "s16c_digital_subscription_area.png"),
            ],
            [
                "デジタル資産: サービス名（必須）/ アカウント名 / 死後の処理方法 / 備考",
                "サブスクリプション: サービス名（必須）/ 月額料金 / 解約方法 / 備考",
                "2 種のフォームが縦に並ぶレイアウト。それぞれ追加・削除が独立して機能",
            ]
        ),
        (
            "S17: 緊急連絡先タブ",
            "緊急時・相続手続き時に連絡すべき人物を記録する。複数件・優先順位付きで登録できる。",
            [
                ("空の初期状態",     "s17a_contacts_empty.png"),
                ("フォーム入力済み", "s17b_contact_form_filled.png"),
                ("1 件保存後",       "s17c_contact_saved.png"),
            ],
            [
                "入力項目: 名前（必須）/ 続柄 / 電話番号 / メールアドレス / 備考",
                "priority フィールドで表示順を制御（数値、小さいほど上位）",
                "各アイテムに削除ボタン",
            ]
        ),
        (
            "S18: ペットタブ",
            "飼っているペットの情報と、自分が亡くなった後の世話を引き継いでほしい人を記録する。",
            [
                ("空の初期状態",     "s18a_pets_empty.png"),
                ("フォーム入力済み", "s18b_pet_form_filled.png"),
                ("1 件保存後",       "s18c_pet_saved.png"),
            ],
            [
                "入力項目: ペット名（必須）/ 種類 / 病歴・かかりつけ医 / 性格・特徴 / 世話を頼む人 / 備考",
                "各アイテムに削除ボタン",
            ]
        ),
        (
            "S19: 家族へのメッセージタブ",
            "家族へ残すメッセージを自由記述で入力する。変更後 1 秒で自動保存される。",
            [
                ("空の初期状態",     "s19a_message_empty.png"),
                ("メッセージ入力後", "s19b_message_typed.png"),
            ],
            [
                "入力項目: テキストエリア（自由記述・文字数制限なし）",
                "変更後 1 秒で自動保存。ヘッダーに「○ 秒前に保存」を表示",
            ]
        ),
    ]),

    # ══════════════════════════════════════════════════════
    # 認証ガード・セキュリティ
    # ══════════════════════════════════════════════════════
    ("authguard", "認証ガード・セキュリティ", [
        (
            "S20: ログアウト・認証リダイレクト",
            "ログアウト後または未ログイン状態で保護ページにアクセスすると /login へリダイレクトされる。"
            "JWT の有効期限切れ（30 分）でも同様の動作となる。",
            [
                ("ログアウト後（ログイン画面）",               "s20a_after_logout.png"),
                ("ダッシュボードへ未認証アクセス → リダイレクト", "s20b_auth_redirect.png"),
                ("終活ページへ未認証アクセス → リダイレクト",     "s20c_shukatsu_redirect.png"),
            ],
            [
                "PrivateRoute コンポーネントが認証状態をチェックして未認証なら /login へ Navigate",
                "JWT 有効期限: 30 分（backend/app/config.py で設定）",
                "保護対象 URL: /dashboard, /memorials/*, /shukatsu, /estate/*, /ending-note",
                "非保護 URL: /login, /register, /m/:slug（公開墓誌）",
            ]
        ),
    ]),
]

# ─── HTML 生成 ────────────────────────────────────────────────────
def count_screenshots() -> int:
    total = 0
    for _, _, subs in SCREENS:
        for _, _, shots, _ in subs:
            total += len(shots)
    return total

def count_screens() -> int:
    return sum(len(subs) for _, _, subs in SCREENS)

def generate():
    today = datetime.date.today().strftime("%Y年%m月%d日")
    n_screens = count_screens()
    n_shots   = count_screenshots()

    # ── TOC ──────────────────────────────────────────────
    toc_items = []
    for sid, stitle, subs in SCREENS:
        toc_items.append(f'<li><a href="#{sid}" class="toc-group">{stitle}</a><ul>')
        for sub in subs:
            sub_id = sub[0].replace(":", "").replace(" ", "-").replace("/", "-")
            toc_items.append(f'  <li><a href="#{sub_id}">{sub[0]}</a></li>')
        toc_items.append("</ul></li>")
    toc_html = "\n".join(toc_items)

    # ── セクション本文 ──────────────────────────────────
    body_parts = []
    for sid, stitle, subs in SCREENS:
        body_parts.append(f'<section id="{sid}" class="screen-group">')
        body_parts.append(f'<h2 class="group-title">{stitle}</h2>')

        for sub in subs:
            sub_title, sub_desc, shots, notes = sub
            sub_id = sub_title.replace(":", "").replace(" ", "-").replace("/", "-")

            body_parts.append(f'<div id="{sub_id}" class="screen-section">')
            body_parts.append(f'<h3 class="screen-title">{sub_title}</h3>')
            body_parts.append(f'<p class="screen-desc">{sub_desc}</p>')

            # スクリーンショット
            n = len(shots)
            grid_cls = "shots-1" if n == 1 else ("shots-2" if n == 2 else "shots-grid")
            body_parts.append(f'<div class="shots {grid_cls}">')
            for cap, fname in shots:
                body_parts.append(
                    f'<figure>{img_tag(fname, cap)}'
                    f'<figcaption>{cap}</figcaption></figure>'
                )
            body_parts.append('</div>')

            # 仕様メモ
            if notes:
                body_parts.append('<div class="notes"><ul>')
                for note in notes:
                    body_parts.append(f'<li>{note}</li>')
                body_parts.append('</ul></div>')

            body_parts.append('</div>')  # screen-section
        body_parts.append('</section>')  # screen-group

    body_html = "\n".join(body_parts)

    # ── 最終 HTML ─────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Digital Memorial – 画面仕様書</title>
<style>
  /* ─ Reset ─ */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif;
    font-size: 14px; line-height: 1.75; color: #1a1a1a; background: #f4f5f7;
  }}
  a {{ color: #1a5c38; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* ─ Layout ─ */
  .layout {{ display: flex; min-height: 100vh; }}

  /* ─ Sidebar ─ */
  .sidebar {{
    position: sticky; top: 0; height: 100vh; overflow-y: auto;
    width: 248px; flex-shrink: 0;
    background: #162618; color: #b8dbc2; padding: 0;
    font-size: 12.5px;
    scrollbar-width: thin; scrollbar-color: #2e4a38 transparent;
  }}
  .sidebar-logo {{
    padding: 20px 20px 16px;
    background: #0f1f12;
    border-bottom: 1px solid #1e3a24;
  }}
  .sidebar-logo strong {{ display: block; font-size: 14px; color: #fff; font-weight: 700; }}
  .sidebar-logo span {{ display: block; font-size: 11px; color: #6aaa7e; margin-top: 3px; }}
  .sidebar nav {{ padding: 10px 0 24px; }}
  .sidebar nav ul {{ list-style: none; }}
  /* グループ見出し */
  .sidebar nav > ul > li {{ margin-bottom: 2px; }}
  .toc-group {{
    display: block; padding: 8px 20px 6px;
    color: #e0f0e5; font-weight: 700; font-size: 11.5px;
    letter-spacing: 0.04em; text-transform: uppercase;
    border-top: 1px solid #1e3624;
    margin-top: 6px;
  }}
  .toc-group:hover {{ background: #1e3624; color: #fff; }}
  /* サブ項目 */
  .sidebar nav ul ul {{ padding-left: 0; margin-bottom: 4px; }}
  .sidebar nav ul ul li a {{
    display: block; padding: 4px 20px 4px 28px;
    color: #7dbf8e; font-size: 11.5px; line-height: 1.5;
  }}
  .sidebar nav ul ul li a:hover {{ background: #1e3a24; color: #c8e6d0; }}

  /* ─ Main ─ */
  .main {{ flex: 1; min-width: 0; padding: 40px 52px 80px; max-width: 1120px; }}

  /* カバー */
  .cover {{
    background: linear-gradient(130deg, #163a22 0%, #22643a 60%, #1d7a46 100%);
    border-radius: 14px; padding: 48px 56px; color: #fff; margin-bottom: 52px;
    box-shadow: 0 4px 24px rgba(0,0,0,.15);
  }}
  .cover h1 {{ font-size: 30px; font-weight: 800; line-height: 1.3; letter-spacing: -0.02em; }}
  .cover .tagline {{ font-size: 14px; color: rgba(255,255,255,.7); margin-top: 10px; }}
  .cover .meta-row {{
    display: flex; gap: 0; margin-top: 28px;
    background: rgba(0,0,0,.18); border-radius: 10px; overflow: hidden;
  }}
  .cover .meta-item {{
    flex: 1; padding: 14px 20px; border-right: 1px solid rgba(255,255,255,.1);
    font-size: 12px; color: rgba(255,255,255,.65);
  }}
  .cover .meta-item:last-child {{ border-right: none; }}
  .cover .meta-item strong {{ display: block; font-size: 20px; color: #fff; font-weight: 800; margin-bottom: 2px; }}

  /* グループ見出し */
  .screen-group {{ margin-bottom: 64px; }}
  .group-title {{
    font-size: 18px; font-weight: 800; color: #163a22;
    border-bottom: 3px solid #1a5c38;
    padding-bottom: 10px; margin-bottom: 28px;
    display: flex; align-items: center; gap: 10px;
  }}
  .group-title::before {{
    content: ""; display: inline-block;
    width: 6px; height: 22px; background: #1a5c38; border-radius: 3px;
  }}

  /* 画面セクション */
  .screen-section {{
    background: #fff; border-radius: 12px; padding: 32px 36px;
    box-shadow: 0 1px 6px rgba(0,0,0,.07), 0 0 0 1px rgba(0,0,0,.04);
    margin-bottom: 24px;
  }}
  .screen-title {{
    font-size: 15px; font-weight: 700; color: #111;
    margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
  }}
  .screen-title::before {{
    content: ""; display: inline-block;
    width: 10px; height: 10px; background: #22a85a;
    border-radius: 2px; flex-shrink: 0;
  }}
  .screen-desc {{
    font-size: 13.5px; color: #444; margin-bottom: 24px; line-height: 1.85;
  }}

  /* スクリーンショットグリッド */
  .shots {{ display: grid; gap: 18px; margin-bottom: 24px; }}
  .shots-1 {{ grid-template-columns: minmax(0, 700px); }}
  .shots-2 {{ grid-template-columns: repeat(2, 1fr); }}
  .shots-grid {{ grid-template-columns: repeat(2, 1fr); }}

  figure {{ display: flex; flex-direction: column; gap: 0; }}
  figure img {{
    width: 100%; display: block;
    border-radius: 8px 8px 0 0;
    border: 1px solid #e0e3e8;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
  }}
  figcaption {{
    font-size: 12px; color: #666; text-align: center;
    background: #f5f6f8; border: 1px solid #e0e3e8; border-top: none;
    padding: 6px 10px; border-radius: 0 0 8px 8px;
    letter-spacing: 0.01em;
  }}
  .no-img {{
    background: #f9fafb; border: 1.5px dashed #d0d4db; border-radius: 8px;
    padding: 40px 20px; text-align: center; color: #9ca3af; font-size: 12px;
    aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center;
  }}

  /* 仕様メモ */
  .notes {{
    background: #f0fdf4; border-left: 4px solid #22a85a;
    border-radius: 0 10px 10px 0; padding: 16px 20px;
  }}
  .notes ul {{ list-style: none; display: flex; flex-direction: column; gap: 6px; }}
  .notes ul li {{
    font-size: 13px; color: #2d3a35; padding: 0;
    display: flex; gap: 8px; line-height: 1.6;
  }}
  .notes ul li::before {{
    content: "▸"; color: #22a85a; font-size: 11px;
    flex-shrink: 0; margin-top: 3px;
  }}

  /* 印刷 */
  @media print {{
    .sidebar {{ display: none; }}
    .main {{ padding: 16px; max-width: 100%; }}
    .cover {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .screen-section {{ break-inside: avoid; page-break-inside: avoid; box-shadow: none; border: 1px solid #ddd; }}
  }}
</style>
</head>
<body>
<div class="layout">

  <!-- ── サイドバー ── -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <strong>Digital Memorial</strong>
      <span>画面仕様書 v1.1</span>
    </div>
    <nav>
      <ul>
        {toc_html}
      </ul>
    </nav>
  </aside>

  <!-- ── メインコンテンツ ── -->
  <main class="main">

    <!-- カバー -->
    <div class="cover">
      <h1>Digital Memorial<br>画面仕様書</h1>
      <p class="tagline">デジタル遺産・終活支援サービス — Phase 1 全画面リファレンス</p>
      <div class="meta-row">
        <div class="meta-item"><strong>{n_screens}</strong>画面</div>
        <div class="meta-item"><strong>{n_shots}</strong>スクリーンショット</div>
        <div class="meta-item"><strong>Phase 1</strong>対象バージョン</div>
        <div class="meta-item"><strong>{today}</strong>最終更新</div>
      </div>
    </div>

    {body_html}

  </main>
</div>
</body>
</html>"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_FILE) // 1024
    print(f"生成完了: {OUT_FILE}")
    print(f"画面数: {n_screens}  スクリーンショット: {n_shots}  ファイルサイズ: {size_kb} KB")


if __name__ == "__main__":
    generate()
