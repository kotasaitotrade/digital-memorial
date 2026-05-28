from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── 相続計画 ────────────────────────────────────────────────

class FamilyMemberCreate(BaseModel):
    name: str = Field(min_length=1)
    relationship: str
    is_alive: bool = True
    is_adopted: bool = False
    is_half_blood: bool = False
    has_renounced: bool = False
    is_disqualified: bool = False
    parent_member_id: Optional[int] = None

class FamilyMemberResponse(FamilyMemberCreate):
    id: int
    estate_plan_id: int
    class Config:
        from_attributes = True

class AssetCreate(BaseModel):
    asset_type: str
    name: str
    estimated_value: int = 0
    is_deemed_estate: bool = False
    notes: Optional[str] = None

class AssetResponse(AssetCreate):
    id: int
    estate_plan_id: int
    class Config:
        from_attributes = True

class EstatePlanCreate(BaseModel):
    title: str = Field(default="自分の相続計画", min_length=1, max_length=100)

class EstatePlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    family_members: List[FamilyMemberResponse] = []
    assets: List[AssetResponse] = []
    class Config:
        from_attributes = True

class FamilyMembersBulkSave(BaseModel):
    members: List[FamilyMemberCreate]

class AssetsBulkSave(BaseModel):
    assets: List[AssetCreate]


# ─── エンディングノート ──────────────────────────────────────

class BequestItemCreate(BaseModel):
    item_name: str
    recipient: str
    notes: Optional[str] = None

class BequestItemResponse(BequestItemCreate):
    id: int
    class Config:
        from_attributes = True

class DigitalAssetCreate(BaseModel):
    service_name: str
    account: Optional[str] = None
    after_death_instruction: Optional[str] = None
    notes: Optional[str] = None

class DigitalAssetResponse(DigitalAssetCreate):
    id: int
    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    service_name: str
    monthly_fee: Optional[int] = None
    cancellation_method: Optional[str] = None
    notes: Optional[str] = None

class SubscriptionResponse(SubscriptionCreate):
    id: int
    class Config:
        from_attributes = True

class EmergencyContactCreate(BaseModel):
    name: str
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    priority: int = 0

class EmergencyContactResponse(EmergencyContactCreate):
    id: int
    class Config:
        from_attributes = True

class PetCreate(BaseModel):
    name: str
    species: Optional[str] = None
    medical_info: Optional[str] = None
    personality: Optional[str] = None
    caretaker: Optional[str] = None
    notes: Optional[str] = None

class PetResponse(PetCreate):
    id: int
    class Config:
        from_attributes = True

class EndingNoteUpdate(BaseModel):
    life_prolonging: Optional[str] = None
    cpr: Optional[str] = None
    tube_feeding: Optional[str] = None
    organ_donation: Optional[str] = None
    organ_donation_detail: Optional[str] = None
    care_location: Optional[str] = None
    primary_doctor: Optional[str] = None
    medications: Optional[str] = None
    medical_notes: Optional[str] = None
    funeral_style: Optional[str] = None
    religion: Optional[str] = None
    funeral_music: Optional[str] = None
    funeral_notes: Optional[str] = None
    family_message: Optional[str] = None

class EndingNoteResponse(BaseModel):
    id: int
    user_id: int
    life_prolonging: Optional[str]
    cpr: Optional[str]
    tube_feeding: Optional[str]
    organ_donation: Optional[str]
    organ_donation_detail: Optional[str]
    care_location: Optional[str]
    primary_doctor: Optional[str]
    medications: Optional[str]
    medical_notes: Optional[str]
    funeral_style: Optional[str]
    religion: Optional[str]
    funeral_music: Optional[str]
    funeral_notes: Optional[str]
    funeral_photo_path: Optional[str]
    family_message: Optional[str]
    updated_at: Optional[datetime]
    bequest_items: List[BequestItemResponse] = []
    digital_assets: List[DigitalAssetResponse] = []
    subscriptions: List[SubscriptionResponse] = []
    emergency_contacts: List[EmergencyContactResponse] = []
    pets: List[PetResponse] = []
    class Config:
        from_attributes = True


# ─── チェックリスト ──────────────────────────────────────────

class ChecklistToggle(BaseModel):
    task_key: str
    is_completed: bool

class ChecklistStatusResponse(BaseModel):
    task_key: str
    is_completed: bool
    completed_at: Optional[datetime]
    class Config:
        from_attributes = True


# ─── 遺言書シミュレーター ─────────────────────────────────────

class WillDraftSave(BaseModel):
    allocations: dict = {}
    memo: Optional[str] = None

class WillDraftResponse(BaseModel):
    estate_plan_id: int
    allocations: dict
    memo: Optional[str]
    class Config:
        from_attributes = True


# ─── デジタル遺品鍵 ──────────────────────────────────────────

class TrustedPersonCreate(BaseModel):
    name: str
    email: str
    access_scope: List[str] = ["all"]

class TrustedPersonResponse(BaseModel):
    id: int
    name: str
    email: str
    access_scope: List[str]
    access_token: str
    has_requested: bool
    requested_at: Optional[datetime]
    email_verified: bool
    created_at: datetime
    class Config:
        from_attributes = True

class DigitalKeyUpdate(BaseModel):
    unlock_condition: Optional[str] = None
    notes: Optional[str] = None

class DigitalKeyResponse(BaseModel):
    id: int
    user_id: int
    unlock_condition: str
    is_unlocked: bool
    unlocked_at: Optional[datetime]
    notes: Optional[str]
    trusted_persons: List[TrustedPersonResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True


# ─── リマインダー設定 ─────────────────────────────────────────

class ReminderSettingUpdate(BaseModel):
    enabled: Optional[bool] = None
    review_month: Optional[int] = None
    notify_incomplete: Optional[bool] = None
    notify_trusted: Optional[bool] = None
    email: Optional[str] = None

class ReminderSettingResponse(BaseModel):
    id: int
    user_id: int
    enabled: bool
    review_month: int
    notify_incomplete: bool
    notify_trusted: bool
    email: Optional[str]
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True


# ─── 追悼メッセージ ──────────────────────────────────────────

class ScheduledMessageCreate(BaseModel):
    recipient_name: str
    recipient_email: str
    subject: str
    body: str

class ScheduledMessageResponse(ScheduledMessageCreate):
    id: int
    is_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True


# ─── ビデオメッセージ ─────────────────────────────────────────

class VideoMessageResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    duration_seconds: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True
