from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.activity_log import ActivityLog
from ..schemas.user import (
    UserCreate, UserResponse, Token, PasswordChange, AccountDelete,
    UserPreferences, TOTPVerify, TOTPDisable,
)
from ..models.memorial import Memorial
from ..models.shukatsu import (
    EstatePlan, FamilyMember, Asset, EndingNote, BequestItem,
    DigitalAsset, Subscription, EmergencyContact, Pet, ChecklistCompletion,
)
from ..services.auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user_from_token, get_user_by_email, pwd_context,
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = get_current_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def log_activity(db: Session, user_id: int, action: str, target: str = None, detail: str = None, ip: str = None):
    entry = ActivityLog(user_id=user_id, action=action, target=target, detail=detail, ip_address=ip)
    db.add(entry)
    db.commit()


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    # 最終ログイン日時を更新
    user.last_login_at = datetime.utcnow()
    db.commit()
    # 活動ログ
    ip = request.client.host if request.client else None
    log_activity(db, user.id, "login", detail="ログイン成功", ip=ip)
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not pwd_context.verify(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    log_activity(db, current_user.id, "change_password")
    return {"ok": True}


@router.patch("/preferences")
def update_preferences(data: UserPreferences, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.font_size is not None:
        if data.font_size not in ("small", "medium", "large", "xlarge"):
            raise HTTPException(status_code=400, detail="Invalid font_size")
        current_user.font_size = data.font_size
    if data.simple_mode is not None:
        current_user.simple_mode = data.simple_mode
    db.commit()
    db.refresh(current_user)
    log_activity(db, current_user.id, "update_preferences", detail=str(data.dict(exclude_none=True)))
    return {"ok": True, "font_size": current_user.font_size, "simple_mode": current_user.simple_mode}


# ─── 2FA (TOTP) ─────────────────────────────────────────────

@router.post("/totp/setup")
def totp_setup(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import pyotp, qrcode, io, base64
    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    db.commit()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="Digital Memorial")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"totp_secret": secret, "qr_data_url": f"data:image/png;base64,{b64}"}


@router.post("/totp/verify")
def totp_verify(data: TOTPVerify, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import pyotp
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not set up")
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.totp_enabled = True
    db.commit()
    log_activity(db, current_user.id, "enable_2fa")
    return {"ok": True, "totp_enabled": True}


@router.post("/totp/disable")
def totp_disable(data: TOTPDisable, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import pyotp
    if not pwd_context.verify(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    if current_user.totp_enabled and current_user.totp_secret:
        totp = pyotp.TOTP(current_user.totp_secret)
        if not totp.verify(data.code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    log_activity(db, current_user.id, "disable_2fa")
    return {"ok": True, "totp_enabled": False}


# ─── 活動ログ ────────────────────────────────────────────────

@router.get("/activity-log")
def get_activity_log(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "action": l.action,
            "target": l.target,
            "detail": l.detail,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


# ─── データエクスポート ──────────────────────────────────────

@router.get("/export")
def export_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    def _row(obj, exclude=None):
        exclude = exclude or set()
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in exclude}

    memorials = db.query(Memorial).filter(Memorial.owner_id == current_user.id).all()
    memorial_data = []
    for m in memorials:
        d = _row(m, exclude={"password_hash"})
        d["media"] = [_row(med) for med in m.media]
        memorial_data.append(d)

    estate_plans = db.query(EstatePlan).filter(EstatePlan.user_id == current_user.id).all()
    estate_data = []
    for ep in estate_plans:
        d = _row(ep)
        d["family_members"] = [_row(fm) for fm in ep.family_members]
        d["assets"] = [_row(a) for a in ep.assets]
        estate_data.append(d)

    ending_note = db.query(EndingNote).filter(EndingNote.user_id == current_user.id).first()
    note_data = None
    if ending_note:
        note_data = _row(ending_note)
        note_data["bequest_items"] = [_row(b) for b in ending_note.bequest_items]
        note_data["digital_assets"] = [_row(da) for da in ending_note.digital_assets]
        note_data["subscriptions"] = [_row(s) for s in ending_note.subscriptions]
        note_data["emergency_contacts"] = [_row(ec) for ec in ending_note.emergency_contacts]
        note_data["pets"] = [_row(p) for p in ending_note.pets]

    checklist = [_row(c) for c in db.query(ChecklistCompletion).filter(ChecklistCompletion.user_id == current_user.id).all()]

    export = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": {"id": current_user.id, "email": current_user.email, "name": current_user.name},
        "memorials": memorial_data,
        "estate_plans": estate_data,
        "ending_note": note_data,
        "checklist": checklist,
    }

    def default_serializer(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    import json
    content = json.dumps(export, ensure_ascii=False, default=default_serializer, indent=2)
    log_activity(db, current_user.id, "export_data", detail="JSON export")
    return JSONResponse(content=json.loads(content), headers={
        "Content-Disposition": "attachment; filename=digital-memorial-export.json"
    })


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """エンディングノート + 相続資産を CSV で出力（中村美代 要望）"""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["セクション", "項目", "値"])

    ending_note = db.query(EndingNote).filter(EndingNote.user_id == current_user.id).first()
    if ending_note:
        writer.writerow(["エンディングノート", "葬儀スタイル", ending_note.funeral_style or ""])
        writer.writerow(["エンディングノート", "宗教", ending_note.religion or ""])
        writer.writerow(["エンディングノート", "お花の希望", ending_note.funeral_flower_type or ""])
        writer.writerow(["エンディングノート", "埋葬方法", ending_note.burial_preference or ""])
        writer.writerow(["エンディングノート", "戒名希望", ending_note.kaimyo_preference or ""])
        writer.writerow(["エンディングノート", "好きな音楽", ending_note.favorite_music or ""])
        writer.writerow(["エンディングノート", "好きな映画・本", ending_note.favorite_movies or ""])
        writer.writerow(["エンディングノート", "家族へのメッセージ", ending_note.family_message or ""])
        for pet in ending_note.pets:
            writer.writerow(["ペット", f"{pet.name}（{pet.species or ''}）", f"引き継ぎ先: {pet.caretaker or ''} 獣医: {pet.vet_name or ''}"])
        for ec in ending_note.emergency_contacts:
            writer.writerow(["緊急連絡先", ec.name, f"{ec.relationship or ''} {ec.phone or ''} {ec.email or ''}"])
        for sub in ending_note.subscriptions:
            writer.writerow(["サブスク", sub.service_name, f"月額{sub.monthly_fee or 0}円 解約方法: {sub.cancellation_method or ''}"])

    estate_plans = db.query(EstatePlan).filter(EstatePlan.user_id == current_user.id).all()
    for ep in estate_plans:
        writer.writerow(["相続計画", "タイトル", ep.title])
        for a in ep.assets:
            writer.writerow(["資産", a.name, f"種別:{a.asset_type} 評価額:{a.estimated_value}円"])
        for fm in ep.family_members:
            writer.writerow(["家族", fm.name, f"関係:{fm.relationship}"])

    content = output.getvalue()
    log_activity(db, current_user.id, "export_data", detail="CSV export")
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=digital-memorial-export.csv"},
    )


@router.delete("/me")
def delete_account(data: AccountDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not pwd_context.verify(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    db.delete(current_user)
    db.commit()
    return {"ok": True}
