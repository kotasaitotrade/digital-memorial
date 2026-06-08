# 残タスク一覧

> 最終更新: 2026-06-04

---

## 🔴 優先度高（デプロイ完了に必要）

### 1. Hugging Face Spaces デプロイ

**状態**: コード準備済み・Space 未作成

**必要なもの**: HF アカウント + Write トークン（[settings/tokens](https://huggingface.co/settings/tokens)）

CLIで自動化済みにしたい場合は HF トークンを Claude に渡せば自動実行可。

手動でやる場合:
1. [huggingface.co/new-space](https://huggingface.co/new-space)
   - Owner: `kotasaitotrade` / Name: `digital-memorial` / SDK: `Docker` / Public
2. Files → Link repository → `kotasaitotrade/digital-memorial`
3. Settings → Repository secrets に以下を設定:

| Secret キー | 値 |
|------------|-----|
| `GOOGLE_DRIVE_TOKEN_JSON` | `~/system_trade/config/KOTASAITO_drive_token.json` の中身 |
| `GOOGLE_DRIVE_DB_FOLDER_ID` | `19qxgONBY30xCDF7OBr_gUxuo1FL5Yktg` |
| `GOOGLE_DRIVE_UPLOADS_FOLDER_ID` | `10KXhTye1mWng4tItp5TVGQgKIhXKFHwm` |
| `SECRET_KEY` | 任意のランダム文字列（例: `openssl rand -hex 32` の出力） |
| `BASE_URL` | `https://kotasaitotrade-digital-memorial.hf.space` |

---

### 2. 動作確認（HF デプロイ後）

- [ ] トップページ表示
- [ ] ユーザー登録・ログイン
- [ ] 墓誌作成・写真アップロード（Drive 保存確認）
- [ ] Drive フォルダに `memorial.db` が同期されているか確認
- [ ] サーバー再起動後もデータが残るか確認

---

## 🟡 優先度中（動作確認後）

### 3. PostgreSQL 移行（Supabase）

SQLite → PostgreSQL でデータの永続性・パフォーマンスを向上。

1. [supabase.com](https://supabase.com) でプロジェクト作成（無料・永久）
2. Settings → Database → Connection string (URI) をコピー
3. HF Spaces Secrets に追加:
   - `DATABASE_URL` = `postgresql://postgres:パスワード@db.xxx.supabase.co:5432/postgres`
4. Space を再起動 → 自動でテーブル作成

> ⚠️ SQLite から PostgreSQL に移行する際、既存データは一度消えます。  
> 移行スクリプトが必要な場合は別途作成。

---

### 4. メール通知設定（SMTP）

現在はメール送信が無効（コンソールログのみ）。

HF Spaces Secrets に追加:
| キー | 値 |
|-----|-----|
| `SMTP_HOST` | `smtp.gmail.com` 等 |
| `SMTP_USER` | メールアドレス |
| `SMTP_PASSWORD` | アプリパスワード |
| `SMTP_FROM` | 送信元アドレス |

---

## 🟢 優先度低（将来対応）

### 5. カスタムドメイン設定
- HF Spaces Pro ($9/月) にするとカスタムドメイン設定可能
- または Cloudflare Workers + カスタムドメインでプロキシ

### 6. 写真サムネイル（墓誌一覧）
- 現在は名前の頭文字表示
- `C-003` として improvement_proposals.md に記録済み

### 7. パスワードリセット機能
- `C-002` として記録済み

### 8. パスワード確認フィールド（登録フォーム）
- `C-001` として記録済み

---

## ✅ 完了済み（このセッション）

- [x] ペルソナ型 E2E モニター実装（6ペルソナ・28スクリーンショット）
- [x] a11y 修正（フォーム label/id/htmlFor・✕ボタン aria-label）
- [x] 404 ページ追加
- [x] エンディングノート「自動保存」バッジ常時表示
- [x] Cloudflare R2 ストレージ対応
- [x] Google Drive ストレージ統合（DB 5分同期・ファイルアップロード）
- [x] Drive フォルダ作成済み（DB: `19qxgONBY30xCDF7OBr_gUxuo1FL5Yktg` / Uploads: `10KXhTye1mWng4tItp5TVGQgKIhXKFHwm`）
- [x] HF Spaces 用 Dockerfile 整備
- [x] render.yaml 整備（Render デプロイ設定）
- [x] 全 E2E テスト 12/12 パス確認
