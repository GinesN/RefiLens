from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = "sqlite:///./data/refilens.db"
    sec_user_agent: str = ""
    sec_cache_dir: Path = ROOT / "data/sec-cache"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def db_url(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            path = ROOT / self.database_url.removeprefix("sqlite:///./")
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path}"
        return self.database_url

    @property
    def cache_dir(self) -> Path:
        return self.sec_cache_dir if self.sec_cache_dir.is_absolute() else ROOT / self.sec_cache_dir


settings = Settings()
