export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
  totp_enabled?: boolean;
  font_size?: string;
  simple_mode?: boolean;
}

export interface MemorialMedia {
  id: number;
  file_path: string;
  media_type: "image" | "video";
  caption?: string;
  order: number;
  album_name?: string;
  taken_at?: string;
  location?: string;
  episode?: string;
  media_is_public?: boolean;
}

export interface Memorial {
  id: number;
  slug: string;
  name: string;
  birth_date?: string;
  death_date?: string;
  biography?: string;
  message?: string;
  is_public: boolean;
  qr_code_path?: string;
  created_at: string;
  media: MemorialMedia[];
}

export interface MemorialPublic {
  slug: string;
  name: string;
  birth_date?: string;
  death_date?: string;
  biography?: string;
  message?: string;
  media: MemorialMedia[];
}

// ─── 相続計画 ────────────────────────────────────────────────

export interface FamilyMember {
  id: number;
  estate_plan_id: number;
  name: string;
  relationship: "spouse" | "child" | "grandchild" | "parent" | "grandparent" | "sibling" | "nephew_niece";
  is_alive: boolean;
  is_adopted: boolean;
  is_half_blood: boolean;
  has_renounced: boolean;
  is_disqualified: boolean;
  parent_member_id?: number;
  personal_message?: string;
}

export interface Asset {
  id: number;
  estate_plan_id: number;
  asset_type: "real_estate" | "bank_account" | "securities" | "life_insurance" | "retirement" | "pension" | "farmland" | "other" | "debt";
  name: string;
  estimated_value: number;
  is_deemed_estate: boolean;
  notes?: string;
  property_registration_no?: string;
  fixed_asset_tax_value?: number;
  is_farmland?: boolean;
  location_address?: string;
  policy_number?: string;
  insurance_company?: string;
  beneficiary?: string;
}

export interface EstatePlan {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at?: string;
  family_members: FamilyMember[];
  assets: Asset[];
}

export interface HeirResult {
  id: number;
  name: string;
  relationship: string;
  share_fraction: string;
  share_percent: number;
  share_amount: number;
  reserved_fraction?: string;
  reserved_percent?: number;
  reserved_amount: number;
  has_reserved_right: boolean;
}

export interface InheritanceCalculation {
  heirs: HeirResult[];
  order_label: string;
  estate_value: number;
  total_reserved_ratio?: string;
  basic_deduction: number;
  message?: string;
}

// ─── エンディングノート ──────────────────────────────────────

export interface BequestItem { id: number; item_name: string; recipient: string; notes?: string; }
export interface DigitalAssetItem { id: number; service_name: string; account?: string; after_death_instruction?: string; notes?: string; }
export interface SubscriptionItem { id: number; service_name: string; monthly_fee?: number; cancellation_method?: string; notes?: string; }
export interface EmergencyContact { id: number; name: string; relationship?: string; phone?: string; email?: string; notes?: string; priority: number; }
export interface PetItem {
  id: number; name: string; species?: string; breed?: string; birth_year?: number;
  microchip_no?: string; vaccine_info?: string; vet_name?: string; vet_phone?: string;
  medical_info?: string; personality?: string; caretaker?: string; caretaker_phone?: string; notes?: string;
}

export interface EndingNote {
  id: number;
  user_id: number;
  life_prolonging?: string;
  cpr?: string;
  tube_feeding?: string;
  organ_donation?: string;
  organ_donation_detail?: string;
  care_location?: string;
  primary_doctor?: string;
  medications?: string;
  medical_notes?: string;
  funeral_style?: string;
  religion?: string;
  funeral_music?: string;
  funeral_notes?: string;
  funeral_photo_path?: string;
  family_message?: string;
  funeral_flower_type?: string;
  kaimyo_preference?: string;
  funeral_guest_limit?: number;
  burial_preference?: string;
  favorite_music?: string;
  favorite_movies?: string;
  favorite_foods?: string;
  updated_at?: string;
  bequest_items: BequestItem[];
  digital_assets: DigitalAssetItem[];
  subscriptions: SubscriptionItem[];
  emergency_contacts: EmergencyContact[];
  pets: PetItem[];
}

// ─── チェックリスト ──────────────────────────────────────────

export interface ChecklistItem {
  task_key: string;
  category: string;
  label: string;
  stars: number;
  priority: "必須" | "推奨" | "任意";
  link: string;
  is_completed: boolean;
  completed_at?: string;
}
