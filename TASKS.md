# タスク一覧

> 最終更新: 2026-06-04  
> 詳細な機能提案は [docs/improvement_proposals.md](docs/improvement_proposals.md) を参照

---

## 🚀 STEP 1: 本番デプロイ（最優先）

### 1-1. Hugging Face Spaces Space 作成

**状態**: コード・Dockerfile 準備済み / Space 未作成

1. [huggingface.co/new-space](https://huggingface.co/new-space)
   - Owner: `kotasaitotrade` / Name: `digital-memorial` / SDK: `Docker` / Public
2. Files → **Link repository** → `kotasaitotrade/digital-memorial`
3. Settings → Repository secrets に以下を追加:

| Secret キー | 値 | 備考 |
|------------|-----|------|
| `SECRET_KEY` | `openssl rand -hex 32` の出力 | JWT署名キー |
| `BASE_URL` | `https://kotasaitotrade-digital-memorial.hf.space` | 公開URL |
| `GOOGLE_DRIVE_TOKEN_JSON` | `~/system_trade/config/KOTASAITO_drive_token.json` の中身 | Drive認証 |
| `GOOGLE_DRIVE_DB_FOLDER_ID` | `19qxgONBY30xCDF7OBr_gUxuo1FL5Yktg` | 作成済み |
| `GOOGLE_DRIVE_UPLOADS_FOLDER_ID` | `10KXhTye1mWng4tItp5TVGQgKIhXKFHwm` | 作成済み |

> HF Write トークンを Claude に渡せば CLI で全自動実行可。

### 1-2. デプロイ後の動作確認

- [ ] トップページ表示 (`https://kotasaitotrade-digital-memorial.hf.space`)
- [ ] ユーザー登録・ログイン
- [ ] 墓誌作成・写真アップロード → Drive フォルダに保存されるか確認
- [ ] `memorial.db` が Drive の `digital-memorial-db` フォルダに同期されるか確認
- [ ] Space 再起動後もデータが残るか確認

---

## 🔧 STEP 2: インフラ強化（デプロイ確認後）

### 2-1. PostgreSQL 移行（Supabase・無料永久）

1. [supabase.com](https://supabase.com) → New project 作成
2. Settings → Database → Connection string (URI) をコピー
3. HF Secrets に追加: `DATABASE_URL` = `postgresql://postgres:パスワード@db.xxx.supabase.co:5432/postgres`
4. Space 再起動 → 自動でテーブル作成される

> ⚠️ SQLite → PostgreSQL 移行時、既存データはリセット。  
> 移行スクリプトが必要な場合は Claude に依頼。

### 2-2. メール通知 SMTP 設定

HF Secrets に追加:

| キー | 値 |
|-----|-----|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_USER` | 送信元メールアドレス |
| `SMTP_PASSWORD` | Gmail アプリパスワード |
| `SMTP_FROM` | 送信元表示アドレス |

有効になる機能: デッドマンスイッチ通知 / 信頼者への解除通知 / 年次リマインダー

---

## 📋 STEP 3: 機能追加バックログ

improvement_proposals.md の ★★★ 最優先リストより、実装コストの低い順に並べた推奨順序。

### フェーズ A（UI改善・実装簡単）

| タスク | 提案ID | 概要 |
|--------|--------|------|
| 公開URLコピーボタン | F-058 | 墓誌編集ページにURLコピーボタン追加 |
| 写真キャプションUI | F-051 | API対応済みだがUIが未実装 |
| セクション完成度インジケーター | F-045 | 終活ノートの各セクションに進捗バー |
| チェックインボタン常時表示 | F-017 | デジタルキーページに目立つボタン |
| 相続計算結果→修正ボタン | F-062 | 結果ページから入力に戻れない問題を解消 |
| 家族リスト折りたたみ | F-065 | 相続計画の家族リストが長くなる問題 |
| パスワード確認フィールド | C-001 | 登録フォームにパスワード再入力欄追加 |
| パスワードリセット機能 | C-002 | メールリンクでパスワードリセット |

### フェーズ B（機能追加・中程度）

| タスク | 提案ID | 概要 |
|--------|--------|------|
| 印刷用PDF出力 | F-004/D-001 | エンディングノート・相続計算をPDF化 |
| 資産円グラフ・棒グラフ | F-060/F-061 | 相続計算結果のビジュアル化 |
| 入力ガイド表示 | F-001 | 高齢者向けにフォームの入力例・説明を追加 |
| チェックイン未実施リマインダー | F-018/N-001 | 一定期間チェックインなし時にメール通知 |
| 葬儀希望プリセット | F-003 | エンディングノートに選択肢のクイック入力 |
| 写真サムネイル（墓誌一覧） | C-003 | 現在は名前の頭文字、実際の写真に変更 |

### フェーズ C（大規模・要設計）

| タスク | 提案ID | 概要 |
|--------|--------|------|
| 家族アカウント共有 | F-029/B-001 | 複数ユーザーで終活ノートを共同編集 |
| 遺族向けポータル | F-040/F-041 | 鍵解除後に遺族がすべき手続きリスト |
| PWA対応 | M-001 | スマホホーム画面に追加・オフライン対応 |
| TOTPバックアップコード | F-002/S-005 | 2FA設定後にロックアウトされる問題の解消 |
| 訪問者メッセージ機能 | F-054 | 墓誌公開ページから遺族へメッセージ送信 |

---

## 🟢 STEP 4: 将来対応（余裕があれば）

- **カスタムドメイン**: HF Spaces Pro ($9/月) またはCloudflare Workersでプロキシ
- **モバイルファーストレイアウト** (M-002/U-002): SP最適化
- **ヘルプ・FAQページ** (F-073): よくある質問
- **全データJSONエクスポート** (D-003): GDPR対応・データポータビリティ
- **ブルートフォース対策** (S-007): レートリミット実装
- **不審ログイン通知** (S-002): 新規IP/デバイスからのログイン通知

---

## ✅ 完了済み（2026-06-02〜04）

- [x] ペルソナ型 E2E モニター実装（6ペルソナ・28スクリーンショット・`e2e/persona_monitor.py`）
- [x] a11y 修正（フォーム label/id/htmlFor・✕ボタン aria-label 4箇所）
- [x] 404 ページ追加（App.tsx catch-all route）
- [x] エンディングノート「自動保存」バッジ常時表示
- [x] WillSimulatorPage 保存後ホームボタン追加
- [x] Cloudflare R2 ストレージ対応（storage.py）
- [x] Google Drive ストレージ統合（drive_storage.py・DB 5分同期）
- [x] Drive フォルダ作成済み
  - DB: `19qxgONBY30xCDF7OBr_gUxuo1FL5Yktg`
  - Uploads: `10KXhTye1mWng4tItp5TVGQgKIhXKFHwm`
- [x] HF Spaces 用 Dockerfile 整備
- [x] render.yaml 整備（Render デプロイ対応）
- [x] 全 E2E テスト 12/12 パス確認（23分）
- [x] TypeScript 型チェック パス
- [x] docs/persona-monitor-report.md 作成
- [x] docs/improvement_proposals.md v3 更新
- [x] README 全面更新・backend/.env.example 整備
