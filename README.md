---
title: Digital Memorial
emoji: 🕊️
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Digital Memorial — デジタル墓誌・終活サポートアプリ

QRコードで故人の墓誌ページを公開できる終活サポートWebアプリ。

**→ 残タスク・デプロイ手順は [TASKS.md](TASKS.md) を参照**

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | React 18 + TypeScript + Vite |
| バックエンド | FastAPI (Python 3.11) |
| DB | SQLite（本番: PostgreSQL / Supabase） |
| ファイル保存 | ローカル → Google Drive → Cloudflare R2 の優先順で自動切替 |
| 認証 | JWT (python-jose) |
| スケジューラ | APScheduler（デッドマンスイッチ・DB同期） |
| テスト | pytest + Playwright (E2E) |
| デプロイ先 | Hugging Face Spaces (Docker) |

---

## ローカル開発環境構築

### 前提条件
- Python 3.11+
- Node.js 20+
- Git

### 1. リポジトリ取得

```bash
git clone https://github.com/kotasaitotrade/digital-memorial.git
cd digital-memorial
```

### 2. バックエンド起動

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # 必要に応じて編集
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### 3. フロントエンド起動

```bash
cd frontend
npm install
npm run dev
```

アプリ: http://localhost:5173

### 4. テスト実行

```bash
# E2Eテスト（バックエンド・フロントエンド両方起動してから）
cd /path/to/digital-memorial
python3 -m pytest e2e/beta_test.py -x -q

# ペルソナ型モニター（スクリーンショット付き）
python3 e2e/persona_monitor.py

# 画面仕様書再生成
python3 e2e/screen_spec_generator.py
```

---

## 環境変数一覧

`backend/.env.example` を参照。主要なもの：

| 変数 | 説明 | デフォルト |
|-----|------|-----------|
| `DATABASE_URL` | DB接続文字列 | `sqlite:///./memorial.db` |
| `SECRET_KEY` | JWT署名キー | `dev-secret-key` |
| `BASE_URL` | アプリの公開URL | `http://localhost:5173` |
| `CORS_ORIGINS` | 許可するオリジン | `http://localhost:5173,...` |
| `GOOGLE_DRIVE_TOKEN_JSON` | Drive OAuth2トークン(JSON文字列) | 空（Drive無効） |
| `GOOGLE_DRIVE_DB_FOLDER_ID` | DBバックアップ先DriveフォルダID | 空 |
| `GOOGLE_DRIVE_UPLOADS_FOLDER_ID` | ファイルアップロード先DriveフォルダID | 空 |
| `R2_ACCOUNT_ID` | Cloudflare R2アカウントID | 空（R2無効） |
| `R2_ACCESS_KEY_ID` | R2 APIキー | 空 |
| `R2_SECRET_ACCESS_KEY` | R2 シークレット | 空 |
| `R2_BUCKET_NAME` | R2バケット名 | 空 |
| `R2_PUBLIC_URL` | R2公開URL | 空 |
| `SMTP_HOST` | SMTPサーバー | 空（メール無効） |
| `SMTP_USER` | SMTPユーザー | 空 |
| `SMTP_PASSWORD` | SMTPパスワード | 空 |

---

## Google Drive 認証情報（別PCでの作業時）

以下のファイルが **`~/system_trade/config/`** に必要：

| ファイル | 用途 |
|---------|------|
| `KOTASAITO_credentials.json` | OAuth2クライアント情報 |
| `KOTASAITO_drive_token.json` | アクセス・リフレッシュトークン |

HF Spaces にデプロイする際は `KOTASAITO_drive_token.json` の**中身**を  
`GOOGLE_DRIVE_TOKEN_JSON` シークレットに設定する。

作成済みの Drive フォルダ：
- **DBフォルダ**: `19qxgONBY30xCDF7OBr_gUxuo1FL5Yktg` (`digital-memorial-db`)
- **Uploadsフォルダ**: `10KXhTye1mWng4tItp5TVGQgKIhXKFHwm` (`digital-memorial-uploads`)

---

## プロジェクト構成

```
digital-memorial/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPIアプリ・lifespan
│   │   ├── config.py        # 設定（環境変数）
│   │   ├── storage.py       # ファイル保存抽象（R2/Drive/ローカル）
│   │   ├── drive_storage.py # Google Drive統合（DB同期・アップロード）
│   │   ├── scheduler.py     # APScheduler（デッドマン・DB同期）
│   │   ├── database.py      # SQLAlchemy設定
│   │   ├── models/          # DBモデル
│   │   ├── routers/         # APIルーター
│   │   └── services/        # メール・QR生成等
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/           # 各画面
│   │   ├── components/      # 共通コンポーネント
│   │   ├── hooks/           # カスタムフック
│   │   └── lib/             # API・設定・ユーティリティ
│   └── package.json
├── e2e/
│   ├── beta_test.py         # E2Eテスト (12テスト)
│   ├── persona_monitor.py   # ペルソナ型モニター (6ペルソナ)
│   ├── capture_all_screens.py
│   └── screen_spec_generator.py
├── docs/
│   ├── screen_spec.md       # 自動生成画面仕様書
│   ├── improvement_proposals.md  # 改修提案書 v3
│   ├── persona-monitor-report.md # モニタリングレポート
│   └── screenshots/
├── Dockerfile               # HF Spaces用（FastAPI + React同梱）
├── render.yaml              # Render.com用デプロイ設定
├── TASKS.md                 # 残タスク一覧 ← 必読
├── REQUIREMENTS.md          # 要件定義書
└── DESIGN.md                # 設計書
```

---

## デプロイ（Hugging Face Spaces）

コードは準備済み。**[TASKS.md](TASKS.md)** の手順に従って Secrets を設定するだけ。

```
本番URL（予定）: https://kotasaitotrade-digital-memorial.hf.space
```

---

## ドキュメント

| ファイル | 内容 |
|---------|------|
| [TASKS.md](TASKS.md) | 残タスク・デプロイ手順 |
| [REQUIREMENTS.md](REQUIREMENTS.md) | 要件定義書 |
| [DESIGN.md](DESIGN.md) | 設計書 |
| [docs/improvement_proposals.md](docs/improvement_proposals.md) | 改修・新機能提案書 (v3) |
| [docs/screen_spec.md](docs/screen_spec.md) | 画面仕様書（自動生成） |
| [docs/persona-monitor-report.md](docs/persona-monitor-report.md) | ペルソナモニターレポート |
