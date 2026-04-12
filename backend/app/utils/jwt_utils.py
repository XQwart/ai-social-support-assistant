import uuid

from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone


class JWTTokenUtil:
    _ttl: timedelta
    _secret: str
    _algorithm: str

    def __init__(self, ttl: timedelta, secret: str, algorithm: str = "HS256") -> None:
        self._ttl = ttl
        self._secret = secret
        self._algorithm = algorithm

    def generate(self, user_id: int, extra: dict | None = None) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": str(user_id),
            "exp": now + self._ttl,
            "iat": now,
            "nbf": now,
        }

        if extra:
            payload.update(extra)

        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def validate(self, token: str) -> dict | None:
        try:
            data = jwt.decode(
                token,
                self._secret,
                algorithms=self._algorithm,
            )
            return data
        except JWTError:
            return None

    @staticmethod
    def generate_jti() -> str:
        return str(uuid.uuid4())
