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
- スマートフォン対応レスポンシブUI
- 戻るボタン付きナビゲーション

## 技術スタック

- **フロントエンド**: Streamlit（Python）
- **バックエンド**: SQLAlchemy / SQLite
- **ホスティング**: Streamlit Community Cloud

## Streamlit Community Cloud へのデプロイ

1. [share.streamlit.io](https://share.streamlit.io) にGitHubアカウントでログイン
2. 「New app」→ このリポジトリ `kotasaitotrade/digital-memorial` を選択
3. Main file: `streamlit_app.py`
4. Advanced settings → Secrets に以下を追加:
   ```toml
   BASE_URL = "https://あなたのアプリURL.streamlit.app"
   DATABASE_URL = "sqlite:///./memorial.db"
   SECRET_KEY = "your-secret-key"
   ```
5. Deploy!

## ローカル開発

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

アプリ: http://localhost:8501

## 公開ページURL形式

```
https://your-app.streamlit.app/?slug={スラッグ}
```
QRコードはこのURLを自動で生成します。
