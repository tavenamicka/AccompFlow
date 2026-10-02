from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    admin_email: str
    admin_password: str
    admin_name: str = "Mickaël"

    upload_dir: str = "/data/client_documents"
    max_file_size: int = 50 * 1024 * 1024  # 50 Mo

    smtp_host: str = "localhost"
    smtp_port: int = 25
    sender_email: str = "contact@accomp-num.tranevat.fr"

    frontend_base_url: str = "http://localhost:8102"

    cors_origins: list[str] = [
        "http://localhost:8102",
        "http://localhost:3000",
    ]

    environment: str = "production"

    tz: str = "Europe/Paris"


settings = Settings()
