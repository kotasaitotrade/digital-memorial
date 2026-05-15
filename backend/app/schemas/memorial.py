from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MemorialMediaResponse(BaseModel):
    id: int
    file_path: str
    media_type: str
    caption: Optional[str]
    order: int

    class Config:
        from_attributes = True


class MemorialCreate(BaseModel):
    name: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    biography: Optional[str] = None
    message: Optional[str] = None
    is_public: bool = True
    password: Optional[str] = None


class MemorialUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    biography: Optional[str] = None
    message: Optional[str] = None
    is_public: Optional[bool] = None


class MemorialResponse(BaseModel):
    id: int
    slug: str
    name: str
    birth_date: Optional[str]
    death_date: Optional[str]
    biography: Optional[str]
    message: Optional[str]
    is_public: bool
    qr_code_path: Optional[str]
    created_at: datetime
    media: List[MemorialMediaResponse] = []

    class Config:
        from_attributes = True


class MemorialPublic(BaseModel):
    slug: str
    name: str
    birth_date: Optional[str]
    death_date: Optional[str]
    biography: Optional[str]
    message: Optional[str]
    media: List[MemorialMediaResponse] = []

    class Config:
        from_attributes = True
