"""Application configuration (roadmap B-002).

What this file is for: every knob the running app has lives here, in
one typed place, read from the environment with the ``GPA_`` prefix.
Nothing else in the codebase reads ``os.environ`` directly — if a
setting matters, it is declared here, documented in ``.env.example``,
and validated at startup so a missing or unsafe value fails fast
with a plain-words message instead of a surprise at 2 a.m.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The development-only fallback secret. It exists so a fresh clone
# runs instantly in dev; production startup refuses it (see below).
DEV_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    """Typed settings for the whole application.

    Field names map to environment variables by the GPA_ prefix:
    ``database_url`` is read from ``GPA_DATABASE_URL``, and so on.
    """

    model_config = SettingsConfigDict(env_prefix="GPA_", env_file=".env", extra="ignore")

    # Which world are we in: dev, test, or prod. Prod is stricter.
    env: str = "dev"

    # Database location. SQLite file by default; the URL is the one
    # swap-point for PostgreSQL later (roadmap D-06).
    database_url: str = "sqlite:///./data/gpa.db"

    # Signing secret for access tokens + one-time token hashing.
    secret_key: str = DEV_SECRET

    # Token lifetimes (roadmap B-012/B-013).
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    magic_link_minutes: int = 30

    # Local file storage (B-007) and the dev mail outbox (B-012).
    storage_dir: Path = Path("./data/storage")
    outbox_dir: Path = Path("./data/outbox")

    # Auth rate limiting (B-021): attempts per minute per IP.
    auth_rate_per_minute: int = 30

    # File ingest (B-025): the largest single upload, in bytes.
    # Refused files are rejected before anything is stored.
    max_upload_bytes: int = 10_485_760

    # Background jobs (B-008): attempts before dead-letter, and the
    # base delay that exponential backoff grows from.
    job_max_attempts: int = 5
    job_backoff_base_seconds: int = 5

    # Link ingest (B-029): how long a page fetch may take, and the
    # largest page body the archive will keep. The SSRF guards
    # themselves live in services/linkfetch.py and are not knobs —
    # safety limits are not settings a deployment can loosen.
    link_fetch_timeout_seconds: int = 10
    link_fetch_max_bytes: int = 2_097_152

    # Dev/demo convenience: create tables at startup. Production
    # runs Alembic migrations and sets this to false.
    auto_create_tables: bool = True

    @field_validator("secret_key")
    @classmethod
    def _secret_must_be_real_in_prod(cls, value: str, info) -> str:
        """Fail startup, in plain words, if prod uses the dev secret.

        A config error should stop the world loudly at boot — never
        let a public deployment sign tokens with a published string.
        """
        env = (info.data or {}).get("env", "dev")
        if env == "prod" and value == DEV_SECRET:
            raise ValueError(
                "GPA_SECRET_KEY is not set to a real secret. "
                "Set GPA_SECRET_KEY to a long random value before "
                "running with GPA_ENV=prod."
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built (and validated) once."""
    return Settings()
