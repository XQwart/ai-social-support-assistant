from redis import Redis


class RuntimeStateService:
    INIT_SOURCES_STATUS_KEY = "system:init_sources_status"

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    def set_sources_status(self, status: str) -> None:
        self._redis.set(self.INIT_SOURCES_STATUS_KEY, status)

    def get_sources_status(self) -> str:
        value = self._redis.get(self.INIT_SOURCES_STATUS_KEY)
        if value is None:
            return "pending"
        if not isinstance(value, str):
            raise TypeError("Expected str from redis")
        return value

    def is_sources_ready(self) -> bool:
        return self.get_sources_status() == "ready"
