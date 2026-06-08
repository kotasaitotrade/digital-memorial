"""
画面仕様書を Google Drive にアップロードして共有リンクを発行するスクリプト。

使い方:
  cd /Users/user01/system_trade
  python3 /Users/user01/digital-memorial/docs/upload_to_drive.py

前提:
  - /Users/user01/system_trade/src/library/google_drive_api.py が存在すること
  - config/KOTASAITO_drive_token.json が有効であること
"""
import sys
import os

# system_trade の library を参照
LIBRARY_ROOT = os.path.expanduser("~/system_trade/src")
sys.path.insert(0, LIBRARY_ROOT)
sys.path.insert(0, os.path.join(LIBRARY_ROOT, "library"))

from library import google_drive_api

SPEC_FILE = os.path.join(os.path.dirname(__file__), "screen_spec.html")
DRIVE_NAME = "digital_memorial_画面仕様書.html"


def main():
    if not os.path.exists(SPEC_FILE):
        print(f"ERROR: 仕様書が見つかりません: {SPEC_FILE}")
        sys.exit(1)

    print("Google Drive へアップロード中...")
    manager = google_drive_api.GoogleDriveManager()

    file_id = manager.upload_file(
        file_path=SPEC_FILE,
        file_name=DRIVE_NAME,
        overwrite=True,
    )

    if not file_id:
        print("ERROR: アップロードに失敗しました")
        sys.exit(1)

    # 「リンクを知っている全員が閲覧可能」に設定
    manager.service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    meta = manager.service.files().get(
        fileId=file_id,
        fields="webViewLink",
    ).execute()

    link = meta.get("webViewLink", "")
    print(f"\n共有リンク: {link}")
    return link


if __name__ == "__main__":
    main()
