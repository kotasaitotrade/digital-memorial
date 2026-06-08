"""
Google Drive ストレージ統合。
- SQLite DB: 起動時にDriveからダウンロード、定期的にアップロード
- ファイルアップロード: Drive に保存して公開URL返却
"""
import os
import io
import json
import logging
from .config import settings

logger = logging.getLogger(__name__)

DB_FILENAME = "memorial.db"


def _get_service():
    """Drive サービスを返す。token_json 未設定なら None。"""
    if not settings.google_drive_token_json:
        return None
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        token_data = json.loads(settings.google_drive_token_json)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", ["https://www.googleapis.com/auth/drive"]),
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error(f"Drive 認証失敗: {e}")
        return None


# ─── DB 同期 ──────────────────────────────────────────────

def download_db(local_path: str) -> bool:
    """Drive から memorial.db をダウンロード。見つからない場合は False。"""
    if not settings.google_drive_db_folder_id:
        return False
    service = _get_service()
    if not service:
        return False
    try:
        results = service.files().list(
            q=f"name='{DB_FILENAME}' and '{settings.google_drive_db_folder_id}' in parents and trashed=false",
            fields="files(id,name)",
            pageSize=1,
        ).execute()
        files = results.get("files", [])
        if not files:
            logger.info("Drive に memorial.db が見つかりません（初回起動）")
            return False
        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        with io.FileIO(local_path, "wb") as fh:
            from googleapiclient.http import MediaIoBaseDownload
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        logger.info(f"Drive から DB ダウンロード完了: {local_path}")
        return True
    except Exception as e:
        logger.error(f"DB ダウンロード失敗: {e}")
        return False


def upload_db(local_path: str) -> bool:
    """local_path の DB を Drive にアップロード（上書き）。"""
    if not settings.google_drive_db_folder_id:
        return False
    if not os.path.exists(local_path):
        return False
    service = _get_service()
    if not service:
        return False
    try:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(local_path, mimetype="application/octet-stream", resumable=True)
        # 既存ファイル検索
        results = service.files().list(
            q=f"name='{DB_FILENAME}' and '{settings.google_drive_db_folder_id}' in parents and trashed=false",
            fields="files(id)",
            pageSize=1,
        ).execute()
        files = results.get("files", [])
        if files:
            service.files().update(
                fileId=files[0]["id"],
                media_body=media,
            ).execute()
        else:
            service.files().create(
                body={"name": DB_FILENAME, "parents": [settings.google_drive_db_folder_id]},
                media_body=media,
                fields="id",
            ).execute()
        logger.info("Drive に DB アップロード完了")
        return True
    except Exception as e:
        logger.error(f"DB アップロード失敗: {e}")
        return False


# ─── ファイルアップロード ──────────────────────────────────

def upload_file(fileobj, filename: str, content_type: str) -> str | None:
    """
    ファイルを Drive にアップロードして公開 URL を返す。
    Drive 未設定なら None。
    """
    if not settings.google_drive_uploads_folder_id:
        return None
    service = _get_service()
    if not service:
        return None
    try:
        import tempfile
        import uuid
        from googleapiclient.http import MediaIoBaseUpload

        unique_name = f"{uuid.uuid4().hex}_{filename}"
        media = MediaIoBaseUpload(fileobj, mimetype=content_type, resumable=True)
        file_meta = {
            "name": unique_name,
            "parents": [settings.google_drive_uploads_folder_id],
        }
        created = service.files().create(
            body=file_meta,
            media_body=media,
            fields="id",
        ).execute()
        file_id = created["id"]
        # 全員が閲覧可能に設定
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        # 画像・動画は直接表示URL
        url = f"https://drive.google.com/uc?export=view&id={file_id}"
        logger.info(f"Drive アップロード完了: {url}")
        return url
    except Exception as e:
        logger.error(f"ファイルアップロード失敗: {e}")
        return None
