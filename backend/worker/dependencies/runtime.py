from __future__ import annotations

import asyncio
import logging
from concurrent.futures import Future
from threading import Lock, Thread
from typing import Any

from worker.dependencies.build import WorkerDependencies

logger = logging.getLogger(__name__)


class AsyncRuntime:
    _instance: "AsyncRuntime | None" = None
    _lock = Lock()

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(
            target=self._run_loop,
            name="worker-async-runtime",
            daemon=True,
        )
        self._thread.start()

        self._deps = self.run(WorkerDependencies.create())

    @classmethod
    def get(cls) -> "AsyncRuntime":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro) -> Any:
        future: Future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    @property
    def deps(self) -> WorkerDependencies:
        return self._deps

    def close(self) -> None:
        try:
            self.run(self._deps.aclose())
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
