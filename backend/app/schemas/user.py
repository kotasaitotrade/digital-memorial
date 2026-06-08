from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    totp_enabled: bool = False
    font_size: str = "medium"
    simple_mode: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AccountDelete(BaseModel):
    password: str


class UserPreferences(BaseModel):
    font_size: Optional[str] = None    # small / medium / large / xlarge
    simple_mode: Optional[bool] = None


class TOTPSetup(BaseModel):
    totp_secret: str
    qr_data_url: str


class TOTPVerify(BaseModel):
    code: str


class TOTPDisable(BaseModel):
    password: str
    code: str
