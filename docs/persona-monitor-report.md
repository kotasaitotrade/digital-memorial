# ペルソナ型モニター レポート

**実施日**: 2026-06-02  
**スクリプト**: `e2e/persona_monitor.py`  
**スクリーンショット**: `docs/screenshots/persona-monitor/`

---

## 実施概要

6ペルソナによるシナリオ型E2Eモニタリングを実施。28枚のスクリーンショットを取得し、3件の課題を発見・修正した。

---

## ペルソナ別実施結果

### ペルソナ1: 初心者ユーザー

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| 新規登録フォーム確認 | ✅ 正常 | `p1-beginner-s1-register-01-empty.png` |
| 空送信バリデーション | ✅ 正常 | `p1-beginner-s1-register-02-empty-submit.png` |
| パスワード強度チェック | ✅ 正常 | `p1-beginner-s1-register-03-weak-password.png` |
| ログインフォーム確認 | ✅ 正常 | `p1-beginner-s1-login-01-empty.png` |
| 誤パスワードエラー表示 | ✅ 正常 | `p1-beginner-s1-login-02-wrong-password.png` |
| ダッシュボード初回表示 | ✅ 正常 | `p1-beginner-s1-dashboard-01-after-login.png` |
| オンボーディングモーダル | ✅ 表示確認 | `p1-beginner-s1-dashboard-02-onboarding-modal.png` |
| 終活ノートへの導線 | ✅ リンク24本確認 | `p1-beginner-s1-shukatsu-01-overview.png` |

**課題**: なし（スクリプトの誤検知1件を修正）

---

### ペルソナ2: 日常利用ユーザー

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| エンディングノート概要 | ✅ 正常 | `p2-daily-s2-ending-note-01-overview.png` |
| 医療タブ切替 | ✅ 正常 | `p2-daily-s2-ending-note-02-medical-tab.png` |
| チェックリスト進捗 | ✅ スコア表示確認 | `p2-daily-s2-checklist-01-progress.png` |
| デジタルキー概要 | ✅ 正常 | `p2-daily-s2-digital-key-01-overview.png` |

**課題**: [B-001] 自動保存インジケーターが初回ロード時に非表示 → **修正済み**

---

### ペルソナ3: 急いでいるユーザー

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| 墓誌作成フォーム | ✅ 正常 | `p3-hurry-s3-memorial-create-01-form.png` |
| 相続計算一覧 | ✅ 正常 | `p3-hurry-s3-estate-01-list.png` |
| ダッシュボードナビゲーション | ✅ 正常 | `p3-hurry-s3-navigation-01-dashboard.png` |

**課題**: なし

---

### ペルソナ4: 境界値・異常系ユーザー

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| 長文入力（5000字）| ✅ エラーなし | `p4-edge-s4-long-text-01-after-input.png` |
| 404ページ表示 | ✅ 専用ページ表示 | `p4-edge-s4-404-01-not-found.png` |
| 不正slug公開ページ | ✅ エラー表示 | `p4-edge-s4-public-invalid-01-not-found.png` |
| ログアウト後の認証ガード | ✅ /loginへリダイレクト | `p4-edge-s4-auth-guard-01-redirect.png` |
| 不正解除キーURL | ✅ エラー表示 | `p4-edge-s4-unlock-invalid-01-error.png` |

**課題**: なし（全シナリオ合格）

---

### ペルソナ5: アクセシビリティ重視ユーザー

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| フォームラベル確認（ログイン）| ✅ label/id/htmlFor 対応済み | `p5-a11y-s5-login-01-form-labels.png` |
| キーボードナビゲーション | ✅ Tab順序正常 | `p5-a11y-s5-login-02-keyboard-nav.png` |
| アイコンのみボタン確認 | ✅（修正後） | `p5-a11y-s5-dashboard-01-buttons.png` |

**課題**: [B-002] ✕ ボタン群に `aria-label` なし → **修正済み**（OnboardingModal / MemorialForm / PublicMemorialPage / EstatePlanPage）

---

### ペルソナ6: 管理者・運用担当者

| シナリオ | 結果 | スクリーンショット |
|---------|------|-----------------|
| アカウント設定概要 | ✅ 正常 | `p6-admin-s6-account-01-overview.png` |
| 削除確認ダイアログ | ✅ 確認ステップあり | `p6-admin-s6-account-02-delete-confirm.png` |
| 活動ログ表示 | ✅ 表示確認 | `p6-admin-s6-activity-log-01-log-displayed.png` |
| データエクスポート | ✅ ボタン確認 | `p6-admin-s6-export-01-buttons.png` |
| 2FA設定確認 | ✅ 設定可能 | `p6-admin-s6-2fa-01-setup-available.png` |

**課題**: なし

---

## 発見・修正した課題

| ID | カテゴリ | ペルソナ | 内容 | 優先度 | 対応 |
|----|---------|---------|------|--------|------|
| B-001 | UX | 日常利用 | エンディングノートの自動保存インジケーターが初回ロード時に非表示 | Medium | ✅ 修正済み（「自動保存」バッジを常時表示） |
| B-002 | a11y | アクセシビリティ | ✕ ボタン4箇所に `aria-label` なし | Medium | ✅ 修正済み（4ファイルに `aria-label` 追加） |

---

## 修正内容詳細

### B-001: 自動保存インジケーター常時表示
**ファイル**: `frontend/src/pages/EndingNotePage.tsx`  
**変更**: 未保存状態でも「自動保存」バッジを表示するよう条件分岐を変更

```tsx
// Before
{savedLabel && <span style={...}>{savedLabel}</span>}

// After
<span style={saving ? s.savingLabel : (savedLabel ? s.savedLabel : s.autoSaveBadge)}>
  {savedLabel || "自動保存"}
</span>
```

### B-002: ✕ ボタンへの `aria-label` 追加
**変更ファイル**:
- `frontend/src/components/OnboardingModal.tsx` → `aria-label="閉じる"`
- `frontend/src/components/MemorialForm.tsx` → `aria-label="削除"`
- `frontend/src/pages/PublicMemorialPage.tsx` → `aria-label="閉じる"`
- `frontend/src/pages/EstatePlanPage.tsx` → `aria-label="キャンセル"` / `aria-label="削除"`

---

## 良好点（問題なし）

- 登録・ログインフォームのlabel/id/htmlFor/autoComplete 対応済み（前回修正）
- 404エラーページ表示対応済み（前回修正）
- ログアウト後の認証ガード（/login リダイレクト）正常動作
- 長文入力（5000字）でもエラーなし・自動保存正常
- アカウント削除に確認ステップあり
- キーボードナビゲーション（Tab順序）正常

---

## 次サイクルへの引き継ぎ課題

以下は即修正でなく検討事項として記録:

| 課題 | 内容 | 優先度 |
|------|------|--------|
| C-001 | パスワード確認入力フィールドが登録フォームにない | Medium |
| C-002 | エンディングノートにパスワード忘れ/リセット機能がない | Low |
| C-003 | 墓誌一覧に写真サムネイルが未実装（現在は名前の頭文字） | Medium |
