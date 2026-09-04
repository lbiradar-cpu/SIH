"""
core/config.py
Single Settings object. Everything else imports `settings` from here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SIH26034 Legal Metrology Compliance API"
    env: str = "development"

    upload_dir: str = "uploads"
    report_dir: str = "reports"
    max_upload_mb: int = 10

    database_url: str = "postgresql://postgres:postgres@localhost:5432/legal_metrology"

    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
