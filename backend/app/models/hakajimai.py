from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base

DEFAULT_CHECKLIST = [
    {"key": "family_consult",    "category": "準備",   "label": "家族・親族への相談",               "is_done": False},
    {"key": "temple_consult",    "category": "準備",   "label": "菩提寺・霊園への相談・連絡",       "is_done": False},
    {"key": "new_place_decided", "category": "準備",   "label": "改葬先の決定（永代供養墓・散骨等）","is_done": False},
    {"key": "permit_apply",      "category": "行政",   "label": "市区町村役場で改葬許可申請",        "is_done": False},
    {"key": "kaimoku",           "category": "供養",   "label": "閉眼供養（魂抜き）の依頼・実施",   "is_done": False},
    {"key": "stone_removal",     "category": "工事",   "label": "石材店への墓石撤去・処分依頼",      "is_done": False},
    {"key": "remains_removal",   "category": "工事",   "label": "遺骨の取り出し",                   "is_done": False},
    {"key": "new_burial",        "category": "改葬先", "label": "改葬先での納骨・手続き完了",        "is_done": False},
    {"key": "land_return",       "category": "改葬先", "label": "墓地の返還手続き完了",              "is_done": False},
    {"key": "kaigen",            "category": "供養",   "label": "開眼供養（新しい供養先で）",        "is_done": False},
]

DEFAULT_COST_ITEMS = [
    {"key": "cost_kaimoku",   "label": "閉眼供養（お布施）",     "amount": 30000,  "min": 30000,  "max": 100000, "note": "目安: 3〜10万円"},
    {"key": "cost_stone",     "label": "石材店（撤去・処分費）", "amount": 150000, "min": 100000, "max": 300000, "note": "目安: 10〜30万円"},
    {"key": "cost_permit",    "label": "改葬許可手数料",         "amount": 1500,   "min": 1500,   "max": 5000,   "note": "目安: 1,500〜数千円"},
    {"key": "cost_transport", "label": "遺骨の運搬費",           "amount": 20000,  "min": 10000,  "max": 50000,  "note": "目安: 1〜5万円"},
    {"key": "cost_new_place", "label": "新しい供養先の費用",     "amount": 200000, "min": 50000,  "max": 800000, "note": "方法により大きく異なる"},
    {"key": "cost_kaigen",    "label": "開眼供養（お布施）",     "amount": 30000,  "min": 30000,  "max": 100000, "note": "目安: 3〜10万円"},
]

DEFAULT_GRAVE_INFO = {
    "cemetery_name": "",
    "address": "",
    "temple_name": "",
    "住職名": "",
    "temple_phone": "",
    "stone_shop_name": "",
    "stone_shop_phone": "",
    "annual_fee": "",
    "built_year": "",
    "notes": "",
}


class HakajimaiPlan(Base):
    __tablename__ = "hakajimai_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    kuyou_method = Column(String, default="")
    kuyou_detail = Column(Text, default="")
    message_to_family = Column(Text, default="")
    checklist_items = Column(JSON, default=lambda: list(DEFAULT_CHECKLIST))
    cost_items = Column(JSON, default=lambda: list(DEFAULT_COST_ITEMS))
    # 新規フィールド
    sect = Column(String, default="")                                          # 宗派
    grave_info = Column(JSON, default=lambda: dict(DEFAULT_GRAVE_INFO))        # 現在のお墓の情報
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
