from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, Token, PasswordChange, AccountDelete
from ..models.memorial import Memorial
from ..models.shukatsu import EstatePlan, FamilyMember, Asset, EndingNote, BequestItem, DigitalAsset, Subscription, EmergencyContact, Pet, ChecklistCompletion
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
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
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
    return {"ok": True}


@router.delete("/me")
def delete_account(data: AccountDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not pwd_context.verify(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    db.delete(current_user)
    db.commit()
    return {"ok": True}


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
    return JSONResponse(content=json.loads(content), headers={
        "Content-Disposition": "attachment; filename=digital-memorial-export.json"
    })
