"""
ファイルストレージ抽象レイヤー。
R2設定があれば Cloudflare R2、なければローカルディスクに保存。
"""
import os
import shutil
import uuid
from .config import settings


def _s3():
    if not all([settings.r2_account_id, settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket_name]):
        return None
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def save_upload(fileobj, original_filename: str, prefix: str, content_type: str = "application/octet-stream") -> str:
    """ファイルを保存して公開URLを返す。優先順: R2 → Drive → ローカル"""
    ext = os.path.splitext(original_filename or "")[1] or ""
    key = f"{prefix}/{uuid.uuid4().hex}{ext}"

    # 1. Cloudflare R2
    s3 = _s3()
    if s3:
        s3.upload_fileobj(fileobj, settings.r2_bucket_name, key,
                          ExtraArgs={"ContentType": content_type})
        return f"{settings.r2_public_url}/{key}"

    # 2. Google Drive
    from .drive_storage import upload_file as drive_upload
    url = drive_upload(fileobj, os.path.basename(key), content_type)
    if url:
        return url

    # 3. ローカル
    local_path = os.path.join(settings.upload_dir, key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        shutil.copyfileobj(fileobj, f)
    return f"{settings.base_url}/uploads/{key}"


def save_upload_path(filepath: str, key: str, content_type: str = "application/octet-stream") -> str:
    """既存ファイルパスからアップロードして公開URLを返す。優先順: R2 → Drive → ローカル"""
    # 1. R2
    s3 = _s3()
    if s3:
        s3.upload_file(filepath, settings.r2_bucket_name, key,
                       ExtraArgs={"ContentType": content_type})
        return f"{settings.r2_public_url}/{key}"

    # 2. Drive
    from .drive_storage import upload_file as drive_upload
    with open(filepath, "rb") as f:
        url = drive_upload(f, os.path.basename(key), content_type)
    if url:
        return url

    # 3. ローカル（既にそこにある）
    return f"{settings.base_url}/uploads/{key}"
