from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from ..database import get_db
from ..models.memorial import Memorial, MemorialMedia
from ..models.user import User
from ..schemas.memorial import MemorialCreate, MemorialUpdate, MemorialResponse, MemorialPublic
from ..services.auth import get_password_hash, pwd_context
from ..services.qr import generate_qr_code
from .auth import get_current_user

router = APIRouter(tags=["memorial"])


@router.post("/memorials", response_model=MemorialResponse)
def create_memorial(data: MemorialCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = Memorial(
        owner_id=current_user.id,
        name=data.name,
        birth_date=data.birth_date,
        death_date=data.death_date,
        biography=data.biography,
        message=data.message,
        is_public=data.is_public,
        password_hash=get_password_hash(data.password) if data.password else None,
    )
    db.add(memorial)
    db.commit()
    db.refresh(memorial)
    qr_path = generate_qr_code(memorial.slug)
    memorial.qr_code_path = qr_path
    db.commit()
    db.refresh(memorial)
    return memorial


@router.get("/memorials", response_model=List[MemorialResponse])
def list_memorials(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Memorial).filter(Memorial.owner_id == current_user.id).all()


@router.get("/memorials/{memorial_id}", response_model=MemorialResponse)
def get_memorial(memorial_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_user.id).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")
    return memorial


@router.put("/memorials/{memorial_id}", response_model=MemorialResponse)
def update_memorial(memorial_id: int, data: MemorialUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_user.id).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")
    update_data = data.model_dump(exclude_none=True)
    if "password" in update_data:
        memorial.password_hash = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(memorial, field, value)
    db.commit()
    db.refresh(memorial)
    return memorial


@router.delete("/memorials/{memorial_id}")
def delete_memorial(memorial_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_user.id).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")
    db.delete(memorial)
    db.commit()
    return {"ok": True}


@router.get("/m/{slug}", response_model=MemorialPublic)
def view_memorial_public(slug: str, password: str = None, db: Session = Depends(get_db)):
    memorial = db.query(Memorial).filter(Memorial.slug == slug).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")
    if not memorial.is_public:
        if not memorial.password_hash or not password or not pwd_context.verify(password, memorial.password_hash):
            raise HTTPException(status_code=403, detail="Password required")
    return memorial


@router.post("/memorials/{memorial_id}/media")
def upload_media(memorial_id: int, file: UploadFile = File(...), caption: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_user.id).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")

    upload_dir = f"uploads/media/{memorial_id}"
    os.makedirs(upload_dir, exist_ok=True)

    import uuid
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    disk_path = os.path.join(upload_dir, safe_name)
    with open(disk_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # フルURLで保存（クロスオリジン・同一オリジン両対応）
    from ..config import settings as _s
    url_path = f"{_s.base_url}/uploads/media/{memorial_id}/{safe_name}"

    media_type = "image" if file.content_type.startswith("image") else "video"
    media = MemorialMedia(memorial_id=memorial_id, file_path=url_path, media_type=media_type, caption=caption)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.delete("/memorials/{memorial_id}/media/{media_id}")
def delete_media(memorial_id: int, media_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_user.id).first()
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")
    media = db.query(MemorialMedia).filter(MemorialMedia.id == media_id, MemorialMedia.memorial_id == memorial_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    # URLからディスクパスを復元して削除
    import urllib.parse
    parsed_path = urllib.parse.urlparse(media.file_path).path.lstrip("/")
    if os.path.exists(parsed_path):
        os.remove(parsed_path)
    db.delete(media)
    db.commit()
    return {"ok": True}
