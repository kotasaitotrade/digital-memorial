from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON
from sqlalchemy.orm import relationship as db_relationship
from sqlalchemy.sql import func
from ..database import Base


# ─── 相続計画 ────────────────────────────────────────────────

class EstatePlan(Base):
    __tablename__ = "estate_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="自分の相続計画")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    family_members = db_relationship("FamilyMember", back_populates="estate_plan", cascade="all, delete-orphan")
    assets = db_relationship("Asset", back_populates="estate_plan", cascade="all, delete-orphan")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), nullable=False)
    name = Column(String, nullable=False)
    # spouse / child / grandchild / parent / grandparent / sibling / nephew_niece
    relationship = Column(String, nullable=False)
    is_alive = Column(Boolean, default=True)
    is_adopted = Column(Boolean, default=False)       # 養子
    is_half_blood = Column(Boolean, default=False)    # 半血兄弟姉妹
    has_renounced = Column(Boolean, default=False)    # 相続放棄
    is_disqualified = Column(Boolean, default=False)  # 相続欠格・廃除
    parent_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=True)  # 代襲元
    personal_message = Column(Text, nullable=True)    # 個人へのメッセージ（佐藤健一 要望）

    estate_plan = db_relationship("EstatePlan", back_populates="family_members")
    proxy_children = db_relationship("FamilyMember", foreign_keys=[parent_member_id])


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), nullable=False)
    # real_estate / bank_account / securities / life_insurance / retirement / pension / farmland / other / debt
    asset_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    estimated_value = Column(Integer, default=0)   # 円（負債はマイナス）
    is_deemed_estate = Column(Boolean, default=False)  # みなし相続財産
    notes = Column(Text, nullable=True)
    # 不動産・農地専用フィールド（鈴木太郎 要望）
    property_registration_no = Column(String, nullable=True)   # 登記番号
    fixed_asset_tax_value = Column(Integer, nullable=True)     # 固定資産税評価額
    is_farmland = Column(Boolean, default=False)               # 農地フラグ
    location_address = Column(String, nullable=True)           # 所在地
    # 保険・年金専用フィールド（佐藤健一 要望）
    policy_number = Column(String, nullable=True)              # 証券番号
    insurance_company = Column(String, nullable=True)          # 保険会社/年金機構
    beneficiary = Column(String, nullable=True)                # 受取人

    estate_plan = db_relationship("EstatePlan", back_populates="assets")


# ─── エンディングノート ──────────────────────────────────────

class EndingNote(Base):
    __tablename__ = "ending_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 医療・介護の希望
    life_prolonging = Column(String, nullable=True)   # 希望する / 希望しない / 家族に委ねる
    cpr = Column(String, nullable=True)
    tube_feeding = Column(String, nullable=True)
    organ_donation = Column(String, nullable=True)
    organ_donation_detail = Column(Text, nullable=True)
    care_location = Column(String, nullable=True)     # 自宅 / 施設 / 病院
    primary_doctor = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    medical_notes = Column(Text, nullable=True)

    # 葬儀の希望（松本恵子・鈴木太郎 要望で拡充）
    funeral_style = Column(String, nullable=True)     # 家族葬 / 一般葬 / 直葬 / 自由
    religion = Column(String, nullable=True)
    funeral_music = Column(Text, nullable=True)
    funeral_notes = Column(Text, nullable=True)
    funeral_photo_path = Column(String, nullable=True)  # 遺影写真
    funeral_flower_type = Column(String, nullable=True)  # 花の種類・色の希望
    kaimyo_preference = Column(Text, nullable=True)      # 戒名への希望
    funeral_guest_limit = Column(Integer, nullable=True) # 会葬者人数の目安
    burial_preference = Column(String, nullable=True)    # 埋葬方法（土葬/火葬/樹木葬/散骨）

    # お気に入り（松本恵子 要望）
    favorite_music = Column(Text, nullable=True)         # 好きな音楽
    favorite_movies = Column(Text, nullable=True)        # 好きな映画・本
    favorite_foods = Column(Text, nullable=True)         # 好きな食べ物・場所

    # 家族へのメッセージ
    family_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bequest_items = db_relationship("BequestItem", back_populates="ending_note", cascade="all, delete-orphan")
    digital_assets = db_relationship("DigitalAsset", back_populates="ending_note", cascade="all, delete-orphan")
    subscriptions = db_relationship("Subscription", back_populates="ending_note", cascade="all, delete-orphan")
    emergency_contacts = db_relationship("EmergencyContact", back_populates="ending_note", cascade="all, delete-orphan")
    pets = db_relationship("Pet", back_populates="ending_note", cascade="all, delete-orphan")


class BequestItem(Base):
    __tablename__ = "bequest_items"

    id = Column(Integer, primary_key=True, index=True)
    ending_note_id = Column(Integer, ForeignKey("ending_notes.id"), nullable=False)
    item_name = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    ending_note = db_relationship("EndingNote", back_populates="bequest_items")


class DigitalAsset(Base):
    __tablename__ = "digital_assets"

    id = Column(Integer, primary_key=True, index=True)
    ending_note_id = Column(Integer, ForeignKey("ending_notes.id"), nullable=False)
    service_name = Column(String, nullable=False)    # SNS名・サービス名
    account = Column(String, nullable=True)          # アカウント名
    after_death_instruction = Column(Text, nullable=True)  # 死後の処理方法
    notes = Column(Text, nullable=True)

    ending_note = db_relationship("EndingNote", back_populates="digital_assets")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    ending_note_id = Column(Integer, ForeignKey("ending_notes.id"), nullable=False)
    service_name = Column(String, nullable=False)
    monthly_fee = Column(Integer, nullable=True)     # 月額（円）
    cancellation_method = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    ending_note = db_relationship("EndingNote", back_populates="subscriptions")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    ending_note_id = Column(Integer, ForeignKey("ending_notes.id"), nullable=False)
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    priority = Column(Integer, default=0)

    ending_note = db_relationship("EndingNote", back_populates="emergency_contacts")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    ending_note_id = Column(Integer, ForeignKey("ending_notes.id"), nullable=False)
    name = Column(String, nullable=False)
    species = Column(String, nullable=True)           # 犬 / 猫 / etc.
    breed = Column(String, nullable=True)             # 品種（山田花子 要望）
    birth_year = Column(Integer, nullable=True)       # 生まれ年
    microchip_no = Column(String, nullable=True)      # マイクロチップ番号
    vaccine_info = Column(Text, nullable=True)        # ワクチン接種情報
    vet_name = Column(String, nullable=True)          # かかりつけ獣医
    vet_phone = Column(String, nullable=True)         # 獣医の電話番号
    medical_info = Column(Text, nullable=True)
    personality = Column(Text, nullable=True)
    caretaker = Column(String, nullable=True)         # 引き継ぎ先
    caretaker_phone = Column(String, nullable=True)   # 引き継ぎ先の連絡先
    notes = Column(Text, nullable=True)

    ending_note = db_relationship("EndingNote", back_populates="pets")


# ─── チェックリスト ──────────────────────────────────────────

class ChecklistCompletion(Base):
    """ユーザーごとの完了状態だけ保存。項目定義はコードで管理。"""
    __tablename__ = "checklist_completions"
    __table_args__ = (UniqueConstraint("user_id", "task_key", name="uq_checklist_user_task"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_key = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


# ─── 遺言書シミュレーター ─────────────────────────────────────

class WillDraft(Base):
    """相続計画ごとの遺言書シミュレーター（希望配分を保存）"""
    __tablename__ = "will_drafts"

    id = Column(Integer, primary_key=True, index=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), unique=True, nullable=False)
    # {family_member_id: desired_amount, ...}
    allocations = Column(JSON, default=dict)
    # 遺言者が書いたカスタム付言事項
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    estate_plan = db_relationship("EstatePlan")


# ─── デジタル遺品鍵 ──────────────────────────────────────────

class DigitalKey(Base):
    __tablename__ = "digital_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    # one_request / two_requests
    unlock_condition = Column(String, default="one_request")
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # デッドマンスイッチ（山田花子 要望）
    deadman_enabled = Column(Boolean, default=False)
    deadman_interval_days = Column(Integer, default=90)   # 何日間未ログインで通知するか
    last_checkin_at = Column(DateTime(timezone=True), nullable=True)  # 最後の生存確認

    trusted_persons = db_relationship("TrustedPerson", back_populates="digital_key", cascade="all, delete-orphan")


import secrets

class TrustedPerson(Base):
    __tablename__ = "trusted_persons"

    id = Column(Integer, primary_key=True, index=True)
    digital_key_id = Column(Integer, ForeignKey("digital_keys.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    # all / estate / ending_note
    access_scope = Column(JSON, default=list)
    access_token = Column(String, default=lambda: secrets.token_urlsafe(32))
    has_requested = Column(Boolean, default=False)
    requested_at = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    digital_key = db_relationship("DigitalKey", back_populates="trusted_persons")


# ─── リマインダー設定 ─────────────────────────────────────────

class ReminderSetting(Base):
    __tablename__ = "reminder_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    review_month = Column(Integer, default=1)       # 年次見直し月（1〜12）
    notify_incomplete = Column(Boolean, default=True)  # 未完了タスク通知
    notify_trusted = Column(Boolean, default=True)    # 信頼者確認メール
    email = Column(String, nullable=True)             # 通知先（未設定ならアカウントのメール）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ─── 追悼メッセージ（予約送信） ──────────────────────────────────

class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_name = Column(String, nullable=False)   # 送り先の名前
    recipient_email = Column(String, nullable=False)  # 送り先メール
    subject = Column(String, nullable=False)          # 件名
    body = Column(Text, nullable=False)               # 本文
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ─── ビデオメッセージ ─────────────────────────────────────────

class VideoMessage(Base):
    __tablename__ = "video_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)       # サーバー上のパス
    file_size = Column(Integer, nullable=True)       # bytes
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
