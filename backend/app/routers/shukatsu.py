from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
import os, shutil, uuid

from datetime import datetime, timezone
from ..database import get_db
from ..models.user import User
from ..models.shukatsu import (
    EstatePlan, FamilyMember, Asset,
    EndingNote, BequestItem, DigitalAsset, Subscription, EmergencyContact, Pet,
    ChecklistCompletion, WillDraft,
    DigitalKey, TrustedPerson, ReminderSetting, ScheduledMessage, VideoMessage,
)
from ..schemas.shukatsu import (
    EstatePlanCreate, EstatePlanResponse,
    FamilyMemberCreate, FamilyMemberResponse, FamilyMembersBulkSave,
    AssetCreate, AssetResponse, AssetsBulkSave,
    EndingNoteUpdate, EndingNoteResponse,
    BequestItemCreate, BequestItemResponse,
    DigitalAssetCreate, DigitalAssetResponse,
    SubscriptionCreate, SubscriptionResponse,
    EmergencyContactCreate, EmergencyContactResponse,
    PetCreate, PetResponse,
    ChecklistToggle, ChecklistStatusResponse,
    WillDraftSave, WillDraftResponse,
    TrustedPersonCreate, TrustedPersonResponse,
    DigitalKeyUpdate, DigitalKeyResponse,
    ReminderSettingUpdate, ReminderSettingResponse,
    ScheduledMessageCreate, ScheduledMessageResponse,
    VideoMessageResponse,
)
from ..services.inheritance import calculate_inheritance
from ..services.email import (
    send_email,
    make_verification_email,
    make_scheduled_message_email,
)
from .auth import get_current_user
from ..config import settings

router = APIRouter(tags=["shukatsu"])


# ─── チェックリスト定義（コードで管理）─────────────────────

# stars(1-5): 3以上 → 必須 / 2 → 推奨 / 1 → 任意  ／ 降順ソート済み
_RAW_CHECKLIST = [
    {"task_key": "estate_heirs_confirmed",   "category": "相続",    "label": "相続人を確認した",                   "stars": 5, "link": "/estate"},
    {"task_key": "estate_assets_listed",     "category": "相続",    "label": "財産・負債を一覧にした",             "stars": 5, "link": "/estate"},
    {"task_key": "will_considered",          "category": "遺言",    "label": "遺言書を作成した（または検討した）", "stars": 5, "link": "/estate"},
    {"task_key": "medical_prolonging_set",   "category": "医療",    "label": "延命治療の希望を記録した",           "stars": 5, "link": "/ending-note"},
    {"task_key": "contacts_listed",          "category": "人間関係","label": "緊急連絡先リストを作成した",         "stars": 5, "link": "/ending-note"},
    {"task_key": "estate_reserved_checked",  "category": "相続",    "label": "遺留分を把握した",                   "stars": 4, "link": "/estate"},
    {"task_key": "medical_doctor_recorded",  "category": "医療",    "label": "かかりつけ医・処方薬を記録した",     "stars": 4, "link": "/ending-note"},
    {"task_key": "funeral_style_set",        "category": "葬儀",    "label": "葬儀の希望（形式・規模）を記録した", "stars": 4, "link": "/ending-note"},
    {"task_key": "digital_key_set",          "category": "デジタル","label": "デジタル遺品鍵を設定した",           "stars": 4, "link": "/digital-key"},
    {"task_key": "estate_gifts_recorded",    "category": "相続",    "label": "生前贈与の記録を残した",             "stars": 3, "link": "/ending-note"},
    {"task_key": "medical_organ_set",        "category": "医療",    "label": "臓器提供の意思を記録した",           "stars": 3, "link": "/ending-note"},
    {"task_key": "funeral_photo_selected",   "category": "葬儀",    "label": "遺影に使いたい写真を選んだ",         "stars": 3, "link": "/ending-note"},
    {"task_key": "digital_subscriptions",    "category": "デジタル","label": "サブスクリプション一覧を作成した",   "stars": 3, "link": "/ending-note"},
    {"task_key": "digital_sns_set",          "category": "デジタル","label": "SNSアカウントの死後処理を決めた",     "stars": 3, "link": "/ending-note"},
    {"task_key": "family_message_written",   "category": "思い出",  "label": "家族へのメッセージを書いた",         "stars": 3, "link": "/ending-note"},
    {"task_key": "bequest_listed",           "category": "人間関係","label": "形見分けリストを作成した",           "stars": 2, "link": "/ending-note"},
    {"task_key": "pet_caretaker_set",        "category": "ペット",  "label": "ペットの引き継ぎ先を決めた",         "stars": 2, "link": "/ending-note"},
]

def _stars_to_priority(stars: int) -> str:
    if stars >= 3:
        return "必須"
    if stars == 2:
        return "推奨"
    return "任意"

CHECKLIST_ITEMS = sorted(
    [{**item, "priority": _stars_to_priority(item["stars"])} for item in _RAW_CHECKLIST],
    key=lambda x: x["stars"],
    reverse=True,
)

VALID_TASK_KEYS = {item["task_key"] for item in CHECKLIST_ITEMS}


# ═══════════════════════════════════════════════════════════
# 相続計画
# ═══════════════════════════════════════════════════════════

@router.post("/estate-plans", response_model=EstatePlanResponse)
def create_estate_plan(
    data: EstatePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = EstatePlan(user_id=current_user.id, title=data.title)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/estate-plans", response_model=List[EstatePlanResponse])
def list_estate_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(EstatePlan).filter(EstatePlan.user_id == current_user.id).all()


@router.get("/estate-plans/{plan_id}", response_model=EstatePlanResponse)
def get_estate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    return plan


@router.patch("/estate-plans/{plan_id}", response_model=EstatePlanResponse)
def rename_estate_plan(
    plan_id: int,
    data: EstatePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    if data.title.strip():
        plan.title = data.title.strip()
        db.commit()
        db.refresh(plan)
    return plan


@router.delete("/estate-plans/{plan_id}")
def delete_estate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    db.delete(plan)
    db.commit()
    return {"ok": True}


# ─── 家族構成 ────────────────────────────────────────────────

@router.post("/estate-plans/{plan_id}/family", response_model=List[FamilyMemberResponse])
def save_family_members(
    plan_id: int,
    data: FamilyMembersBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """家族構成を一括保存（既存データを差し替え）"""
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    db.query(FamilyMember).filter(FamilyMember.estate_plan_id == plan_id).delete()
    members = []
    for m in data.members:
        member = FamilyMember(estate_plan_id=plan_id, **m.model_dump())
        db.add(member)
        members.append(member)
    db.commit()
    for m in members:
        db.refresh(m)

    # フロントエンドは parent_member_id に配列インデックスを送ってくる。
    # 保存後にインデックス → 実 DB ID へ変換する。
    id_map = {i: m.id for i, m in enumerate(members)}
    remapped = False
    for member in members:
        if member.parent_member_id is not None and 0 <= member.parent_member_id < len(members):
            member.parent_member_id = id_map[member.parent_member_id]
            remapped = True
    if remapped:
        db.commit()
        for m in members:
            db.refresh(m)

    return members


@router.get("/estate-plans/{plan_id}/family", response_model=List[FamilyMemberResponse])
def get_family_members(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_plan_or_404(db, plan_id, current_user.id)
    return db.query(FamilyMember).filter(FamilyMember.estate_plan_id == plan_id).all()


# ─── 財産 ────────────────────────────────────────────────────

@router.post("/estate-plans/{plan_id}/assets", response_model=List[AssetResponse])
def save_assets(
    plan_id: int,
    data: AssetsBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """財産を一括保存（既存データを差し替え）"""
    _get_plan_or_404(db, plan_id, current_user.id)
    db.query(Asset).filter(Asset.estate_plan_id == plan_id).delete()
    assets = []
    for a in data.assets:
        asset = Asset(estate_plan_id=plan_id, **a.model_dump())
        db.add(asset)
        assets.append(asset)
    db.commit()
    for a in assets:
        db.refresh(a)
    return assets


@router.get("/estate-plans/{plan_id}/assets", response_model=List[AssetResponse])
def get_assets(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_plan_or_404(db, plan_id, current_user.id)
    return db.query(Asset).filter(Asset.estate_plan_id == plan_id).all()


# ─── 相続計算 ────────────────────────────────────────────────

@router.get("/estate-plans/{plan_id}/calculate")
def calculate(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    family = db.query(FamilyMember).filter(FamilyMember.estate_plan_id == plan_id).all()
    assets = db.query(Asset).filter(Asset.estate_plan_id == plan_id).all()

    # 正味遺産額（みなし相続財産を含む）
    estate_value = sum(a.estimated_value for a in assets)

    return calculate_inheritance(family, estate_value)


# ═══════════════════════════════════════════════════════════
# エンディングノート
# ═══════════════════════════════════════════════════════════

def _get_or_create_note(db: Session, user_id: int) -> EndingNote:
    note = db.query(EndingNote).filter(EndingNote.user_id == user_id).first()
    if not note:
        note = EndingNote(user_id=user_id)
        db.add(note)
        db.commit()
        db.refresh(note)
    return note


@router.get("/ending-note", response_model=EndingNoteResponse)
def get_ending_note(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_note(db, current_user.id)


@router.put("/ending-note", response_model=EndingNoteResponse)
def update_ending_note(
    data: EndingNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_or_create_note(db, current_user.id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


# 遺影写真アップロード
@router.post("/ending-note/funeral-photo")
def upload_funeral_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_or_create_note(db, current_user.id)
    from ..storage import save_upload
    url_path = save_upload(file.file, file.filename, f"funeral_photos/{current_user.id}", file.content_type or "image/jpeg")
    note.funeral_photo_path = url_path
    db.commit()
    db.refresh(note)
    return {"path": url_path}


# ─── 形見分けリスト ──────────────────────────────────────────

@router.post("/ending-note/bequest-items", response_model=BequestItemResponse)
def add_bequest_item(data: BequestItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = BequestItem(ending_note_id=note.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/ending-note/bequest-items/{item_id}")
def delete_bequest_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = db.query(BequestItem).filter(BequestItem.id == item_id, BequestItem.ending_note_id == note.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ─── デジタル資産 ────────────────────────────────────────────

@router.post("/ending-note/digital-assets", response_model=DigitalAssetResponse)
def add_digital_asset(data: DigitalAssetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = DigitalAsset(ending_note_id=note.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/ending-note/digital-assets/{item_id}")
def delete_digital_asset(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = db.query(DigitalAsset).filter(DigitalAsset.id == item_id, DigitalAsset.ending_note_id == note.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ─── サブスクリプション ──────────────────────────────────────

@router.post("/ending-note/subscriptions", response_model=SubscriptionResponse)
def add_subscription(data: SubscriptionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = Subscription(ending_note_id=note.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/ending-note/subscriptions/{item_id}")
def delete_subscription(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = db.query(Subscription).filter(Subscription.id == item_id, Subscription.ending_note_id == note.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ─── 緊急連絡先 ──────────────────────────────────────────────

@router.post("/ending-note/emergency-contacts", response_model=EmergencyContactResponse)
def add_emergency_contact(data: EmergencyContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = EmergencyContact(ending_note_id=note.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/ending-note/emergency-contacts/{item_id}")
def delete_emergency_contact(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = db.query(EmergencyContact).filter(EmergencyContact.id == item_id, EmergencyContact.ending_note_id == note.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ─── ペット ──────────────────────────────────────────────────

@router.post("/ending-note/pets", response_model=PetResponse)
def add_pet(data: PetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = Pet(ending_note_id=note.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/ending-note/pets/{item_id}")
def delete_pet(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_or_create_note(db, current_user.id)
    item = db.query(Pet).filter(Pet.id == item_id, Pet.ending_note_id == note.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════
# チェックリスト
# ═══════════════════════════════════════════════════════════


@router.get("/checklist")
def get_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    completions = db.query(ChecklistCompletion).filter(
        ChecklistCompletion.user_id == current_user.id
    ).all()
    completion_map = {c.task_key: c for c in completions}

    items = []
    completed_count = 0
    for item in CHECKLIST_ITEMS:
        c = completion_map.get(item["task_key"])
        is_done = c.is_completed if c else False
        if is_done:
            completed_count += 1
        items.append({
            **item,
            "is_completed": is_done,
            "completed_at": c.completed_at.isoformat() if (c and c.completed_at) else None,
        })

    total = len(items)
    rate = round(completed_count / total * 100, 1) if total else 0.0
    return {"items": items, "completion_rate": rate}


@router.post("/checklist/toggle")
def toggle_checklist(
    data: ChecklistToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.task_key not in VALID_TASK_KEYS:
        raise HTTPException(status_code=404, detail="Task key not found")

    completion = db.query(ChecklistCompletion).filter(
        ChecklistCompletion.user_id == current_user.id,
        ChecklistCompletion.task_key == data.task_key,
    ).first()
    if not completion:
        completion = ChecklistCompletion(user_id=current_user.id, task_key=data.task_key)
        db.add(completion)
    completion.is_completed = data.is_completed
    completion.completed_at = func.now() if data.is_completed else None
    db.commit()
    return {"ok": True, "is_completed": data.is_completed}


# ─── ヘルパー ────────────────────────────────────────────────

def _get_plan_or_404(db: Session, plan_id: int, user_id: int) -> EstatePlan:
    plan = db.query(EstatePlan).filter(
        EstatePlan.id == plan_id,
        EstatePlan.user_id == user_id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Estate plan not found")
    return plan


# ═══════════════════════════════════════════════════════════
# 遺言書シミュレーター
# ═══════════════════════════════════════════════════════════

@router.get("/estate-plans/{plan_id}/will", response_model=WillDraftResponse)
def get_will(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_plan_or_404(db, plan_id, current_user.id)
    draft = db.query(WillDraft).filter(WillDraft.estate_plan_id == plan_id).first()
    if not draft:
        return WillDraftResponse(estate_plan_id=plan_id, allocations={}, memo=None)
    return draft


@router.put("/estate-plans/{plan_id}/will", response_model=WillDraftResponse)
def save_will(
    plan_id: int,
    data: WillDraftSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_plan_or_404(db, plan_id, current_user.id)
    draft = db.query(WillDraft).filter(WillDraft.estate_plan_id == plan_id).first()
    if draft:
        draft.allocations = data.allocations
        draft.memo = data.memo
    else:
        draft = WillDraft(estate_plan_id=plan_id, allocations=data.allocations or {}, memo=data.memo)
        db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


# ═══════════════════════════════════════════════════════════════
#  デジタル遺品鍵
# ═══════════════════════════════════════════════════════════════

def _get_or_create_digital_key(db: Session, user_id: int) -> DigitalKey:
    key = db.query(DigitalKey).filter(DigitalKey.user_id == user_id).first()
    if not key:
        key = DigitalKey(user_id=user_id)
        db.add(key)
        db.commit()
        db.refresh(key)
    return key


@router.get("/digital-key", response_model=DigitalKeyResponse)
def get_digital_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_create_digital_key(db, current_user.id)


@router.patch("/digital-key", response_model=DigitalKeyResponse)
def update_digital_key(
    data: DigitalKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = _get_or_create_digital_key(db, current_user.id)
    if data.unlock_condition is not None:
        key.unlock_condition = data.unlock_condition
    if data.notes is not None:
        key.notes = data.notes
    if data.is_unlocked is not None:
        key.is_unlocked = data.is_unlocked
        if not data.is_unlocked:
            key.unlocked_at = None
    if data.deadman_enabled is not None:
        key.deadman_enabled = data.deadman_enabled
    if data.deadman_interval_days is not None:
        key.deadman_interval_days = data.deadman_interval_days
    db.commit()
    db.refresh(key)
    return key


@router.post("/digital-key/checkin")
def deadman_checkin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """デッドマンスイッチ：生存確認チェックイン（山田花子 要望）"""
    key = _get_or_create_digital_key(db, current_user.id)
    key.last_checkin_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "last_checkin_at": key.last_checkin_at.isoformat()}


@router.post("/digital-key/trusted-persons", response_model=TrustedPersonResponse)
def add_trusted_person(
    data: TrustedPersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = _get_or_create_digital_key(db, current_user.id)
    if len(key.trusted_persons) >= 3:
        raise HTTPException(status_code=400, detail="信頼者は最大3名まで登録できます")
    person = TrustedPerson(digital_key_id=key.id, name=data.name, email=data.email, access_scope=data.access_scope)
    db.add(person)
    db.commit()
    db.refresh(person)
    # メールアドレス確認メールを送信
    verify_url = (
        f"{settings.base_url}/api/digital-key/trusted-persons/{person.id}/verify-email"
        f"?token={person.access_token}"
    )
    subj, html, text = make_verification_email(person.name, verify_url)
    send_email(person.email, subj, html, text)
    return person


@router.get("/digital-key/trusted-persons/{person_id}/verify-email")
def verify_trusted_person_email(person_id: int, token: str, db: Session = Depends(get_db)):
    """信頼者がメールのリンクをクリックしてアドレスを確認する（認証不要）"""
    from fastapi.responses import HTMLResponse
    person = db.query(TrustedPerson).filter(TrustedPerson.id == person_id).first()
    if not person or person.access_token != token:
        raise HTTPException(status_code=403, detail="無効なリンクです")
    if not person.email_verified:
        person.email_verified = True
        db.commit()
    html = """<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f5}
.card{background:#fff;border-radius:12px;padding:40px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,.1)}
h2{color:#2d6a4f}p{color:#555}</style></head>
<body><div class="card"><h2>✅ メールアドレスが確認されました</h2>
<p>Digital Memorial の信頼者として登録が完了しました。<br>このページは閉じてください。</p></div></body></html>"""
    return HTMLResponse(content=html)


@router.delete("/digital-key/trusted-persons/{person_id}", status_code=204)
def delete_trusted_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = _get_or_create_digital_key(db, current_user.id)
    person = db.query(TrustedPerson).filter(
        TrustedPerson.id == person_id,
        TrustedPerson.digital_key_id == key.id,
    ).first()
    if not person:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(person)
    db.commit()


@router.post("/digital-key/trusted-persons/{person_id}/request")
def request_unlock(
    person_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    """信頼者が解除キーを使って開錠申請する（認証不要の公開エンドポイント）"""
    person = db.query(TrustedPerson).filter(TrustedPerson.id == person_id).first()
    if not person or person.access_token != token:
        raise HTTPException(status_code=403, detail="無効な解除キーです")
    if not person.has_requested:
        person.has_requested = True
        person.requested_at = datetime.now(timezone.utc)
        db.commit()
        # 条件判定
        key = db.query(DigitalKey).filter(DigitalKey.id == person.digital_key_id).first()
        requesters = sum(1 for p in key.trusted_persons if p.has_requested)
        required = 2 if key.unlock_condition == "two_requests" else 1
        if requesters >= required and not key.is_unlocked:
            key.is_unlocked = True
            key.unlocked_at = datetime.now(timezone.utc)
            db.commit()
            # 解除成立：予約メッセージを全件送信
            _send_scheduled_messages_on_unlock(db, key.user_id)
    db.refresh(person)
    return {"message": "申請を受け付けました", "is_unlocked": person.digital_key.is_unlocked}


def _send_scheduled_messages_on_unlock(db: Session, user_id: int) -> None:
    """デジタル鍵解除時に未送信の予約メッセージを一括送信"""
    messages = db.query(ScheduledMessage).filter(
        ScheduledMessage.user_id == user_id,
        ScheduledMessage.is_sent == False,
    ).all()
    for msg in messages:
        subj, html, text = make_scheduled_message_email(msg.recipient_name, msg.subject, msg.body)
        ok = send_email(msg.recipient_email, subj, html, text)
        if ok:
            msg.is_sent = True
            msg.sent_at = datetime.now(timezone.utc)
    db.commit()


# ═══════════════════════════════════════════════════════════════
#  リマインダー設定
# ═══════════════════════════════════════════════════════════════

@router.get("/reminder-settings", response_model=ReminderSettingResponse)
def get_reminder_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    setting = db.query(ReminderSetting).filter(ReminderSetting.user_id == current_user.id).first()
    if not setting:
        setting = ReminderSetting(user_id=current_user.id, email=current_user.email)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.put("/reminder-settings", response_model=ReminderSettingResponse)
def update_reminder_settings(
    data: ReminderSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    setting = db.query(ReminderSetting).filter(ReminderSetting.user_id == current_user.id).first()
    if not setting:
        setting = ReminderSetting(user_id=current_user.id, email=current_user.email)
        db.add(setting)
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(setting, field, val)
    db.commit()
    db.refresh(setting)
    return setting


@router.post("/reminder-settings/test-send")
def send_test_reminder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """リマインダーのテスト送信（設定確認用）"""
    from ..services.email import make_reminder_email
    setting = db.query(ReminderSetting).filter(ReminderSetting.user_id == current_user.id).first()
    to_email = (setting.email if setting else None) or current_user.email
    user_name = current_user.name or current_user.email
    from ..models.shukatsu import ShukatsuCheckItem
    incomplete = db.query(ShukatsuCheckItem).filter(
        ShukatsuCheckItem.user_id == current_user.id,
        ShukatsuCheckItem.is_done == False,
    ).count()
    review_month = setting.review_month if setting else 1
    subj, html, text = make_reminder_email(user_name, review_month, incomplete)
    ok = send_email(to_email, subj, html, text)
    return {"ok": ok, "sent_to": to_email}


# ═══════════════════════════════════════════════════════════════
#  追悼メッセージ（予約送信）
# ═══════════════════════════════════════════════════════════════

@router.get("/scheduled-messages", response_model=List[ScheduledMessageResponse])
def list_scheduled_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ScheduledMessage).filter(ScheduledMessage.user_id == current_user.id).all()


@router.post("/scheduled-messages", response_model=ScheduledMessageResponse)
def create_scheduled_message(
    data: ScheduledMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = ScheduledMessage(user_id=current_user.id, **data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.put("/scheduled-messages/{msg_id}", response_model=ScheduledMessageResponse)
def update_scheduled_message(
    msg_id: int,
    data: ScheduledMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ScheduledMessage).filter(
        ScheduledMessage.id == msg_id, ScheduledMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Not found")
    for field, val in data.model_dump().items():
        setattr(msg, field, val)
    db.commit()
    db.refresh(msg)
    return msg


@router.delete("/scheduled-messages/{msg_id}", status_code=204)
def delete_scheduled_message(
    msg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ScheduledMessage).filter(
        ScheduledMessage.id == msg_id, ScheduledMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(msg)
    db.commit()


# ═══════════════════════════════════════════════════════════════
#  ビデオメッセージ
# ═══════════════════════════════════════════════════════════════

VIDEO_DIR = os.path.join(settings.upload_dir, "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)


@router.get("/video-messages", response_model=List[VideoMessageResponse])
def list_video_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(VideoMessage).filter(VideoMessage.user_id == current_user.id).all()


@router.post("/video-messages", response_model=VideoMessageResponse)
def upload_video_message(
    title: str,
    description: str = "",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="動画ファイルのみアップロードできます")
    ext = os.path.splitext(file.filename or "")[1] or ".mp4"
    filename = f"{uuid.uuid4()}{ext}"
    # 一旦ローカルに保存してサイズ・長さを取得してからR2へ
    dest = os.path.join(VIDEO_DIR, filename)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(dest)
    duration_seconds = _extract_video_duration(dest)
    from ..storage import save_upload_path
    file_url = save_upload_path(dest, f"videos/{filename}", file.content_type or "video/mp4")
    video = VideoMessage(
        user_id=current_user.id, title=title, description=description or None,
        file_path=file_url, file_size=size,
        duration_seconds=duration_seconds,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def _extract_video_duration(filepath: str) -> int | None:
    """mutagen で動画の再生時間を秒単位で取得する"""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(filepath)
        if audio and audio.info and hasattr(audio.info, "length"):
            return int(audio.info.length)
    except Exception:
        pass
    return None


@router.delete("/video-messages/{video_id}", status_code=204)
def delete_video_message(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.query(VideoMessage).filter(
        VideoMessage.id == video_id, VideoMessage.user_id == current_user.id
    ).first()
    if not video:
        raise HTTPException(status_code=404, detail="Not found")
    filename = os.path.basename(video.file_path)
    path = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    db.delete(video)
    db.commit()
