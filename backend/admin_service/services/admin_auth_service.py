from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from admin_service.core.security import (
    AdminSessionToken,
    consume_login_attempt,
    generate_totp_secret,
    hash_password,
    needs_rehash,
    reset_login_counter,
    totp_provisioning_uri,
    verify_password,
    verify_totp,
)

if TYPE_CHECKING:
    from redis.asyncio import Redis

    from shared.models import Admin

    from admin_service.core.config import AdminConfig
    from admin_service.repositories.admin_repository import AdminRepository
    from admin_service.services.admin_audit_service import AdminAuditService


logger = logging.getLogger(__name__)


class LoginFailure:
    INVALID_CREDENTIALS = "invalid_credentials"
    TOTP_REQUIRED = "totp_required"
    TOTP_INVALID = "totp_invalid"
    INACTIVE = "inactive"
    RATE_LIMITED = "rate_limited"


class LoginResult:
    admin: "Admin | None"
    token: str | None
    session_id: str | None
    failure: str | None
    retry_after_seconds: int | None

    def __init__(
        self,
        admin: "Admin | None" = None,
        token: str | None = None,
        session_id: str | None = None,
        failure: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.admin = admin
        self.token = token
        self.session_id = session_id
        self.failure = failure
        self.retry_after_seconds = retry_after_seconds

    @property
    def ok(self) -> bool:
        return self.admin is not None and self.token is not None


class AdminAuthService:
    _admin_repo: "AdminRepository"
    _audit: "AdminAuditService"
    _token: AdminSessionToken
    _config: "AdminConfig"
    _redis: "Redis"

    def __init__(
        self,
        admin_repo: "AdminRepository",
        audit: "AdminAuditService",
        token: AdminSessionToken,
        config: "AdminConfig",
        redis: "Redis",
    ) -> None:
        self._admin_repo = admin_repo
        self._audit = audit
        self._token = token
        self._config = config
        self._redis = redis

    # ------------------------------------------------------------------
    # Login / logout
    # ------------------------------------------------------------------
    async def login(
        self,
        username: str,
        password: str,
        totp_code: str | None,
        client_ip: str | None,
    ) -> LoginResult:
        ident_user = f"user:{username.lower()}"
        ident_ip = f"ip:{client_ip or 'unknown'}"

        user_count, user_over = await consume_login_attempt(
            self._redis,
            ident_user,
            self._config.admin_login_rate_limit_window_seconds,
            self._config.admin_login_rate_limit_attempts,
        )
        ip_count, ip_over = await consume_login_attempt(
            self._redis,
            ident_ip,
            self._config.admin_login_rate_limit_window_seconds,
            self._config.admin_login_rate_limit_attempts,
        )
        if user_over or ip_over:
            await self._audit.record(
                action="admin.login.rate_limited",
                payload_diff={
                    "username": username,
                    "user_count": user_count,
                    "ip_count": ip_count,
                },
            )
            return LoginResult(
                failure=LoginFailure.RATE_LIMITED,
                retry_after_seconds=self._config.admin_login_rate_limit_window_seconds,
            )

        admin = await self._admin_repo.get_by_username(username)
        if admin is None or not admin.is_active:
            await self._audit.record(
                action="admin.login.failed",
                payload_diff={"username": username, "reason": "unknown_or_inactive"},
            )
            return LoginResult(failure=LoginFailure.INVALID_CREDENTIALS)

        if admin.locked_until and admin.locked_until > datetime.now(tz=timezone.utc):
            await self._audit.record(
                action="admin.login.locked",
                admin_id=admin.id,
                payload_diff={"locked_until": admin.locked_until.isoformat()},
            )
            return LoginResult(failure=LoginFailure.RATE_LIMITED)

        if not verify_password(password, admin.password_hash):
            await self._record_failed_password(admin.id, username)
            return LoginResult(failure=LoginFailure.INVALID_CREDENTIALS)

        if admin.is_totp_enabled:
            if not totp_code:
                return LoginResult(failure=LoginFailure.TOTP_REQUIRED, admin=admin)
            if not admin.totp_secret or not verify_totp(admin.totp_secret, totp_code):
                await self._record_failed_password(admin.id, username)
                return LoginResult(failure=LoginFailure.TOTP_INVALID, admin=admin)

        if needs_rehash(admin.password_hash):
            await self._admin_repo.update_password(
                admin.id,
                hash_password(password),
                must_change_password=admin.must_change_password,
            )

        await self._admin_repo.reset_failed_logins(admin.id)
        await self._admin_repo.update_last_login(admin.id)
        await reset_login_counter(self._redis, ident_user)
        await reset_login_counter(self._redis, ident_ip)

        session_id = AdminSessionToken.generate_session_id()
        token_value = self._token.encode(admin.id, session_id)

        await self._audit.record(
            action="admin.login.success",
            admin_id=admin.id,
            target_type="admin",
            target_id=str(admin.id),
        )

        return LoginResult(
            admin=admin,
            token=token_value,
            session_id=session_id,
        )

    async def _record_failed_password(self, admin_id: int, username: str) -> None:
        count = await self._admin_repo.increment_failed_logins(admin_id)
        if count >= self._config.admin_login_rate_limit_attempts:
            lockout_until = datetime.now(tz=timezone.utc) + self._config.lockout_duration
            await self._admin_repo.set_locked_until(admin_id, lockout_until)
            await self._audit.record(
                action="admin.login.auto_locked",
                admin_id=admin_id,
                payload_diff={
                    "username": username,
                    "locked_until": lockout_until.isoformat(),
                },
            )
        else:
            await self._audit.record(
                action="admin.login.failed",
                admin_id=admin_id,
                payload_diff={"username": username, "failed_count": count},
            )

    async def logout(self, admin_id: int | None) -> None:
        if admin_id is not None:
            await self._audit.record(
                action="admin.logout",
                admin_id=admin_id,
                target_type="admin",
                target_id=str(admin_id),
            )

    # ------------------------------------------------------------------
    # Password changes
    # ------------------------------------------------------------------
    async def change_password(
        self,
        admin_id: int,
        current_password: str,
        new_password: str,
    ) -> bool:
        admin = await self._admin_repo.get_by_id(admin_id)
        if admin is None:
            return False
        if not verify_password(current_password, admin.password_hash):
            await self._audit.record(
                action="admin.password.change_failed",
                admin_id=admin.id,
                target_type="admin",
                target_id=str(admin.id),
            )
            return False
        await self._admin_repo.update_password(
            admin.id,
            hash_password(new_password),
            must_change_password=False,
        )
        await self._audit.record(
            action="admin.password.changed",
            admin_id=admin.id,
            target_type="admin",
            target_id=str(admin.id),
        )
        return True

    # ------------------------------------------------------------------
    # TOTP enrollment / disable
    # ------------------------------------------------------------------
    async def begin_totp_enrollment(
        self,
        admin_id: int,
    ) -> tuple[str, str] | None:
        admin = await self._admin_repo.get_by_id(admin_id)
        if admin is None:
            return None
        secret = generate_totp_secret()
        # Store but keep disabled until the admin confirms with a valid code.
        await self._admin_repo.set_totp_secret(
            admin.id,
            secret,
            enabled=False,
        )
        uri = totp_provisioning_uri(
            secret,
            admin.username,
            self._config.admin_totp_issuer,
        )
        await self._audit.record(
            action="admin.totp.enrollment_started",
            admin_id=admin.id,
            target_type="admin",
            target_id=str(admin.id),
        )
        return secret, uri

    async def confirm_totp_enrollment(
        self,
        admin_id: int,
        code: str,
    ) -> bool:
        admin = await self._admin_repo.get_by_id(admin_id)
        if admin is None or not admin.totp_secret:
            return False
        if not verify_totp(admin.totp_secret, code):
            return False
        await self._admin_repo.set_totp_secret(
            admin.id,
            admin.totp_secret,
            enabled=True,
        )
        await self._audit.record(
            action="admin.totp.enabled",
            admin_id=admin.id,
            target_type="admin",
            target_id=str(admin.id),
        )
        return True

    async def reset_totp(self, target_admin_id: int, acting_admin_id: int) -> None:
        await self._admin_repo.set_totp_secret(target_admin_id, None, enabled=False)
        await self._audit.record(
            action="admin.totp.reset",
            admin_id=acting_admin_id,
            target_type="admin",
            target_id=str(target_admin_id),
        )

    # ------------------------------------------------------------------
    # Admin CRUD helpers (used by admins_routes)
    # ------------------------------------------------------------------
    async def create_admin(
        self,
        acting_admin_id: int,
        username: str,
        password: str,
    ) -> "Admin":
        admin = await self._admin_repo.create(
            username=username,
            password_hash=hash_password(password),
            must_change_password=True,
        )
        await self._audit.record(
            action="admin.user.created",
            admin_id=acting_admin_id,
            target_type="admin",
            target_id=str(admin.id),
            payload_diff={"username": admin.username},
        )
        return admin

    async def set_admin_active(
        self,
        acting_admin_id: int,
        target_admin_id: int,
        is_active: bool,
    ) -> None:
        await self._admin_repo.set_active(target_admin_id, is_active)
        await self._audit.record(
            action="admin.user.activated" if is_active else "admin.user.disabled",
            admin_id=acting_admin_id,
            target_type="admin",
            target_id=str(target_admin_id),
        )
