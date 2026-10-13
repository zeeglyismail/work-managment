import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("worklog")

DEFAULT_PASSWORD = "change-me"
DEFAULT_SECRET = "dev-secret-change-me"


class Settings:
    def __init__(self) -> None:
        self.username = os.getenv("APP_USERNAME", "admin")
        self.password = os.getenv("APP_PASSWORD", DEFAULT_PASSWORD)
        self.secret_key = os.getenv("SECRET_KEY", DEFAULT_SECRET)
        self.owner_name = os.getenv("OWNER_NAME", "")
        self.tz_name = os.getenv("TZ_NAME", "Asia/Dhaka")
        self.tz = ZoneInfo(self.tz_name)
        self.cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
        self.data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
        self.static_dir = Path(
            os.getenv("STATIC_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist")
        )

    @property
    def db_path(self) -> Path:
        return self.data_dir / "worklog.db"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    def warn_insecure_defaults(self) -> None:
        if self.password == DEFAULT_PASSWORD:
            log.warning("APP_PASSWORD is the default value - set it before exposing the app")
        if self.secret_key == DEFAULT_SECRET:
            log.warning("SECRET_KEY is the default value - set it before exposing the app")


settings = Settings()


def now_local() -> datetime:
    """Current wall-clock time in the configured timezone, stored naive.

    The app tracks one person's day, so all times are kept as naive local
    datetimes; that keeps "which day did this happen" trivial everywhere.
    """
    return datetime.now(settings.tz).replace(tzinfo=None, microsecond=0)
