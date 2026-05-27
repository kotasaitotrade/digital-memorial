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
    title: str = "自分の相続計画"

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
