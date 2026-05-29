from __future__ import annotations
import base64
import io
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pyotp
import qrcode
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from itsdangerous import BadSignature, URLSafeSerializer
from jose import JWTError, jwt

if TYPE_CHECKING:
    from redis.asyncio import Redis


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password hashing (Argon2id)
# ---------------------------------------------------------------------------
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    try:
        return _password_hasher.verify(hash_value, password)
    except (VerifyMismatchError, InvalidHash):
        return False
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error verifying password")
        return False


def needs_rehash(hash_value: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(hash_value)
    except InvalidHash:
        return True


# ---------------------------------------------------------------------------
# JWT (admin session cookie)
# ---------------------------------------------------------------------------
class AdminSessionToken:
    """Wraps admin-session JWT encoding/decoding.

    Uses a separate secret from user JWTs so a compromise of one cannot
    be used to forge the other.
    """

    _secret: str
    _ttl: timedelta
    _algorithm: str

    def __init__(
        self,
        secret: str,
        ttl: timedelta,
        algorithm: str = "HS256",
    ) -> None:
        self._secret = secret
        self._ttl = ttl
        self._algorithm = algorithm

    def encode(self, admin_id: int, session_id: str) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": str(admin_id),
            "sid": session_id,
            "iat": now,
            "nbf": now,
            "exp": now + self._ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError:
            return None

    @staticmethod
    def generate_session_id() -> str:
        return secrets.token_urlsafe(24)


# ---------------------------------------------------------------------------
# TOTP (2FA)
# ---------------------------------------------------------------------------
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, username: str, issuer: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def render_totp_qr_data_uri(provisioning_uri: str) -> str:
    """Render the TOTP URI as a base64 PNG data URI suitable for <img src>."""
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error verifying TOTP")
        return False


# ---------------------------------------------------------------------------
# CSRF double-submit token
# ---------------------------------------------------------------------------
class CSRFTokenSigner:
    """HMAC-signed double-submit CSRF token.

    The cookie value and the submitted header/form value must match; the
    signature prevents forging new tokens without the CSRF secret.
    """

    _serializer: URLSafeSerializer

    def __init__(self, secret: str) -> None:
        self._serializer = URLSafeSerializer(secret, salt="admin-csrf")

    def issue(self) -> str:
        nonce = secrets.token_urlsafe(16)
        return self._serializer.dumps(nonce)

    def validate(self, token: str) -> bool:
        try:
            self._serializer.loads(token)
            return True
        except BadSignature:
            return False
        except Exception:  # noqa: BLE001
            return False


# ---------------------------------------------------------------------------
# Redis-backed login rate limit
# ---------------------------------------------------------------------------
async def consume_login_attempt(
    redis: "Redis",
    identifier: str,
    window_seconds: int,
    max_attempts: int,
) -> tuple[int, bool]:
    """Register one login attempt for ``identifier`` (username or IP).

    Returns ``(current_count, is_over_limit)``. Uses a fixed-window
    counter; the key TTL is set on first increment.
    """
    key = f"admin:login:{identifier}"
    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        count, _ = await pipe.execute()
    except Exception:  # noqa: BLE001
        logger.exception(
            "Failed to update login rate-limit counter for identifier=%s",
            identifier,
        )
        return 0, False

    count = int(count or 0)
    return count, count > max_attempts


async def reset_login_counter(redis: "Redis", identifier: str) -> None:
    key = f"admin:login:{identifier}"
    try:
        await redis.delete(key)
    except Exception:  # noqa: BLE001
        logger.exception(
            "Failed to reset login rate-limit counter for identifier=%s",
            identifier,
        )
