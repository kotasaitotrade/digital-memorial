---
title: Digital Memorial
emoji: 🕊️
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Digital Memorial — デジタル墓誌

QRコードから故人の墓誌ページにアクセスできるWebアプリ。

## 機能

- 墓誌ページの作成・管理（故人情報・略歴・写真）
- QRコード自動生成（樹木葬プレート・一般墓向け）
- パスワード保護による非公開設定
- スマートフォン対応のレスポンシブUI

## 技術スタック

- **Backend**: Python / FastAPI / SQLAlchemy / SQLite
- **Frontend**: React / TypeScript / Vite

## ローカル開発

### バックエンド

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
