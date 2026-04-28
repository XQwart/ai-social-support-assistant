from __future__ import annotations
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import Config as BackendConfig, get_config as get_backend_config


ADMIN_BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ADMIN_BASE_DIR / "templates"
STATIC_DIR = ADMIN_BASE_DIR / "static"


class AdminConfig(BaseSettings):
    """Admin-panel-specific settings.

    Loaded from the same ``.env`` file as the backend. Only fields that
    are admin-only live here — shared values (Postgres, Redis, Qdrant,
    embeddings) come from :class:`app.core.config.Config` so there is a
    single source of truth.
    """

    model_config = SettingsConfigDict(
        env_file=ADMIN_BASE_DIR.parents[0] / ".env",
        extra="ignore",
    )

    admin_jwt_secret: str
    admin_session_ttl_minutes: int = 120

    admin_csrf_secret: str

    initial_admin_username: str | None = None
    initial_admin_password: str | None = None

    admin_login_rate_limit_attempts: int = 5
    admin_login_rate_limit_window_seconds: int = 900
    admin_lockout_seconds: int = 900

    admin_force_https: bool = True

    admin_totp_issuer: str = "SOC Admin"

    # Public mount path of the admin service behind nginx. The service
    # itself listens on root paths (``/login``, ``/prompts``, ...), but
    # generated absolute URLs (redirect Location headers, cookies, links
    # in templates) need to include this prefix so the browser stays on
    # the admin app instead of falling back to the public frontend.
    #
    # Set to an empty string when running the admin app directly (e.g.
    # for tests on port 8001).
    admin_base_path: str = "/admin"

    @property
    def normalized_base_path(self) -> str:
        """``/admin`` -> ``/admin``; ``admin/`` -> ``/admin``; ``""`` -> ``""``."""
        raw = (self.admin_base_path or "").strip()
        if not raw:
            return ""
        if not raw.startswith("/"):
            raw = "/" + raw
        if raw.endswith("/") and len(raw) > 1:
            raw = raw.rstrip("/")
        return raw

    @property
    def cookie_path(self) -> str:
        """Cookie ``Path`` attribute — never empty (browsers default to /)."""
        return self.normalized_base_path or "/"

    def url_for(self, path: str) -> str:
        """Prepend the admin base path to an internal absolute path."""
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.normalized_base_path}{path}"

    @property
    def session_ttl(self) -> timedelta:
        return timedelta(minutes=self.admin_session_ttl_minutes)

    @property
    def login_rate_limit_window(self) -> timedelta:
        return timedelta(seconds=self.admin_login_rate_limit_window_seconds)

    @property
    def lockout_duration(self) -> timedelta:
        return timedelta(seconds=self.admin_lockout_seconds)


@lru_cache
def get_admin_config() -> AdminConfig:
    return AdminConfig()


def get_shared_backend_config() -> BackendConfig:
    return get_backend_config()
