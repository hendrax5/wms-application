from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "ISP ERP System"
    DATABASE_URL: str = "sqlite:///./warehouse.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    APP_URL: str = "http://localhost:5173"

    # Network Integration (Phase 1: dry-run by default)
    DRY_RUN_MODE: bool = True

    # OLT ZTE SSH
    OLT_HOST: str = ""
    OLT_PORT: int = 22
    OLT_USERNAME: str = ""
    OLT_PASSWORD: str = ""

    # FreeRadius DB
    RADIUS_DB_URL: str = ""

    # Mikrotik RouterOS API
    MIKROTIK_HOST: str = ""
    MIKROTIK_USERNAME: str = ""
    MIKROTIK_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

