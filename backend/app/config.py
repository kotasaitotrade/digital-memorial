from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./memorial.db"
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
