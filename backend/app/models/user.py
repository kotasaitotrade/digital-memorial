from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # セキュリティ
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    totp_secret = Column(String, nullable=True)          # 2FA TOTP シークレット
    totp_enabled = Column(Boolean, default=False)

    # ユーザー設定
    font_size = Column(String, default="medium")         # small / medium / large / xlarge
    simple_mode = Column(Boolean, default=False)         # かんたんモード

    memorials = relationship("Memorial", back_populates="owner")
