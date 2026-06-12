# 墓じまい計画 E2Eバグ検証レポート

**実施日時**: 2026-06-12  
**対象URL**: https://kotsaito-digital-memorial.hf.space/hakajimai  
**合計**: 27 件 / ✅ PASS: 27 件 / ❌ FAIL: 0 件

---

## 発見・修正したバグ

| バグID | 重要度 | 内容 | 修正内容 |
|---|---|---|---|
| BUG-01 | High | `GET /hakajimai` が 500 エラー — DBの `sect`・`grave_info` カラムが不足 | `main.py` に起動時マイグレーション（`ALTER TABLE ADD COLUMN`）を追加 |
| BUG-02 | High | チェックボックスをクリックしても UI が即座に反映されない | `toggleCheck` に楽観的更新（`setPlan`）を追加。APIレスポンス前に即時反映 |
| BUG-03 | Medium | 通常モードのダッシュボードから墓じまいページへの導線なし（かんたんモードのみ） | ダッシュボードに「墓じまい計画」バナーを追加（全モード表示） |

## 機能一覧・テスト結果

| ID | 機能 | 結果 | 詳細 | スクリーンショット |
|---|---|---|---|---|
| H00 | API GET /hakajimai レスポンス確認 | ✅ | fields OK=True, checklist=10件, cost=6件 | - |
| H01 | API PUT /hakajimai リセット保存 | ✅ | kuyou_method='' | - |
| H02 | ログイン・ダッシュボード表示 | ✅ | ダッシュボード確認 | H02_dashboard.png |
| H03 | 墓じまいページ表示 | ✅ | タイトル確認 | H03_hakajimai_initial.png |
| H04 | 6タブ全表示確認 | ✅ | 供養方法/お墓の情報/手続き/費用/テンプレート/家族へ | H04_tabs.png |
| H05 | 供養方法カード 6種表示 | ✅ | 全6種確認 | H05_method_cards.png |
| H06 | 供養方法 選択・保存 | ✅ | API: kuyou_method='永代供養墓' | H06_method_selected.png |
| H07 | 宗派選択・ヒント表示・保存 | ✅ | API: sect='浄土宗' / ヒント表示OK | H07_sect_selected.png |
| H08 | 「その他」選択でテキストエリア・保存 | ✅ | API: kuyou_detail='樹木葬と散骨を組み合わせる' | H08_other_textarea.png |
| H09 | お墓の情報タブ 入力フィールド表示 | ✅ | 入力フィールド確認 | H09_grave_tab.png |
| H10 | 墓地名 入力・保存 | ✅ | API: cemetery_name='東京都立 多磨霊園' | H10_grave_saved.png |
| H11 | 手続きチェックリスト表示 | ✅ | 進捗: 0 / 10 完了 | H11_checklist_tab.png |
| H12 | チェックボックス ON・保存 | ✅ | API: is_done=True / 表示: '1 / 10 完了' | H12_check_toggled.png |
| H13 | チェックボックス OFF・保存 | ✅ | API: is_done=False | H13_check_untoggled.png |
| H14 | カテゴリ別グループ 5種表示 | ✅ | 準備/行政/供養/工事/改葬先 | H14_category_groups.png |
| H15 | 費用タブ・合計行表示 | ✅ | 'あなたの目安: 431,500 円' | H15_cost_tab.png |
| H16 | 費用 金額変更・保存 | ✅ | API: cost_items[0].amount=50000 | H16_cost_saved.png |
| H17 | 費用合計 リアルタイム更新 | ✅ | 変更前 → 変更後で金額変動確認 | H17_cost_total_updated.png |
| H18 | テンプレート 4件表示 | ✅ | 全4件タイトル確認 | H18_template_tab.png |
| H19 | テンプレートコピーボタン | ✅ | ✓ コピー済み 表示確認 | H19_template_copy.png |
| H20 | 家族へのメッセージタブ表示 | ✅ | テキストエリア確認 | H20_message_tab.png |
| H21 | 家族メッセージ 入力・保存 | ✅ | API: message_to_family 保存確認 | H21_message_saved.png |
| H22 | 手続きタブラベルのカウンタ更新 | ✅ | タブテキスト: '手続き (1/10)' | H22_tab_counter.png |
| H23 | リロード後データ復元 | ✅ | API: kuyou_method='その他', sect='浄土宗' | H23_after_reload.png |
| H24 | ← ダッシュボードへの遷移 | ✅ | /dashboard に遷移確認 | H24_back_nav.png |
| H25 | ダッシュボードに墓じまい導線あり | ✅ | 「墓じまい計画」リンク確認 | H25_dashboard_link.png |
| H26 | 保存インジケーター動作・API確認 | ✅ | 散骨 保存確認: True | H26_saved_indicator.png |

---

## 失敗項目

- なし（全項目 PASS）
