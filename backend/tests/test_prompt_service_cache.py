"""Unit tests for :class:`app.services.prompt_service.PromptService`.

Covers:
- the cache returns DB values when warmed
- ``get`` falls back to module-level defaults when a key is missing
- ``_refresh_one`` updates the cached version+body for a single key
- ``_refresh_one`` removes a key from the cache when the row is gone
- ``_reconcile_all`` re-fetches only the keys whose DB version drifted
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ---------------------------------------------------------------------------
# Stubs that imitate the small slice of the real APIs that PromptService uses.
# ---------------------------------------------------------------------------


@dataclass
class _PromptRow:
    key: str
    body: str
    version: int


class _StubRepo:
    """Fake PromptRepository whose ``rows`` are a single source of truth."""

    def __init__(self, rows: dict[str, _PromptRow]) -> None:
        self.rows = rows
        self.get_one_calls: list[str] = []
        self.get_versions_calls = 0
        self.get_all_calls = 0

    async def get_all(self) -> Iterable[_PromptRow]:
        self.get_all_calls += 1
        return list(self.rows.values())

    async def get_one(self, key: str) -> _PromptRow | None:
        self.get_one_calls.append(key)
        return self.rows.get(key)

    async def get_versions(self) -> dict[str, int]:
        self.get_versions_calls += 1
        return {row.key: row.version for row in self.rows.values()}


class _StubSession:
    async def __aenter__(self) -> "_StubSession":
        return self

    async def __aexit__(self, *exc) -> None:
        return None


class _StubSessionMaker:
    def __call__(self) -> _StubSession:
        return _StubSession()


@pytest.fixture
def stub_repo() -> _StubRepo:
    return _StubRepo(
        rows={
            "SYSTEM_PROMPT_ROLE": _PromptRow(
                key="SYSTEM_PROMPT_ROLE", body="role-from-db", version=2
            ),
            "SYSTEM_PROMPT_RULES": _PromptRow(
                key="SYSTEM_PROMPT_RULES", body="rules-from-db", version=1
            ),
        }
    )


@pytest.fixture
def patched_service(monkeypatch, stub_repo):
    """Build a PromptService whose PromptRepository is the stub above."""

    from app.services import prompt_service as ps_module

    monkeypatch.setattr(
        ps_module, "PromptRepository", lambda session: stub_repo
    )

    service = ps_module.PromptService(session_maker=_StubSessionMaker(), redis=None)  # type: ignore[arg-type]
    return service, stub_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warm_cache_pulls_all_rows(patched_service):
    service, repo = patched_service
    await service._warm_cache()
    assert repo.get_all_calls == 1
    assert service.get("SYSTEM_PROMPT_ROLE") == "role-from-db"
    assert service.get("SYSTEM_PROMPT_RULES") == "rules-from-db"


@pytest.mark.asyncio
async def test_get_falls_back_to_default_when_missing(patched_service):
    """When a key is not in cache and not in DB, the module default wins."""

    service, _ = patched_service

    from app.agent import prompts as prompts_module

    assert prompts_module.DEFAULT_PROMPTS, "DEFAULT_PROMPTS should be seeded"
    sample_key = next(iter(prompts_module.DEFAULT_PROMPTS))
    expected_default = prompts_module.DEFAULT_PROMPTS[sample_key]

    # Cache is empty
    assert service._cache == {}
    assert service.get(sample_key) == expected_default


def test_get_returns_empty_string_for_unknown_key(patched_service):
    service, _ = patched_service
    assert service.get("does-not-exist-anywhere") == ""


@pytest.mark.asyncio
async def test_refresh_one_updates_cache(patched_service):
    service, repo = patched_service
    await service._warm_cache()

    repo.rows["SYSTEM_PROMPT_ROLE"] = _PromptRow(
        key="SYSTEM_PROMPT_ROLE", body="role-edited", version=3
    )

    await service._refresh_one("SYSTEM_PROMPT_ROLE")

    assert service.get("SYSTEM_PROMPT_ROLE") == "role-edited"
    assert service._cache["SYSTEM_PROMPT_ROLE"] == (3, "role-edited")
    assert "SYSTEM_PROMPT_ROLE" in repo.get_one_calls


@pytest.mark.asyncio
async def test_refresh_one_evicts_when_row_disappears(patched_service):
    service, repo = patched_service
    await service._warm_cache()
    assert "SYSTEM_PROMPT_ROLE" in service._cache

    repo.rows.pop("SYSTEM_PROMPT_ROLE")
    await service._refresh_one("SYSTEM_PROMPT_ROLE")

    assert "SYSTEM_PROMPT_ROLE" not in service._cache


@pytest.mark.asyncio
async def test_reconcile_all_only_refreshes_drifted_keys(patched_service):
    service, repo = patched_service
    await service._warm_cache()
    repo.get_one_calls.clear()

    # Bump only one key in the DB
    repo.rows["SYSTEM_PROMPT_ROLE"] = _PromptRow(
        key="SYSTEM_PROMPT_ROLE", body="role-bumped", version=99
    )

    await service._reconcile_all()

    assert repo.get_one_calls == ["SYSTEM_PROMPT_ROLE"]
    assert service.get("SYSTEM_PROMPT_ROLE") == "role-bumped"
    assert service._cache["SYSTEM_PROMPT_ROLE"][0] == 99
    # The non-drifted key must keep its original cached version.
    assert service.get("SYSTEM_PROMPT_RULES") == "rules-from-db"
