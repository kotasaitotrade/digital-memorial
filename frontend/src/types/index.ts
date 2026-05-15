export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface MemorialMedia {
  id: number;
  file_path: string;
  media_type: "image" | "video";
  caption?: string;
  order: number;
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
