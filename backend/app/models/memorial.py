from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base


def generate_slug():
    return str(uuid.uuid4())[:8]


class Memorial(Base):
    __tablename__ = "memorials"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, default=generate_slug)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 故人の情報
    name = Column(String, nullable=False)
    birth_date = Column(String)
    death_date = Column(String)
    biography = Column(Text)
    message = Column(Text)

    # アクセス制御
    is_public = Column(Boolean, default=True)
    password_hash = Column(String, nullable=True)

    # QRコード
    qr_code_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="memorials")
    media = relationship("MemorialMedia", back_populates="memorial", cascade="all, delete-orphan")


class MemorialMedia(Base):
    __tablename__ = "memorial_media"

    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False)
    file_path = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # "image" or "video"
    caption = Column(String, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 写真アルバム・詳細フィールド（小林雪 要望）
    album_name = Column(String, nullable=True, default="メイン")  # アルバム名
    taken_at = Column(String, nullable=True)                      # 撮影日（YYYY-MM-DD）
    location = Column(String, nullable=True)                      # 撮影場所
    episode = Column(Text, nullable=True)                         # エピソード・思い出
    media_is_public = Column(Boolean, default=True)               # 写真単位の公開/非公開

    memorial = relationship("Memorial", back_populates="media")


class MemorialView(Base):
    __tablename__ = "memorial_views"

    id = Column(Integer, primary_key=True, index=True)
    memorial_id = Column(Integer, ForeignKey("memorials.id"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
