from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./memorial.db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    base_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # SMTP設定（未設定時はコンソールログのみ・開発モード）
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@digital-memorial.example.com"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
